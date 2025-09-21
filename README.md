# as3lib-miniamf
This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that aims to work properly on newer python versions. Miniamf made use of a lot of deprecated or removed functionality, especially in the cython modules, which means I had to rewrite a lot of stuff. If something doesn't work as expected, please let me know, I'll try to fix it as best as I can.

This package uses the same directories as miniamf. They should not be installed together.

While I am trying to bring back the remoting stuff, the stuff listed below will not be brought back:
- Elixir (never updated to python 3)
- Google AppEngine (SDK no longer easily accessible)

## Change Overview
Python 2 support has been removed.
<br>The cython modules now compile properly and pass all non-remoting tests.
<br>The cython modules are no longer optional. I tried to make them optional but I couldn't figure out how to without breaking other stuff.
<br>Use importlib instead of pkg_resources.
<br>Use datetime.fromtimestamp instead of datetime.utcfromtimestamp.
<br>cElementTree can no longer be used for xml.
<br>sol.save and sol.load actually the files they opened.
<br>Replaces find_module with find_spec and spread load_module out into create_module and exec_module in util.imports.ModuleFinder
<br>util.pure.BufferedByteStream is now a child of io.BytesIO. I saw no reason not to do this as python 2 is no longer a support target. Excursion has also been removed because it isn't needed anymore.
<br>Remoting support has been partially brought back. The gateways currently available are wsgi and django. The adapters currently available are Django and SQLAlchemy.
<br>A utcnow function has been added to miniamf.util because remoting support requires it

## TODO
Test cython modules on 3.9
<br>Make cython modules optional
<br>Bring back twisted support. (I'm having a bit of trouble with this)
<br>Add tests for AS3 vectors and dictionaries.
<br>Fix Django adapters
