#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import types


class lazycall:
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return types.MethodType(self, instance)

    def __call__(self, instance, n):
        if n in instance.cache:
            return instance.cache[n]
        else:
            val = self.func(n)
            instance.cache[n] = val
            return val


def fib(n):
    print("Getting fib({n}")
    return (fib(n - 2) + fib(n - 1)) if n >= 2 else n


class Fib:
    @lazycall
    def fib(self, n):
        return fib(n)


if __name__ == "__main__":
    f = Fib()
    for n in range(8):
        print(f.fib(n))
