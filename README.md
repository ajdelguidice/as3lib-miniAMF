<b>This is a heavily work in progress project</b>

This is a fork of <a href="https://pypi.org/project/Mini-AMF/">Mini-AMF</a> that works properly on newer python versions (currently only tested on 3.13). Miniamf made use of a lot of deprecated or removed functionality, especially in the c modules, which means I had to rewrite a lot of stuff. The cython modules have also been fixed, however I'm not sure if everything in them works as it should. If something doesn't work as expected, please let me know, I'll try to fix it as best as I can.

Supporting python 2 at this point would require a massive amount of backporting work so I just decided to remove it.
