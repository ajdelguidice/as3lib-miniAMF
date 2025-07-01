<b>This is heavily work in progress</b>

This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that works properly on newer python versions (currently only tested on 3.13). Miniamf made use of a lot of deprecated or removed functionality, especially in the cython modules, which means I had to rewrite a lot of stuff. If something doesn't work as expected, please let me know, I'll try to fix it as best as I can. The cython modules are no longer optional, I tried to make them optional but it didn't work out.

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
| &#95;&#95;init&#95;&#95; | :heavy_check_mark: :heavy_check_mark: | |
| &#95;version / versions | :heavy_check_mark: :heavy_check_mark: | |
| alias | :heavy_check_mark: :heavy_check_mark: | |
| amf0 | :o: :heavy_check_mark: | |
| amf3 | :o: :heavy_check_mark: | |
| codec | :o: :heavy_check_mark: | |
| sol | :heavy_check_mark: :heavy_check_mark: | |
| xml | :o: :heavy_check_mark: | |
| &#95;accel.amf0 | :o: :x: | Fails test_use_amf3 (test_amf0.EncoderTestCase.test_use_amf3). _accel.amf3.Encoder.writeDict does not sort keys (amf3.Encoder.writeDict also does other stuff that it does not do). Every time I try to fix this, everything else breaks so I might leave it the way it is. |
| &#95;accel.amf3 | :o: :x: | |
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
| util.imports | :o: :heavy_check_mark: | |
| util.pure | :o: :heavy_check_mark: | |
