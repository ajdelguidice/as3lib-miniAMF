#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>

#if PY_VERSION_HEX < 0x030b0000
int PyFloat_Pack4(double x, char *p, int le) {
    return _PyFloat_Pack4(x, (unsigned char *)p, le);
}
int PyFloat_Pack8(double x, char *p, int le) {
    return _PyFloat_Pack8(x, (unsigned char *)p, le);
}
double PyFloat_Unpack4(const char *p, int le) {
    return _PyFloat_Unpack4((const unsigned char*)p, le);
}
double PyFloat_Unpack8(const char *p, int le) {
    return _PyFloat_Unpack8((const unsigned char*)p, le);
}
#endif

#ifdef __cplusplus
}
#endif
