# as3lib-miniAMF
This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that aims to bring back some of the cut/broken functionality and work properly on newer python versions. Python 3.9 is the lowest version that I have been able to get working.

This package uses the same directories as miniamf. Installing them together will break both of them.

## Changes
- Removed Python 2 support
- Fixed _accel modules
- Replaced pkg_resources (setuptools) with importlib.resources
- Removed the deprecated cElementTree from xml related stuff
- Properly manage files in sol.save and sol.load
- Updated util.imports.ModuleFinder to use find_spec, create_module, and exec_module instead of the deprecated find_module and load_module
- Added partial support for AS3 Dictionaries and Vectors. The implementation used is adapted from <a href="https://github.com/fmoo/pyamf/commit/67d2bf2a0da9b940d96cff6cc98156349cad276f">this commit</a>.
- Refactored util.pure.BufferedByteStream to remove util.pure.Excursion. It is now a child of io.BytesIO.
- Added utcnow and utcfromtimestamp to the util module in preperation for their removal from datetime.
- Brought back the flex and remoting support that was cut in miniamf. Everything except Elixir is present. NOTE: <a href="https://github.com/StdCarrot/Py3AMF/commit/5a9963f2ee5622b638dcccb374fdc3c70fdc567d">this commit</a> was used as a reference to fix the twisted tests.

Elixir support will not be brought back due to being the project being abandoned.

## TODO
Fix library when cython modules are not installed.
<br>Use the original MiniAMF version system.
<br>Attempt to get Python 3.4 - 3.9 working
<br>Fix unclosed SQL database warnings when cython modules are used
<br>Fix the remaining test failures (django and appengine).
<br>Add tests for AS3 vectors and dictionaries.
<br>Update docs
<br>Migrate docs to sphinx
