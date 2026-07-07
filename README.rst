as3lib-miniAMF
==============

This is a fork of `Mini-AMF <https://pypi.org/project/Mini-AMF/>`__ which brings back the cut functionality and works properly on newer python versions. Python 3.9 is the current minimum version but this fork should work all the way back to python 3.4.

This package uses the same directories as miniamf. Installing them together will break both of them.

Changes
~~~~~~~

- Removed Python 2 support
- Fixed _accel modules
- Replaced pkg_resources (setuptools) with importlib.resources
- Removed the deprecated cElementTree from xml related stuff
- Properly manage files in sol.save and sol.load
- Updated util.imports.ModuleFinder to use find_spec, create_module, and exec_module instead of the deprecated find_module and load_module
- Added partial support for AS3 Dictionaries and Vectors. The implementation used is adapted from `this commit <https://github.com/fmoo/pyamf/commit/67d2bf2a0da9b940d96cff6cc98156349cad276f>`__.
- Refactored util.pure.BufferedByteStream to remove util.pure.Excursion. It is now a child of io.BytesIO.
- Added utcnow and utcfromtimestamp to the util module in preperation for their removal from datetime.
- Brought back the flex and remoting support that was cut in miniamf. Everything except Elixir is present. NOTE: `this commit <https://github.com/StdCarrot/Py3AMF/commit/5a9963f2ee5622b638dcccb374fdc3c70fdc567d>`__ was used as a reference to fix the twisted tests.
- Removed miniamf.util.get_module. Using importlib instead removes the need for except handling and is faster in every case where it was used.

Elixir support will not be brought back due to being the project being abandoned.

TODO
~~~~

| Fix library when cython modules are not installed.
| Rename to as3lib-AMF
| Change package directory to as3lib.AMF
| Fix build script on python 3.4 - 3.8.
| Fix unclosed SQL database warnings when cython modules are used
| Fix the remaining test failures (django and appengine).
| Add tests for AS3 vectors and dictionaries.
| Update docs
| Don't use epydoc for docs
