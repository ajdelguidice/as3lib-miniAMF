# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Local Shared Object implementation.

Local Shared Object (LSO), sometimes known as Adobe Flash cookies, is a
cookie-like data entity used by the Adobe Flash Player and Gnash. The players
allow web content to read and write LSO data to the computer's local drive on
a per-domain basis.

@see: U{Local Shared Object on WikiPedia
    <http://en.wikipedia.org/wiki/Local_Shared_Object>}
@since: 0.1
"""

import miniamf
from miniamf import util

#: Magic Number - 2 bytes
HEADER_VERSION = b'\x00\xbf'
#: Marker - 10 bytes
HEADER_SIGNATURE = b'TCSO\x00\x04\x00\x00\x00\x00'
#: Padding - 4 bytes
PADDING_BYTE = b'\x00'


def decode(stream, strict=True):
    """
    Decodes a SOL stream. L{strict} mode ensures that the sol stream is as spec
    compatible as possible.

    @return: A C{tuple} containing the C{root_name} and a C{dict} of name,
        value pairs.
    """
    if not isinstance(stream, util.BufferedByteStream):
        stream = util.BufferedByteStream(stream)

    # read the version
    version = stream.read(2)

    if version != HEADER_VERSION:
        raise miniamf.DecodeError("Unknown SOL version in header")

    # read the length
    length = stream.read_ulong()

    if strict and stream.remaining() != length:
        raise miniamf.DecodeError("Inconsistent stream header length")

    # read the signature
    signature = stream.read(10)

    if signature != HEADER_SIGNATURE:
        raise miniamf.DecodeError("Invalid signature")

    length = stream.read_ushort()
    root_name = stream.read_utf8_string(length)

    # read padding
    if stream.read(3) != PADDING_BYTE * 3:
        raise miniamf.DecodeError("Invalid padding read")

    decoder = miniamf.get_decoder(stream.read_uchar())
    decoder.stream = stream

    values = {}

    while 1:
        if stream.at_eof():
            break

        name = decoder.readString()
        value = decoder.readElement()

        # read the padding
        if stream.read(1) != PADDING_BYTE:
            raise miniamf.DecodeError("Missing padding byte")

        values[name] = value

    return (root_name, values)


def encode(name, values, strict=True, encoding=miniamf.AMF0):
    """
    Produces a SharedObject encoded stream based on the name and values.

    @param name: The root name of the SharedObject.
    @param values: A `dict` of name value pairs to be encoded in the stream.
    @param strict: Ensure that the SOL stream is as spec compatible as
        possible.
    @return: A SharedObject encoded stream.
    @rtype: L{BufferedByteStream<miniamf.util.BufferedByteStream>}, a file like
        object.
    """
    encoder = miniamf.get_encoder(encoding)
    stream = encoder.stream

    # write the header
    stream.write(HEADER_VERSION)

    if strict:
        length_pos = stream.tell()

    stream.write_ulong(0)

    # write the signature
    stream.write(HEADER_SIGNATURE)

    # write the root name
    name = name.encode("utf-8")

    stream.write_ushort(len(name))
    stream.write(name)

    # write the padding
    stream.write(PADDING_BYTE * 3)
    stream.write_uchar(encoding)
    for n, v in values.items():
        encoder.serialiseString(n)
        encoder.writeElement(v)

        # write the padding
        stream.write(PADDING_BYTE)

    if strict:
        stream.seek(length_pos)
        stream.write_ulong(stream.remaining() - 4)

    stream.seek(0)

    return stream


def _load(f):
    name, values = decode(f.read())
    s = SOL(name)

    for n, v in values.items():
        s[n] = v

    return s


def load(name_or_file):
    """
    Loads a sol file and returns a L{SOL} object.

    @param name_or_file: Name of file, or file-object.
    @type name_or_file: C{string}
    """
    f = name_or_file

    if isinstance(name_or_file, str):
        with open(name_or_file, "rb") as f:
            return _load(f)
    elif not hasattr(f, "read"):
        raise ValueError("Readable stream expected")
    else:
        return _load(f)


def save(sol, name_or_file, encoding=miniamf.AMF0):
    """
    Writes a L{SOL} object to C{name_or_file}.

    @param name_or_file: Name of file or file-object to write to.
    @param encoding: AMF encoding type.
    """
    f = name_or_file
    encoded = encode(sol.name, sol, encoding=encoding).getvalue()

    if isinstance(name_or_file, str):
        with open(name_or_file, "wb+") as f:
            f.write(encoded)
    elif not hasattr(f, "write"):
        raise ValueError("Writable stream expected")
    else:
        f.write(encoded)


class SOL(dict):
    """
    Local Shared Object class, allows easy manipulation of the internals of a
    C{sol} file.
    """
    def __init__(self, name):
        self.name = name

    def save(self, name_or_file, encoding=miniamf.AMF0):
        save(self, name_or_file, encoding)

    def __repr__(self):
        return "<%s %s %s at 0x%x>" % (
            self.__class__.__name__,
            self.name,
            dict.__repr__(self),
            id(self)
        )


LSO = SOL
