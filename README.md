<b>This is heavily work in progress</b>

This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that works properly on newer python versions (currently only tested on 3.13). Miniamf made use of a lot of deprecated or removed functionality, especially in the cython modules, which means I had to rewrite a lot of stuff. The cython modules at least compile now, however I'm not sure if everything in them works as it should. If something doesn't work as expected, please let me know, I'll try to fix it as best as I can.

Supporting python 2 at this point would require a massive amount of backporting work so I just decided to remove it.

## Fork Coverage
Here's a list of everything in this fork and their status (&#95;&#95;init&#95;&#95; files that contain code included as well). I'm not very concerned about the functionality of most of the pure python module since they used <a href="https://pypi.org/project/six/">six</a> for most of the cross version functionality but the cython modules will likely be more broken due to api changes from python 2 to python 3.

:heavy_check_mark: - Working and tested
<b>-</b> - Check notes
:o: - Untested
:x: - Broken

| Module       | Component  | Status | Notes      |
| ------------ | ---------- | ------ | ---------- |
| &#95;&#95;init&#95;&#95; | | :o: | |
| &#95;version / versions | | :o: | |
| alias | | :o: | |
| amf0 | | :o: | |
| amf3 | | :o: | |
| codec | | :o: | |
| sol | | - | There does not seem to be anything wrong with the module itself but it relies on other things that might be broken |
| xml | | :o: | |
| &#95;accel.amf0 | | :o: | |
| &#95;accel.amf3 | | :o: | |
| &#95;accel.codec | | :o: | |
| &#95;accel.util | | - | Seems to work mostly fine but some stuff that I haven't tested yet could still be broken due to differences between python 2 and python 3 |
| adapters.&#95;&#95;init&#95;&#95; | | :o: | |
| adapters.&#95;array | | :o: | |
| adapters.&#95;collections | | :o: | |
| adapters.&#95;decimal | | :x: | I attempted to fix this but it seems that python 3's decimal.Decimal objects can not be encoded with the current encoder |
| adapters.&#95;sets | | :o: | |
| adapters.&#95;weakref | | :o: | |
| adapters.util | | :heavy_check_mark: | |
| util.&#95;&#95;init&#95;&#95; | | :o: | |
| util.imports | | :x: | This uses a lot of deprecated or removed functionality of the import system. This must be comletely rewritten (partially functional up until python 3.12 but breaks after that) |
| util.pure | | - | This should be mostly working since I can read and write shared objects and bytearrays just fine but I haven't tested it |

