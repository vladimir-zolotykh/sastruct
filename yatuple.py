#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


from operator import itemgetter


class TupleMeta(type):
    def __init__(cls, clsname, bases, ns):
        for n, name in enumerate(cls.__schema__):
            setattr(cls, name, property(itemgetter(n)))


class Tuple(tuple, metaclass=TupleMeta):
    def __new__(cls, *args, **kwargs):
        if len(args) != (n := len(cls.__schema__)):
            raise TypeError(f"{cls} gets exactly {n} arguments")
        return super().__new__(args)


class Person(Tuple):
    __schema__ = ["name", "age", "salary"]


if __name__ == "__main__":
    p = Person("Bob", 37, 12000)
    print(p)
