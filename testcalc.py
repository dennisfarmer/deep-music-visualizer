#!/usr/bin/env python


def f(x, **kwargs):
    g({k: kwargs.pop(k) for k in kwargs})

def g(**kwargs):
    for k in kwargs:
        print(k, kwargs[k])

f(x=1, y=2)



