#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import types


class lazycall:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if not hasattr(instance, "cache"):
            setattr(instance, "cache", {})
        return types.MethodType(self, instance)

    def __call__(self, instance, n):
        if n in instance.cache:
            return instance.cache[n]
        else:
            val = self.func(instance, n)
            instance.cache[n] = val
            return val


class Fib:
    @lazycall
    def fib(self, n):
        return (self.fib(n - 1) + self.fib(n - 2)) if n >= 2 else n


if __name__ == "__main__":
    f = Fib()
    print(f.fib(80))
