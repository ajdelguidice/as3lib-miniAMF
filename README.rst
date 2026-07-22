as3lib-miniAMF
==============

This is a fork of `Mini-AMF <https://pypi.org/project/Mini-AMF/>`__ which brings back the cut functionality and works properly on newer python versions. Python 3.9 is the current minimum version but this fork should work all the way back to python 3.4.

This package uses the same directories as miniamf. Installing them together will break both of them.

Elixir support will not be brought back due to being the project being abandoned.


TODO
~~~~

| Add a way to not install the Cython modules
| Fix the remaining test failures (Cython fail:8 skip:5, noCython fail:2 skip:9).
| Rename to as3lib-AMF
| Change package directory to as3lib.AMF
| Fix build script on python 3.4 - 3.8.
| Fix unclosed SQL database warnings when cython modules are used
| Add tests for AS3 vectors and dictionaries.
| Update docs
| Don't use epydoc for docs
