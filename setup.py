#!/usr/bin/env python

# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

import os.path
from setuptools import Feature, setup
import sys

try:
    from Cython.Build import cythonize
    have_cython = True
except:
    have_cython = False

class AccelFeature(Feature):
    def __init__(self, have_cython):
        self.have_cython = have_cython
        self.extensions = []

        Feature.__init__(
            self,
            description="optional C accelerator modules (broken)",
            standard=False,
            available=have_cython,
            ext_modules=self.extensions
        )

    def include_in(self, dist):
        if not self.have_cython:
            sys.stderr.write(
                "ERROR: Cython is required to compile accelerator modules.\n")
            sys.exit(1)

        sys.stderr.write(
            "WARNING: Accelerator modules are broken.\n"
            "WARNING: You should only use --with-accel "
            "if you are trying to fix them.\n")

        self.extensions.extend(cythonize("miniamf/_accel/*.pyx"))
        Feature.include_in(self, dist)


def get_version():
    """
    Retrieve the version number from miniamf/_version.py.  It is
    necessary to do this by hand, because the package may not yet be
    importable (critical dependencies, like "six", may be missing).

    This duplicates the tuple-to-string logic in miniamf/versions.py,
    but without any dependence on "six".
    """
    from ast import literal_eval
    import re

    with open(os.path.join(os.path.dirname(__file__),
                           "miniamf/_version.py"), "rt") as f:
        vdat = f.read()
    m = re.search(
        r"(?ms)^\s*version\s*=\s*Version\(\*(\([^)]+\))\)",
        vdat)
    if not m:
        raise RuntimeError("failed to extract version tuple")

    vtuple = literal_eval(m.group(1))
    if not vtuple:
        raise RuntimeError("version tuple appears to be empty")

    v = []
    first = True
    for x in vtuple:
        if not first and isinstance(x, int):
            v.append(u'.')
        if isinstance(x, str):
            v.append(x)
        elif isinstance(x, bytes):
            v.append(x.decode("utf-8"))
        else:
            v.append(str(x))
        first = False

    return u''.join(v)

def setup_package():
    setup(
        features={"accel": AccelFeature(have_cython)},
        test_suite="tests",
        zip_safe=True,
    )


if __name__ == "__main__":
    setup_package()
