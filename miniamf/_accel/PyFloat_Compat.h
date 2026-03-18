#ifdef __cplusplus
extern "C" {
#endif

#include <Python.h>

#ifdef _PyFloat_Pack4
int PyFloat_Pack4(double x, char *p, int le) {
    return _PyFloat_Pack4(x, (unsigned char *)p, le);
}
#endif
#ifdef _PyFloat_Pack8
int PyFloat_Pack8(double x, char *p, int le) {
    return _PyFloat_Pack8(x, (unsigned char *)p, le);
}
#endif
#ifdef _PyFloat_Unpack4
double PyFloat_Unpack4(const char *p, int le) {
    return _PyFloat_Unpack4((const unsigned char*)p, le);
}
#endif
#ifdef _PyFloat_Unpack8
double PyFloat_Unpack8(const char *p, int le) {
    return _PyFloat_Unpack8((const unsigned char*)p, le);
}
#endif

#ifdef __cplusplus
}
#endif
