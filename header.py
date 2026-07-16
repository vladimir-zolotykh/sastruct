#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import ClassVar
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
            if name[:2] == "__" and name[-2:] == "__":
                continue
            if isinstance(val, str):
                f = FieldFmt(name, off, val)
                off += struct.calcsize(val)
                fields.append(name)
                ns2[name] = f
            elif isinstance(val, type):
                f = FieldType(name, off, val)
                off += val._view_size
                fields.append(name)
                ns2[name] = f
        ns2["_view_size"] = off
        ns2["_fields"] = fields
        return super().__new__(mcls, clsname, bases, ns2)


class View(metaclass=StructMeta):
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


class Sized(View):
    pass


if __name__ == "__main__":
    with open("polygons.dat", "rb") as f:
        h = Header(f.read(Header._view_size))
        print(h)
