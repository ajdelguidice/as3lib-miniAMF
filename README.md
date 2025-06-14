<b>This is heavily work in progress</b>

This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that works properly on newer python versions (currently only tested on 3.13). Miniamf made use of a lot of deprecated or removed functionality, especially in the cython modules, which means I had to rewrite a lot of stuff. The cython modules at least compile now, however I'm not sure if everything in them works as it should. If something doesn't work as expected, please let me know, I'll try to fix it as best as I can.

Supporting python 2 at this point would require a massive amount of backporting work so I just decided to remove it.

## Fork Coverage
Here's a list of everything in this fork and their status (&#95;&#95;init&#95;&#95; files that contain code included as well). I'm not very concerned about the functionality of most of the pure python module since they used <a href="https://pypi.org/project/six/">six</a> for most of the cross version functionality but the cython modules will likely be more broken due to api changes from python 2 to python 3.

| Key |              |
| --- | ------------ |
| :heavy_check_mark: | Working and tested |
| - | Check notes |
| :o: | Untested |
| :x: | Broken |


| Module       | Status | Notes      |
| ------------ | ------ | ---------- |
| &#95;&#95;init&#95;&#95; | :o: | |
| &#95;version / versions | :heavy_check_mark: | |
| alias | :o: | |
| amf0 | - | Should work but not fully tested. |
| amf3 | - | Should work but not fully tested. |
| codec | :o: | |
| sol | - | There does not seem to be anything wrong with the module itself but it relies on other things that might be broken |
| xml | :o: | |
| &#95;accel.amf0 | :o: | |
| &#95;accel.amf3 | :o: | |
| &#95;accel.codec | :o: | |
| &#95;accel.util | - | Seems to work mostly fine but some stuff that I haven't tested yet could still be broken due to differences between python 2 and python 3 |
| adapters.&#95;&#95;init&#95;&#95; | :heavy_check_mark: | |
| adapters.&#95;array | :heavy_check_mark: | |
| adapters.&#95;collections | :heavy_check_mark: | |
| adapters.&#95;decimal | :heavy_check_mark: | |
| adapters.&#95;sets | :heavy_check_mark: | |
| adapters.&#95;weakref | :heavy_check_mark: | |
| adapters.util | :heavy_check_mark: | |
| util.&#95;&#95;init&#95;&#95; | :o: | |
| util.imports | - | This mostly works now, however it still uses deprecated functionality and will break in python 3.15 when that is released. I'm still trying to fix this. |
| util.pure | - | Should work but not fully tested. |
