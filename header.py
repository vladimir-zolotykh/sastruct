#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import ClassVar, BinaryIO, Self
from functools import singledispatchmethod
import argparse
import argcomplete
import struct


class Field:
    def __init__(self, name, offset):
        self._name = name
        self.offset = offset

    def fetch(self, instance):
        raise NotImplementedError

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self.fetch(instance)


class FieldFmt(Field):
    def __init__(self, name, offset, fmt):
        super().__init__(name, offset)
        self.fmt = fmt

    def fetch(self, instance):
        sl = slice(self.offset, self.offset + struct.calcsize(self.fmt))
        tup = struct.unpack_from(self.fmt, instance.view[sl])
        return tup[0] if len(tup) == 1 else tup


class FieldType(Field):
    def __init__(self, name, offset, factory):
        super().__init__(name, offset)
        self.factory = factory

    def fetch(self, instance):
        sl = slice(self.offset, self.offset + self.factory._view_size)
        return self.factory(instance.view[sl])


class StructMeta(type):
    def __new__(mcls, clsname, bases, ns):
        ns2 = dict(ns)
        off: int = 0
        fields: list[str] = []
        for name, val in ns.items():
            if (name[:2] == "__" and name[-2:] == "__") or ns.get("_exclude", False):
                continue
            if isinstance(val, str):
                ns2[name] = FieldFmt(name, off, val)
                off += struct.calcsize(val)
            elif isinstance(val, type):
                ns2[name] = FieldType(name, off, val)
                off += val._view_size
            fields.append(name)
        ns2["_view_size"] = off
        ns2["_fields"] = fields
        return super().__new__(mcls, clsname, bases, ns2)


class View(metaclass=StructMeta):
    _exclude = True  # do not inject fields for this class
    _view_size: ClassVar[int]
    _fields: list[str]

    def __init__(self, bytesdata: bytes | memoryview):
        self.view = memoryview(bytesdata)

    def as_csv(self):
        return ", ".join(f"{f}={getattr(self, f)!r}" for f in self._fields)

    def __repr__(self):
        return f"{type(self).__name__}({self.as_csv()})"


class Point(View):
    x = "<d"
    y = "<d"


class Bbox(View):
    p1 = Point
    p2 = Point


class Header(View):
    magic = "<i"
    bb = Bbox
    cnt = "<i"


class Polygon(View):
    @classmethod
    def from_file(cls, f: BinaryIO) -> Self:
        _INT = struct.Struct("<i")
        (sz,) = struct.unpack(_INT.format, f.read(_INT.size))
        return cls(f.read(sz - _INT.size))

    @singledispatchmethod
    def iter_as(self, kind):
        raise NotImplementedError(f"Cannot iterate as {kind}")

    @iter_as.register
    def _(self, fmt: str) -> tuple[float, float]:
        for off in range(0, len(self.view), struct.calcsize(fmt)):
            sl = slice(off, off + struct.calcsize(fmt))
            yield struct.unpack_from(fmt, self.view[sl])

    @iter_as.register
    def _(self, factory: StructMeta) -> StructMeta:
        for off in range(0, len(self.view), factory._view_size):
            sl = slice(off, off + factory._view_size)
            yield factory(self.view[sl])


parser = argparse.ArgumentParser(
    description="Iterate polygons as",
    #    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("--iter-as", choices=["<dd", "Point"], help="Choose iter-as kind")
if __name__ == "__main__":
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    with open("polygons.dat", "rb") as f:
        h = Header(f.read(Header._view_size))
        print(h)
        for _ in range(h.cnt):
            polygon = Polygon.from_file(f)
            if args.iter_as == "<dd":
                for x in polygon.iter_as(args.iter_as):
                    print(x)
            else:
                for x in polygon.iter_as(globals()[args.iter_as]):
                    print(x)
