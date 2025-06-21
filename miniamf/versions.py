# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Because there is disparity between Python packaging (and it is being sorted
out ...) we currently provide our own way to get the string of a version tuple.

@since: 0.6
"""


class Version(tuple):

    _version = None

    def __new__(cls, *args):
        x = tuple.__new__(cls, args)

        return x

    def __str__(self):
        if not self._version:
            self._version = get_version(self)

        return self._version


def get_version(elements):
    v = []
    first = True

    for x in elements:
        if not first and isinstance(x, int):
            v.append(".")
        if isinstance(x, str):
            v.append(x)
        elif isinstance(x, bytes):
            v.append(x.decode('utf-8'))
        else:
            v.append(str(x))
        first = False

    return "".join(v)
