# -*- encoding: utf-8 -*-

import re


def re_compile_ui(regexp):
    return re.compile(regexp, re.I | re.U)


def some(items):
    for item in items:
        if item: return item
