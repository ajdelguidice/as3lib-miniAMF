# Parts of this file are loosely based on https://github.com/h5py/h5py/blob/master/setup_build.py
from pathlib import Path
import os
from platform import python_version_tuple
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext
from Cython import Tempita
from Cython.Build import cythonize


def localpath():
    return os.path.abspath(os.path.join(os.path.dirname(__file__)))

def get_extensions(ext_list:list):
    exts = []
    for ext in ext_list:
        raw_path = Path(localpath()).joinpath(ext).resolve()

        file = raw_path.with_suffix('.pyx')
        tempfile = raw_path.with_suffix('.temp.pyx')

        if not file.exists():
            continue

        if tempfile.exists():
            current_text = tempfile.read_text('utf-8')
        else:
            current_text = ''

        new_text = Tempita.sub(file.read_text(), PY_MAJOR_VERSION=int(python_version_tuple()[0]), PY_MINOR_VERSION=int(python_version_tuple()[1]))
        if new_text != current_text:
            tempfile.write_text(new_text, 'utf-8')

        exts.append(Extension(name=ext.replace('/','.'), sources=[f'{ext}.temp.pyx']))
    return exts

class Build(build_ext):
    def run(self):
        self.extensions = self.distribution.ext_modules = cythonize(get_extensions(["miniamf/_accel/util","miniamf/_accel/codec","miniamf/_accel/amf3","miniamf/_accel/amf0"]))

        self.swig_opts = None
        self.finalize_options()
        super().run()

if os.environ.get('MINIAMF_NO_CYTHON',"0") == "1":
    setup()
else:
    setup(
        ext_modules=[Extension('miniamf.x',['x.c'],optional=True)],
        cmdclass={'build_ext': Build}
    )
