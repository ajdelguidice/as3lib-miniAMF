<b>This is heavily work in progress</b>

This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that aims to work properly on newer python versions (3.11+). This could theoretically go down to 3.9 but PyFloat_Unpack{4,8} and PyFloat_Pack{4,8} were changed in 3.11 so I would need to do some backporting. Miniamf made use of a lot of deprecated or removed functionality, especially in the cython modules, which means I had to rewrite a lot of stuff. If something doesn't work as expected, please let me know, I'll try to fix it as best as I can.

This package currently uses the same directories as miniamf. They should not be installed together.

## Change Overview
Python 2 support has been removed.
<br>The cython modules now compile properly and pass all of the tests.
<br>The cython modules are no longer optional. I tried to make them optional but I couldn't figure out how to without breaking other stuff.
<br>Use importlib instead of pkg_resources.
<br>Use datetime.fromtimestamp instead of datetime.utcfromtimestamp.
<br>cElementTree can no longer be used for xml.
<br>sol.save and sol.load actually close their files.
<br>Replaces find_module with find_spec and spread load_module out into create_module and exec_module in util.imports.ModuleFinder

## Fork Coverage
Here's a list of everything in this fork and their status (&#95;&#95;init&#95;&#95; files that contain code included as well). Every module works according to the tests, I just have to make sure everything works on other python versions and look over each module to make sure things are done properly.

| Key |              |
| --- | ------------ |
| :heavy_check_mark: | Working and tested |
| - | Read notes |
| :o: | Untested |
| :x: | Broken |

The first mark is the status of the module itself (manual testing), the second is the status of the tests (passing or not).

| Module       | Status | Notes      |
| ------------ | ------ | ---------- |
| &#95;&#95;init&#95;&#95; | :heavy_check_mark: :heavy_check_mark: | |
| &#95;version / versions | :heavy_check_mark: :heavy_check_mark: | |
| alias | :heavy_check_mark: :heavy_check_mark: | |
| amf0 | :o: :heavy_check_mark: | |
| amf3 | :o: :heavy_check_mark: | |
| codec | :heavy_check_mark: :heavy_check_mark: | |
| sol | :heavy_check_mark: :heavy_check_mark: | |
| xml | :heavy_check_mark: :heavy_check_mark: | |
| &#95;accel.amf0 | :o: :heavy_check_mark: | |
| &#95;accel.amf3 | :o: :heavy_check_mark: | |
| &#95;accel.codec | :o: :heavy_check_mark: | |
| &#95;accel.util | :o: :heavy_check_mark: | |
| adapters.&#95;&#95;init&#95;&#95; | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;array | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;collections | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;decimal | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;sets | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;weakref | :heavy_check_mark: :heavy_check_mark: | |
| adapters.util | :heavy_check_mark: :heavy_check_mark: | |
| util.&#95;&#95;init&#95;&#95; | :heavy_check_mark: :heavy_check_mark: | |
| util.imports | :heavy_check_mark: :heavy_check_mark: | |
| util.pure | :o: :heavy_check_mark: | |
