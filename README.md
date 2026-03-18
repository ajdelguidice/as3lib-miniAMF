# as3lib-miniAMF
This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that aims to bring back some of the cut/broken functionality and work properly on newer python versions. Python 3.9 is the lowest version that this library can support while still supporting newer versions.

This package uses the same directories as miniamf. Installing them together will break both of them.

## Changes
- Python 2 support has been removed
- The _accel modules have been fixed
- The _accel modules are optional and can be disabled by setting the environment variable 'MINIAMF_NO_CYTHON' to 1. This currently breaks some stuff but I'm working on it.
- pkg_resources (setuptools) has been replaced with importlib.resources
- The deprecated cElementTree can no longer be used for xml related stuff
- sol.save and sol.load now properly manage the files that they manipulate
- util.imports.ModuleFinder has been updated to use find_spec, create_module, and exec_module instead of the deprecated find_module and load_module
- Partial support for AS3 Dictionaries and Vectors has been added. The implementation used is adapted from <a href="https://github.com/fmoo/pyamf/commit/67d2bf2a0da9b940d96cff6cc98156349cad276f">this commit</a>.
- util.pure.BufferedByteStream has been rewritten as a child of io.BytesIO. This shouldn't break things more than they already were.
- util.pure.Excursion has been removed because it is no longer needed.
- The functions utcnow and utcfromtimestamp were added to the util module as future proofing for when they are removed from datetime.
- Flex and remoting support have been brought back. Every gateway/adapter has been brought back except for Elixir. NOTE: <a href="https://github.com/StdCarrot/Py3AMF/commit/5a9963f2ee5622b638dcccb374fdc3c70fdc567d">this commit</a> was used as a reference to fix the twisted tests.

Elixir support will not be brought back due to being the project being abandoned.

## TODO
Fix library when cython modules are not installed.
<br>Fix unclosed SQL database warnings when cython modules are used
<br>Fix the remaining test failures (django and appengine). These only fail sometimes, which is weird.
<br>Add tests for AS3 vectors and dictionaries.
<br>Update docs
