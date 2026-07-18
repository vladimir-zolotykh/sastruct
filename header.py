#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from __future__ import annotations
from typing import BinaryIO, Self, TYPE_CHECKING, Iterator
from functools import singledispatch, singledispatchmethod
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
    _view_size: int

    def __new__(mcls, clsname, bases, ns):
        ns2 = dict(ns)
        off: int = 0
        fields: list[str] = []
        for name, val in ns.items():
            if (name[:2] == "__" and name[-2:] == "__") or ns.get("_exclude", False):
                continue
            ns2[name], delta = make_field(val, name, off)
            off += delta
            fields.append(name)
        ns2["_view_size"] = off
        ns2["_fields"] = fields
        return super().__new__(mcls, clsname, bases, ns2)


@singledispatch
def make_field(val, name, off):
    raise TypeError(f"Cannot make_field for {val!r}")


@make_field.register
def _(val: str, name: str, off: int) -> tuple[FieldFmt, int]:
    fld = FieldFmt(name, off, val)
    off = struct.calcsize(val)
    return (fld, off)


@make_field.register
def _(val: StructMeta, name: str, off: int) -> tuple[FieldType, int]:
    fld = FieldType(name, off, val)
    off = val._view_size
    return (fld, off)


class View(metaclass=StructMeta):
    _exclude = True  # do not inject fields for this class
    _view_size: int
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
    if TYPE_CHECKING:
        cnt: int
    else:
        cnt = "<i"


class Polygon(View):
    _exclude = True

    @classmethod
    def from_file(cls, f: BinaryIO) -> Self:
        _INT = struct.Struct("<i")
        (sz,) = struct.unpack(_INT.format, f.read(_INT.size))
        return cls(f.read(sz - _INT.size))

    @singledispatchmethod
    def iter_as(self, kind):
        raise NotImplementedError(f"Cannot iterate as {kind}")

    @iter_as.register
    def _(self, fmt: str) -> Iterator[tuple[float, float]]:
        for off in range(0, len(self.view), struct.calcsize(fmt)):
            sl = slice(off, off + struct.calcsize(fmt))
            yield struct.unpack_from(fmt, self.view[sl])

    @iter_as.register
    def _(self, factory: StructMeta) -> Iterator[StructMeta]:
        for off in range(0, len(self.view), factory._view_size):
            sl = slice(off, off + factory._view_size)
            yield factory(self.view[sl])


parser = argparse.ArgumentParser(
    description="Iterate polygons as",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("--iter-as", choices=["dd", "Point"], help="Choose iter-as kind")
if __name__ == "__main__":
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    with open("polygons.dat", "rb") as f:
        h = Header(f.read(Header._view_size))
        print(h)
        for _ in range(h.cnt):
            polygon = Polygon.from_file(f)
            kind = (
                globals()[args.iter_as] if args.iter_as in globals() else args.iter_as
            )
            for x in polygon.iter_as(kind):
                print(x)
