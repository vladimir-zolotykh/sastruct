#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


from operator import itemgetter


class TupleMeta(type):
    def __init__(cls, clsname, bases, ns):
        schema = ns.get("__schema__", [])
        for n, name in enumerate(schema):
            setattr(cls, name, property(itemgetter(n)))


class Tuple(tuple, metaclass=TupleMeta):
    def __new__(cls, *args, **kwargs):
        if len(args) != (n := len(cls.__schema__)):
            raise TypeError(f"<class {cls.__name__!r}> gets exactly {n} arguments")
        return super().__new__(cls, args)


class Person(Tuple):
    __schema__ = ["name", "age", "salary"]


class PersonCsv(Person):
    @classmethod
    def from_person(cls, person_obj):
        return PersonCsv(*person_obj)

    def __repr__(self):
        return f"PersonCsv({as_csv(self)})"


def as_csv(tup: Tuple) -> str:
    schema = getattr(tup, "__schema__", [])
    return ", ".join(f"{a}={getattr(tup, a)!r}" for a in schema)


if __name__ == "__main__":
    p = Person("Bob", 37, 12000)
    print(p)
    p2 = PersonCsv.from_person(p)
    print(p2)
