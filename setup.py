from setuptools import setup, Extension

if __name__ == "__main__":
    nocython = False
    try:
        import Cython
    except:
        nocython = True
    if nocython:
        setup()
    else:
        setup(
            ext_modules=[
                Extension(name = "miniamf._accel.util", sources = ["miniamf/_accel/util.pyx"]),
                Extension(name = "miniamf._accel.codec", sources = ["miniamf/_accel/codec.pyx"]),
                Extension(name = "miniamf._accel.amf3", sources = ["miniamf/_accel/amf3.pyx"]),
                Extension(name = "miniamf._accel.amf0", sources = ["miniamf/_accel/amf0.pyx"])
            ]
        )
