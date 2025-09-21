# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Provides the pure Python version of L{BufferedByteStream}.

Do not reference directly, use L{miniamf.util.BufferedByteStream} instead.

@since: 0.6
"""

import struct
import io


def _get_endian_system():
    encoded = struct.pack("@I", 0x01020304)
    if encoded == b'\x01\x02\x03\x04':
        return ENDIAN_BIG
    elif encoded == b'\x04\x03\x02\x01':
        return ENDIAN_LITTLE
    else:
        raise ValueError("unrecognized system endianness: %r" % (encoded,))


#: Network byte order
ENDIAN_NETWORK = "!"

#: Native byte order
ENDIAN_NATIVE = "@"

#: Little endian
ENDIAN_LITTLE = "<"

#: Big endian
ENDIAN_BIG = ">"

#: System endian (whichever of "<" or ">" corresponds to the behavior of "@").
ENDIAN_SYSTEM = _get_endian_system()

#: All valid endianness strings
VALID_ENDIANS = (ENDIAN_NETWORK, ENDIAN_NATIVE, ENDIAN_LITTLE, ENDIAN_BIG)


def _compile_packers(endian):
    """
    Compile struct packers for all of the formats used by BufferedByteStream.
    Called whenever a BufferedByteStream's endianness is changed.
    """
    return {
        "B": struct.Struct(endian + "B"),
        "b": struct.Struct(endian + "b"),
        "h": struct.Struct(endian + "h"),
        "H": struct.Struct(endian + "H"),
        "l": struct.Struct(endian + "l"),
        "L": struct.Struct(endian + "L"),
        "d": struct.Struct(endian + "d"),
        "f": struct.Struct(endian + "f"),
    }


class BufferedByteStream(io.BytesIO):
    """
    I am a C{BytesIO} type object containing byte data from the AMF stream.

    Features:
     - Always read-write.
     - Raises L{IOError} if reading past end.
     - Allows you to C{peek()} into the stream.
     - Knows its length.

    @see: U{ByteArray on OSFlash
        <http://osflash.org/documentation/amf3#x0c_-_bytearray>}
    @see: U{Parsing ByteArrays on OSFlash
        <http://osflash.org/documentation/amf3/parsing_byte_arrays>}

    @ivar endian: Byte ordering used to represent the data. Default byte order
        is L{ENDIAN_NETWORK}.
    @type endian: ENDIAN_* code
    """

    def __init__(self, data=None, endian=ENDIAN_NETWORK):
        """
        @raise TypeError: C{data} is not acceptable to C{append}.
        """

        self.endian = endian
        self._len = 0

        if data is None:...
        elif isinstance(data, (str, bytes)):
            self.append(data)
        elif hasattr(data, 'getvalue'):
            self.append(data.getvalue())
        elif hasattr(data, 'read') and hasattr(data, 'seek') and hasattr(data, 'tell'):
            old_pos = data.tell()
            data.seek(0)
            self.append(data.read())
            data.seek(old_pos)
        else:
            raise TypeError("Unable to coerce buf->BufferedByteStream")

        self._pos = None

    def __len__(self):
        if self._len is None:
            with self:
                self.seek(0, 2)
                self._len = self.tell()

        return self._len

    def __enter__(self):
        self._pos = self.tell()

    def __exit__(self, *unused):
        if self._pos is not None:
            self.seek(self._pos, 0)

    def truncate(self, size=0):
        cur_pos = self.tell()
        super().truncate(size)
        self._len = size
        if self._len < cur_pos:
            self.seek(self._len)

    def read(self, length=-1):
        """
        If C{length} is -1 or unspecified, return the rest of the buffer.
        Otherwise, return exactly the specified number of bytes from the
        buffer.  Either way, advance the seek position over the data read.

        @raise IOError: Attempted to read past the end of the buffer.
        """
        if length == 0:
            return b''
        if length < -1:
            raise IOError("invalid read length: %r" % length)
        if self.at_eof():
            raise IOError(
                "Attempted to read from the buffer but already at the end")

        if length == -1:
            return super().read()
        else:
            if self.tell() + length > len(self):
                raise IOError(
                    "Attempted to read %d bytes from the buffer but only %d "
                    "remain" % (length, len(self) - self.tell())
                )
            return super().read(length)

    def peek(self, size=1):
        """
        Looks up to C{size} bytes ahead in the stream without changing the
        seek position.  Unlike C{read}, it is not an error to try to peek
        past the end of the buffer, and fewer than the number of requested
        bytes may be returned.

        @param size: Default is 1.
        @type size: C{int}
        @raise ValueError: Trying to peek backwards.

        @return: Bytes.
        """
        if size < -1:
            raise ValueError("Cannot peek backwards")

        if size == 0:
            return b''

        if size == -1:
            size = self.remaining()

        peeked = b''
        with self:
            while len(peeked) < size:
                c = super().read(1)
                if not c:
                    break
                peeked += c

        return peeked

    def consume(self):
        """
        Discard all of the data already read (from byte 0 up to C{tell()})
        and reset the seek position to the new beginning of the stream.

        @since: 0.4
        """
        rest = super().read()
        self.truncate(0)
        self.append(rest)

    def remaining(self):
        """
        Returns number of remaining bytes.

        @rtype: C{number}
        @return: Number of remaining bytes.
        """
        return len(self) - self.tell()

    def at_eof(self):
        """
        Returns C{True} if the seek position is at the end of the stream.

        @rtype: C{bool}
        """
        return self.tell() == len(self)

    def write(self, s):
        """
        Writes the content of the specified C{s} into this buffer at the
        current seek position, and advance the seek position.

        @param s: Raw bytes
        """
        super().write(s)
        self._len = None

    def append(self, data):
        """
        Append data to the end of the stream.  Does not change the
        seek position.

        @param data: The data to append to the stream.
        @type data: None, Unicode string, byte string, byte buffer, or
        any object with either a getvalue method or read+seek+tell
        methods.  In the latter two cases, the value returned by
        getvalue / read must be a Unicode string, byte string, or byte buffer.
        @raise TypeError: data is not convertible to a byte sequence.

        """

        if data is None:
            return

        pos = self.tell()
        self.seek(len(self))

        if hasattr(data, 'getvalue'):
            self.write_utf8_string(data.getvalue())
        else:
            self.write_utf8_string(data)

        self.seek(pos)

    def __add__(self, other):
        new = BufferedByteStream(self)
        new.append(other)
        return new

    # Methods for reading and writing typed data.
    @property
    def endian(self):
        """The endianness of this stream."""
        return self._endian

    @endian.setter
    def endian(self, val):
        if val not in VALID_ENDIANS:
            raise ValueError("invalid endianness code %r" % (val,))
        self._endian = val
        self._packers = _compile_packers(val)

    def _is_little_endian(self):
        if self._endian == ENDIAN_NATIVE:
            return ENDIAN_SYSTEM == ENDIAN_LITTLE
        return self._endian == ENDIAN_LITTLE

    def read_uchar(self):
        """
        Reads an C{unsigned char} from the stream.
        """
        return self._packers["B"].unpack(self.read(1))[0]

    def write_uchar(self, c):
        """
        Writes an C{unsigned char} to the stream.

        @param c: Unsigned char
        @type c: C{int}
        @raise TypeError: Unexpected type for int C{c}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(c, int):
            raise TypeError("expected an int, got %r" % type(c))

        if not 0 <= c <= 255:
            raise OverflowError("Not in range, %d" % c)

        self.write(self._packers["B"].pack(c))

    def read_char(self):
        """
        Reads a C{char} from the stream.
        """
        return self._packers["b"].unpack(self.read(1))[0]

    def write_char(self, c):
        """
        Write a C{char} to the stream.

        @param c: char
        @type c: C{int}
        @raise TypeError: Unexpected type for int C{c}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(c, int):
            raise TypeError("expected an int, got %r" % type(c))

        if not -128 <= c <= 127:
            raise OverflowError("Not in range, %d" % c)

        self.write(self._packers["b"].pack(c))

    def read_ushort(self):
        """
        Reads a 2 byte unsigned integer from the stream.
        """
        return self._packers["H"].unpack(self.read(2))[0]

    def write_ushort(self, s):
        """
        Writes a 2 byte unsigned integer to the stream.

        @param s: 2 byte unsigned integer
        @type s: C{int}
        @raise TypeError: Unexpected type for int C{s}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(s, int):
            raise TypeError("expected an int, got %r" % (type(s),))

        if not 0 <= s <= 65535:
            raise OverflowError("Not in range, %d" % s)

        self.write(self._packers["H"].pack(s))

    def read_short(self):
        """
        Reads a 2 byte integer from the stream.
        """
        return self._packers["h"].unpack(self.read(2))[0]

    def write_short(self, s):
        """
        Writes a 2 byte integer to the stream.

        @param s: 2 byte integer
        @type s: C{int}
        @raise TypeError: Unexpected type for int C{s}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(s, int):
            raise TypeError("expected an int, got %r" % (type(s),))

        if not -32768 <= s <= 32767:
            raise OverflowError("Not in range, %d" % s)

        self.write(self._packers["h"].pack(s))

    def read_ulong(self):
        """
        Reads a 4 byte unsigned integer from the stream.
        """
        return self._packers["L"].unpack(self.read(4))[0]

    def write_ulong(self, l):
        """
        Writes a 4 byte unsigned integer to the stream.

        @param l: 4 byte unsigned integer
        @type l: C{int}
        @raise TypeError: Unexpected type for int C{l}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(l, int):
            raise TypeError("expected an int, got %r" % (type(l),))

        if not 0 <= l <= 4294967295:
            raise OverflowError("Not in range, %d" % l)

        self.write(self._packers["L"].pack(l))

    def read_long(self):
        """
        Reads a 4 byte integer from the stream.
        """
        return self._packers["l"].unpack(self.read(4))[0]

    def write_long(self, l):
        """
        Writes a 4 byte integer to the stream.

        @param l: 4 byte integer
        @type l: C{int}
        @raise TypeError: Unexpected type for int C{l}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(l, int):
            raise TypeError("expected an int, got %r" % (type(l),))

        if not -2147483648 <= l <= 2147483647:
            raise OverflowError("Not in range, %d" % l)

        self.write(self._packers["l"].pack(l))

    def read_24bit_uint(self):
        """
        Reads a 24 bit unsigned integer from the stream.

        @since: 0.4
        """
        if self._is_little_endian():
            order = (0, 8, 16)
        else:
            order = (16, 8, 0)

        n = 0
        for x in order:
            n += (self.read_uchar() << x)

        return n

    def write_24bit_uint(self, n):
        """
        Writes a 24 bit unsigned integer to the stream.

        @since: 0.4
        @param n: 24 bit unsigned integer
        @type n: C{int}
        @raise TypeError: Unexpected type for int C{n}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(n, int):
            raise TypeError("expected an int, got %r" % (type(n),))

        if not 0 <= n <= 0xffffff:
            raise OverflowError("n is out of range")

        if self._is_little_endian():
            order = (0, 8, 16)
        else:
            order = (16, 8, 0)

        for x in order:
            self.write_uchar((n >> x) & 0xff)

    def read_24bit_int(self):
        """
        Reads a 24 bit integer from the stream.

        @since: 0.4
        """
        n = self.read_24bit_uint()

        if n & 0x800000 != 0:
            # the int is signed
            n -= 0x1000000

        return n

    def write_24bit_int(self, n):
        """
        Writes a 24 bit integer to the stream.

        @since: 0.4
        @param n: 24 bit integer
        @type n: C{int}
        @raise TypeError: Unexpected type for int C{n}.
        @raise OverflowError: Not in range.
        """
        if not isinstance(n, int):
            raise TypeError("expected an int, got %r" % (type(n),))

        if not -8388608 <= n <= 8388607:
            raise OverflowError("n is out of range")

        if n < 0:
            n += 0x1000000

        if self._is_little_endian():
            order = (0, 8, 16)
        else:
            order = (16, 8, 0)

        for x in order:
            self.write_uchar((n >> x) & 0xff)

    def read_double(self):
        """
        Reads an 8 byte float from the stream.
        """
        return self._packers["d"].unpack(self.read(8))[0]

    def write_double(self, d):
        """
        Writes an 8 byte float to the stream.

        @param d: 8 byte float
        @type d: C{float}
        @raise TypeError: Unexpected type for float C{d}.
        """
        if not isinstance(d, float):
            raise TypeError("expected a float, got %r" % (type(d),))

        self.write(self._packers["d"].pack(d))

    def read_float(self):
        """
        Reads a 4 byte float from the stream.
        """
        return self._packers["f"].unpack(self.read(4))[0]

    def write_float(self, f):
        """
        Writes a 4 byte float to the stream.

        @param f: 4 byte float
        @type f: C{float}
        @raise TypeError: Unexpected type for float C{f}.
        """
        if not isinstance(f, float):
            raise TypeError("expected a float, got %r" % (type(f),))

        self.write(self._packers["f"].pack(f))

    def read_utf8_string(self, length):
        """
        Reads a UTF-8 string from the stream.

        @rtype: Unicode string
        """
        return self.read(length).decode("utf-8")

    def write_utf8_string(self, u):
        """
        Writes a string to the stream.  If it is a Unicode object,
        it will be encoded in UTF-8; if it is a byte string, it will
        be written out as-is.

        @param u: string
        @raise TypeError: Unexpected type for C{u}
        """
        if isinstance(u, str):
            u = u.encode("utf-8")
        elif isinstance(u, bytearray):
            u = bytes(u)
        if not isinstance(u, bytes):
            raise TypeError("Expected a string, got %r" % (u,))
        self.write(u)
