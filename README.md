<b>This is heavily work in progress</b>

This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that works properly on newer python versions (currently only tested on 3.13). Miniamf made use of a lot of deprecated or removed functionality, especially in the cython modules, which means I had to rewrite a lot of stuff. The cython modules at least compile now, however I'm not sure if everything in them works as it should. If something doesn't work as expected, please let me know, I'll try to fix it as best as I can.

Supporting python 2 at this point would require a massive amount of backporting work so I just decided to remove it.

## Fork Coverage
Here's a list of everything in this fork and their status (&#95;&#95;init&#95;&#95; files that contain code included as well). All pure python modules work properly (according to the test suite) but the cython modules fail some tests (currently 1).

| Key |              |
| --- | ------------ |
| :heavy_check_mark: | Working and tested |
| - | Read notes |
| :o: | Untested |
| :x: | Broken |

The first mark is the status of the module itself (manual testing), the second is the status of the tests (passing or not).

| Module       | Status | Notes      |
| ------------ | ------ | ---------- |
| &#95;&#95;init&#95;&#95; | :o: :heavy_check_mark: | |
| &#95;version / versions | :heavy_check_mark: :heavy_check_mark: | |
| alias | :o: :heavy_check_mark: | |
| amf0 | :o: :heavy_check_mark: | |
| amf3 | :o: :heavy_check_mark: | |
| codec | :o: :heavy_check_mark: | |
| sol | :heavy_check_mark: :heavy_check_mark: | |
| xml | :o: :heavy_check_mark: | |
| &#95;accel.amf0 | :o: :x: | Fails test_use_amf3 (test_amf0.EncoderTestCase.test_use_amf3). _accel.amf3.Encoder.writeDict does not sort keys (amf3.Encoder.writeDict also does other stuff that it does not do). Every time I try to fix this, everything else breaks so I might leave it the way it is. |
| &#95;accel.amf3 | :o: :x: | |
| &#95;accel.codec | :o: :heavy_check_mark: | |
| &#95;accel.util | :o: :heavy_check_mark: | |
| adapters.&#95;&#95;init&#95;&#95; | - :heavy_check_mark: | PackageImporter is broken when I try to use nondeprecated functions in util.imports (error says likely due to circular import) |
| adapters.&#95;array | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;collections | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;decimal | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;sets | :heavy_check_mark: :heavy_check_mark: | |
| adapters.&#95;weakref | :heavy_check_mark: :heavy_check_mark: | |
| adapters.util | :heavy_check_mark: :heavy_check_mark: | |
| util.&#95;&#95;init&#95;&#95; | :o: :heavy_check_mark: | |
| util.imports | - - | This mostly works now, however it still uses deprecated functionality and will break in python 3.15 when that is released. I'm still trying to fix this. |
| util.pure | :o: :heavy_check_mark: | |
