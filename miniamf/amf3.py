# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
AMF3 implementation.

C{AMF3} is the default serialization for
U{ActionScript<http://en.wikipedia.org/wiki/ActionScript>} 3.0 and
provides various advantages over L{AMF0<miniamf.amf0>}, which is used
for ActionScript 1.0 and 2.0. It adds support for sending C{int} and
C{uint} objects as integers and supports data types that are available
only in ActionScript 3.0, such as L{ByteArray} and L{ArrayCollection}.

@see: U{Official AMF3 Specification in English
<http://opensource.adobe.com/wiki/download/attachments/1114283/amf3_spec_05_05_08.pdf>}
@see: U{Official AMF3 Specification in Japanese
<http://opensource.adobe.com/wiki/download/attachments/1114283/JP_amf3_spec_121207.pdf>}
@see: U{AMF3 documentation on OSFlash
<http://osflash.org/documentation/amf3>}

@since: 0.1

"""

import datetime
import zlib

import miniamf
from . import codec, util, xml


__all__ = [
    'ByteArray',
    'Context',
    'Encoder',
    'Decoder',
]


#: The undefined type is represented by the undefined type marker. No further
#: information is encoded for this value.
TYPE_UNDEFINED = b'\x00'
#: The null type is represented by the null type marker. No further
#: information is encoded for this value.
TYPE_NULL = b'\x01'
#: The false type is represented by the false type marker and is used to
#: encode a Boolean value of C{false}. No further information is encoded for
#: this value.
TYPE_BOOL_FALSE = b'\x02'
#: The true type is represented by the true type marker and is used to encode
#: a Boolean value of C{true}. No further information is encoded for this
#: value.
TYPE_BOOL_TRUE = b'\x03'
#: In AMF 3 integers are serialized using a variable length signed 29-bit
#: integer.
#: @see: U{Parsing Integers on OSFlash (external)
#: <http://osflash.org/amf3/parsing_integers>}
TYPE_INTEGER = b'\x04'
#: This type is used to encode an ActionScript Number or an ActionScript
#: C{int} of value greater than or equal to 2^28 or an ActionScript uint of
#: value greater than or equal to 2^29. The encoded value is is always an 8
#: byte IEEE-754 double precision floating point value in network byte order
#: (sign bit in low memory). The AMF 3 number type is encoded in the same
#: manner as the AMF 0 L{Number<miniamf.amf0.TYPE_NUMBER>} type.
TYPE_NUMBER = b'\x05'
#: ActionScript String values are represented using a single string type in
#: AMF 3 - the concept of string and long string types from AMF 0 is not used.
#: Strings can be sent as a reference to a previously occurring String by
#: using an index to the implicit string reference table. Strings are encoding
#: using UTF-8 - however the header may either describe a string literal or a
#: string reference.
TYPE_STRING = b'\x06'
#: ActionScript 3.0 introduced a new XML type however the legacy C{XMLDocument}
#: type from ActionScript 1.0 and 2.0.is retained in the language as
#: C{flash.xml.XMLDocument}. Similar to AMF 0, the structure of an
#: C{XMLDocument} needs to be flattened into a string representation for
#: serialization. As with other strings in AMF, the content is encoded in
#: UTF-8. XMLDocuments can be sent as a reference to a previously occurring
#: C{XMLDocument} instance by using an index to the implicit object reference
#: table.
#: @see: U{OSFlash documentation (external)
#: <http://osflash.org/documentation/amf3
#:     #x07_-_xml_legacy_flash.xml.xmldocument_class>}
TYPE_XML = b'\x07'
#: In AMF 3 an ActionScript Date is serialized as the number of
#: milliseconds elapsed since the epoch of midnight, 1st Jan 1970 in the
#: UTC time zone. Local time zone information is not sent.
TYPE_DATE = b'\x08'
#: ActionScript Arrays are described based on the nature of their indices,
#: i.e. their type and how they are positioned in the Array.
TYPE_ARRAY = b'\x09'
#: A single AMF 3 type handles ActionScript Objects and custom user classes.
TYPE_OBJECT = b'\x0A'
#: ActionScript 3.0 introduces a new top-level XML class that supports
#: U{E4X<http://en.wikipedia.org/wiki/E4X>} syntax.
#: For serialization purposes the XML type needs to be flattened into a
#: string representation. As with other strings in AMF, the content is
#: encoded using UTF-8.
TYPE_XMLSTRING = b'\x0B'
#: ActionScript 3.0 introduces the L{ByteArray} type to hold an Array
#: of bytes. AMF 3 serializes this type using a variable length encoding
#: 29-bit integer for the byte-length prefix followed by the raw bytes
#: of the L{ByteArray}.
#: @see: U{Parsing ByteArrays on OSFlash (external)
#: <http://osflash.org/documentation/amf3/parsing_byte_arrays>}
TYPE_BYTEARRAY = b'\x0C'

#: Reference bit.
REFERENCE_BIT = 0x01

#: The maximum value for an int that will avoid promotion to an
#: ActionScript Number when sent via AMF 3 is represented by a
#: signed 29 bit integer: 2^28 - 1.
MAX_29B_INT = 0x0FFFFFFF

#: The minimum that can be represented by a signed 29 bit integer.
MIN_29B_INT = -0x10000000

ENCODED_INT_CACHE = {}


class ObjectEncoding:
    """
    AMF object encodings.
    """
    #: Property list encoding.
    #: The remaining integer-data represents the number of class members that
    #: exist. The property names are read as string-data. The values are then
    #: read as AMF3-data.
    STATIC = 0x00

    #: Externalizable object.
    #: What follows is the value of the "inner" object, including type code.
    #: This value appears for objects that implement IExternalizable, such as
    #: L{ArrayCollection} and L{ObjectProxy}.
    EXTERNAL = 0x01

    #: Name-value encoding.
    #: The property names and values are encoded as string-data followed by
    #: AMF3-data until there is an empty string property name. If there is a
    #: class-def reference there are no property names and the number of values
    #: is equal to the number of properties in the class-def.
    DYNAMIC = 0x02


class DataOutput(object):
    """
    I am a C{StringIO} type object containing byte data from the AMF stream.
    ActionScript 3.0 introduced the C{flash.utils.ByteArray} class to support
    the manipulation of raw data in the form of an Array of bytes.
    I provide a set of methods for writing binary data with ActionScript 3.0.

    This class is the I/O counterpart to the L{DataInput} class, which reads
    binary data.

    @see: U{IDataOutput on Adobe Help (external)
    <http://help.adobe.com/en_US/FlashPlatform/reference/actionscript/3/flash/utils/IDataOutput.html>}
    """

    def __init__(self, encoder):
        """
        @param encoder: Encoder containing the stream.
        @type encoder: L{amf3.Encoder<miniamf.amf3.Encoder>}
        """
        self.encoder = encoder
        self.stream = encoder.stream

    def writeBoolean(self, value):
        """
        Writes a Boolean value.

        @type value: C{bool}
        @param value: A C{Boolean} value determining which byte is written.
        If the parameter is C{True}, C{1} is written; if C{False}, C{0} is
        written.

        @raise ValueError: Non-boolean value found.
        """
        if not isinstance(value, bool):
            raise ValueError("Non-boolean value found")

        if value is True:
            self.stream.write_uchar(1)
        else:
            self.stream.write_uchar(0)

    def writeByte(self, value):
        """
        Writes a byte.

        @type value: C{int}
        """
        self.stream.write_char(value)

    def writeUnsignedByte(self, value):
        """
        Writes an unsigned byte.

        @type value: C{int}
        @since: 0.5
        """
        return self.stream.write_uchar(value)

    def writeDouble(self, value):
        """
        Writes an IEEE 754 double-precision (64-bit) floating
        point number.

        @type value: C{number}
        """
        self.stream.write_double(value)

    def writeFloat(self, value):
        """
        Writes an IEEE 754 single-precision (32-bit) floating
        point number.

        @type value: C{float}
        """
        self.stream.write_float(value)

    def writeInt(self, value):
        """
        Writes a 32-bit signed integer.

        @type value: C{int}
        """
        self.stream.write_long(value)

    def writeMultiByte(self, value, charset):
        """
        Writes a multibyte string to the datastream using the
        specified character set.

        @type value: string
        @param value: The string value to be written.
        @type charset: string
        @param charset: The string denoting the character set to use. Possible
            character set strings include C{shift-jis}, C{cn-gb},
            C{iso-8859-1} and others.
        @see: U{Supported character sets on Adobe Help (external)
            <http://help.adobe.com/en_US/FlashPlatform/reference/actionscript/3/charset-codes.html>}
        """
        if isinstance(value, str):
            value = value.encode(charset)

        self.stream.write(value)

    def writeObject(self, value):
        """
        Writes an object to data stream in AMF serialized format.

        @param value: The object to be serialized.
        """
        self.encoder.writeElement(value)

    def writeShort(self, value):
        """
        Writes a 16-bit integer.

        @type value: C{int}
        @param value: A byte value as an integer.
        """
        self.stream.write_short(value)

    def writeUnsignedShort(self, value):
        """
        Writes a 16-bit unsigned integer.

        @type value: C{int}
        @param value: A byte value as an integer.
        @since: 0.5
        """
        self.stream.write_ushort(value)

    def writeUnsignedInt(self, value):
        """
        Writes a 32-bit unsigned integer.

        @type value: C{int}
        @param value: A byte value as an unsigned integer.
        """
        self.stream.write_ulong(value)

    def writeUTF(self, value):
        """
        Writes a UTF-8 string to the data stream.

        The length of the UTF-8 string in bytes is written first,
        as a 16-bit integer, followed by the bytes representing the
        characters of the string.

        @type value: string
        @param value: The string value to be written.
        """
        if not isinstance(value, bytes):
            value = value.encode("utf-8")

        self.stream.write_ushort(len(value))
        self.stream.write(value)

    def writeUTFBytes(self, value):
        """
        Writes a UTF-8 string. Similar to L{writeUTF}, but does
        not prefix the string with a 16-bit length word.

        @type value: string
        @param value: The string value to be written.
        """
        if not isinstance(value, bytes):
            value = value.encode("utf-8")

        self.stream.write(value)


class DataInput(object):
    """
    I provide a set of methods for reading binary data with ActionScript 3.0.

    This class is the I/O counterpart to the L{DataOutput} class, which writes
    binary data.

    @see: U{IDataInput on Adobe Help (external)
    <http://help.adobe.com/en_US/FlashPlatform/reference/actionscript/3/flash/utils/IDataInput.html>}
    """

    def __init__(self, decoder=None):
        """
        @param decoder: AMF3 decoder containing the stream.
        @type decoder: L{amf3.Decoder<miniamf.amf3.Decoder>}
        """
        self.decoder = decoder
        self.stream = decoder.stream

    def readBoolean(self):
        """
        Read C{Boolean}.

        @raise ValueError: Error reading Boolean.
        @rtype: C{bool}
        @return: A Boolean value, C{True} if the byte
        is nonzero, C{False} otherwise.
        """
        byte = self.stream.read(1)

        if byte == b'\x00':
            return False
        if byte == b'\x01':
            return True
        raise ValueError("Error reading boolean")

    def readByte(self):
        """
        Reads a signed byte.

        @rtype: C{int}
        @return: The returned value is in the range -128 to 127.
        """
        return self.stream.read_char()

    def readDouble(self):
        """
        Reads an IEEE 754 double-precision floating point number from the
        data stream.

        @rtype: C{number}
        @return: An IEEE 754 double-precision floating point number.
        """
        return self.stream.read_double()

    def readFloat(self):
        """
        Reads an IEEE 754 single-precision floating point number from the
        data stream.

        @rtype: C{number}
        @return: An IEEE 754 single-precision floating point number.
        """
        return self.stream.read_float()

    def readInt(self):
        """
        Reads a signed 32-bit integer from the data stream.

        @rtype: C{int}
        @return: The returned value is in the range -2147483648 to 2147483647.
        """
        return self.stream.read_long()

    def readMultiByte(self, length, charset):
        """
        Reads a multibyte string of specified length from the data stream
        using the specified character set.

        @type length: C{int}
        @param length: The number of bytes from the data stream to read.
        @type charset: string
        @param charset: The string denoting the character set to use.

        @rtype: string
        @return: Unicode string
        """

        bytes = self.stream.read(length)
        return bytes.decode(charset)

    def readObject(self):
        """
        Reads an object from the data stream.

        @return: The deserialized object.
        """
        return self.decoder.readElement()

    def readShort(self):
        """
        Reads a signed 16-bit integer from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range -32768 to 32767.
        """
        return self.stream.read_short()

    def readUnsignedByte(self):
        """
        Reads an unsigned byte from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range 0 to 255.
        """
        return self.stream.read_uchar()

    def readUnsignedInt(self):
        """
        Reads an unsigned 32-bit integer from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range 0 to 4294967295.
        """
        return self.stream.read_ulong()

    def readUnsignedShort(self):
        """
        Reads an unsigned 16-bit integer from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range 0 to 65535.
        """
        return self.stream.read_ushort()

    def readUTF(self):
        """
        Reads a UTF-8 string from the data stream.

        The string is assumed to be prefixed with an unsigned
        short indicating the length in bytes.

        @rtype: Unicode string
        """
        length = self.stream.read_ushort()
        return self.stream.read_utf8_string(length)

    def readUTFBytes(self, length):
        """
        Reads a sequence of C{length} UTF-8 bytes from the data
        stream and returns a string.

        @type length: C{int}
        @param length: The number of bytes from the data stream to read.
        @rtype: Unicode string
        """
        return self.readMultiByte(length, "utf-8")


class ByteArray(util.BufferedByteStream, DataInput, DataOutput):
    """
    I am a C{StringIO} type object containing byte data from the AMF stream.
    ActionScript 3.0 introduced the C{flash.utils.ByteArray} class to support
    the manipulation of raw data in the form of an Array of bytes.

    Supports C{zlib} compression.

    Possible uses of the C{ByteArray} class:
     - Creating a custom protocol to connect to a client.
     - Writing your own AMF/Remoting packet.
     - Optimizing the size of your data by using custom data types.

    @see: U{ByteArray on Adobe Help (external)
    <http://help.adobe.com/en_US/FlashPlatform/reference/actionscript/3/flash/utils/ByteArray.html>}
    """

    _zlib_header = b'\x78\x9c'

    class __amf__:
        amf3 = True

    def __init__(self, buf=None):
        self.context = Context()

        util.BufferedByteStream.__init__(self, buf)
        DataInput.__init__(self, Decoder(self, self.context))
        DataOutput.__init__(self, Encoder(self, self.context))

        self.compressed = self.peek(2) == ByteArray._zlib_header

    def readObject(self):
        self.context.clear()

        return super(ByteArray, self).readObject()

    def writeObject(self, obj):
        self.context.clear()

        return super(ByteArray, self).writeObject(obj)

    def __eq__(self, other):
        if isinstance(other, ByteArray):
            return self.getvalue() == other.getvalue()
        return self.getvalue() == other

    def __ne__(self, other):
        if isinstance(other, ByteArray):
            return self.getvalue() != other.getvalue()
        return self.getvalue() != other

    def __lt__(self, other):
        if isinstance(other, ByteArray):
            return self.getvalue() < other.getvalue()
        return self.getvalue() < other

    def __le__(self, other):
        if isinstance(other, ByteArray):
            return self.getvalue() <= other.getvalue()
        return self.getvalue() <= other

    def __gt__(self, other):
        if isinstance(other, ByteArray):
            return self.getvalue() > other.getvalue()
        return self.getvalue() > other

    def __ge__(self, other):
        if isinstance(other, ByteArray):
            return self.getvalue() >= other.getvalue()
        return self.getvalue() >= other

    def encode(self):
        buf = self.getvalue()

        if not self.compressed:
            return buf

        buf = zlib.compress(buf)
        # FIXME nick: hacked
        return buf[0] + b'\xda' + buf[2:]

    def compress(self):
        """
        Forces compression of the underlying stream.
        """
        self.compressed = True


class ClassDefinition(object):
    """
    This is an internal class used by L{Encoder}/L{Decoder} to hold details
    about transient class trait definitions.
    """

    def __init__(self, alias):
        self.alias = alias
        self.reference = None

        alias.compile()

        self.attr_len = 0

        if alias.static_attrs:
            self.attr_len = len(alias.static_attrs)

        self.encoding = ObjectEncoding.DYNAMIC

        if alias.external:
            self.encoding = ObjectEncoding.EXTERNAL
        elif not alias.dynamic:
            if alias.encodable_properties is not None:
                if len(alias.static_attrs) == len(alias.encodable_properties):
                    self.encoding = ObjectEncoding.STATIC
            else:
                self.encoding = ObjectEncoding.STATIC

    def __repr__(self):
        my_repr = (
            '<%s.ClassDefinition reference=%r encoding=%r alias=%r at 0x%x>'
        )

        return my_repr % (
            self.__class__.__module__,
            self.reference,
            self.encoding,
            self.alias,
            id(self)
        )


class Context(codec.Context):
    """
    I hold the AMF3 context for en/decoding streams.

    @ivar strings: A list of string references.
    @type strings: L{codec.ByteStringReferenceCollection}
    @ivar classes: A list of L{ClassDefinition}.
    @type classes: C{list}
    """

    def __init__(self, **kwargs):
        self.strings = codec.ByteStringReferenceCollection()
        self.classes = {}
        self.class_ref = {}

        self.class_idx = 0

        codec.Context.__init__(self, **kwargs)

    def clear(self):
        """
        Clears the context.
        """
        codec.Context.clear(self)

        self.strings.clear()
        self.classes = {}
        self.class_ref = {}

        self.class_idx = 0

    def getString(self, ref):
        """
        Gets a string based on a reference C{ref}.

        @param ref: The reference index.
        @type ref: string

        @rtype: string or C{None}
        @return: The referenced string.
        """
        return self.strings.getByReference(ref)

    def getStringReference(self, s):
        """
        Return string reference.

        @type s: string
        @param s: The referenced string.
        @return: The reference index to the string.
        @rtype: C{int} or C{None}
        """
        return self.strings.getReferenceTo(s)

    def addString(self, s):
        """
        Creates a reference to C{s}. If the reference already exists, that
        reference is returned.

        @type s: byte string
        @param s: The string to be referenced.
        @rtype: C{int}
        @return: The reference index.

        @raise TypeError: The parameter C{s} is not a byte string.
        """
        if not isinstance(s, bytes):
            raise TypeError

        if len(s) == 0:
            return -1

        return self.strings.append(s)

    def getClassByReference(self, ref):
        """
        Return class reference.

        @return: Class reference.
        """
        return self.class_ref.get(ref)

    def getClass(self, klass):
        """
        Returns a class reference.

        @return: Class reference.
        """
        return self.classes.get(klass)

    def addClass(self, alias, klass):
        """
        Creates a reference to C{class_def}.

        @param alias: C{ClassDefinition} instance.
        @type alias: C{ClassDefinition}
        """
        ref = self.class_idx

        self.class_ref[ref] = alias
        cd = self.classes[klass] = alias

        cd.reference = ref

        self.class_idx += 1

        return ref


class Decoder(codec.Decoder):
    """
    Decodes an AMF3 data stream.
    """

    def buildContext(self, **kwargs):
        return Context(**kwargs)

    def getTypeFunc(self, data):
        if data == TYPE_UNDEFINED:
            return self.readUndefined
        if data == TYPE_NULL:
            return self.readNull
        if data == TYPE_BOOL_FALSE:
            return self.readBoolFalse
        if data == TYPE_BOOL_TRUE:
            return self.readBoolTrue
        if data == TYPE_INTEGER:
            return self.readInteger
        if data == TYPE_NUMBER:
            return self.readNumber
        if data == TYPE_STRING:
            return self.readString
        if data == TYPE_XML:
            return self.readXML
        if data == TYPE_DATE:
            return self.readDate
        if data == TYPE_ARRAY:
            return self.readArray
        if data == TYPE_OBJECT:
            return self.readObject
        if data == TYPE_XMLSTRING:
            return self.readXMLString
        if data == TYPE_BYTEARRAY:
            return self.readByteArray

    def readUndefined(self):
        """
        Read undefined.
        """
        return miniamf.Undefined

    def readNull(self):
        """
        Read null.

        @return: C{None}
        @rtype: C{None}
        """
        return None

    def readBoolFalse(self):
        """
        Returns C{False}.

        @return: C{False}
        @rtype: C{bool}
        """
        return False

    def readBoolTrue(self):
        """
        Returns C{True}.

        @return: C{True}
        @rtype: C{bool}
        """
        return True

    def readNumber(self):
        """
        Read number.
        """
        return self.stream.read_double()

    def readInteger(self, signed=True):
        """
        Reads and returns an integer from the stream.

        @type signed: C{bool}
        @see: U{Parsing integers on OSFlash
        <http://osflash.org/amf3/parsing_integers>} for the AMF3 integer data
        format.
        """
        return decode_int(self.stream, signed)

    def _readLength(self):
        x = decode_int(self.stream, False)

        return (x >> 1, x & REFERENCE_BIT == 0)

    def readBytes(self):
        """
        Reads and returns a utf-8 encoded byte array.
        """
        length, is_reference = self._readLength()

        if is_reference:
            return self.context.getString(length)

        if length == 0:
            return b''

        result = self.stream.read(length)
        self.context.addString(result)

        return result

    def readString(self):
        """
        Reads and returns a string from the stream.
        """
        length, is_reference = self._readLength()

        if is_reference:
            result = self.context.getString(length)

            return self.context.getStringForBytes(result)

        if length == 0:
            return ''

        result = self.stream.read(length)
        self.context.addString(result)

        return self.context.getStringForBytes(result)

    def readDate(self):
        """
        Read date from the stream.

        The timezone is ignored as the date is always in UTC.
        """
        ref = self.readInteger(False)

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ms = self.stream.read_double()
        result = util.get_datetime(ms / 1000.0)

        if self.timezone_offset is not None:
            result += self.timezone_offset

        self.context.addObject(result)

        return result

    def readArray(self):
        """
        Reads an array from the stream.

        @warning: There is a very specific problem with AMF3 where the first
        three bytes of an encoded empty C{dict} will mirror that of an encoded
        C{{'': 1, '2': 2}}
        """
        size = self.readInteger(False)

        if size & REFERENCE_BIT == 0:
            return self.context.getObject(size >> 1)

        size >>= 1

        key = self.readString()

        if key == '':
            # integer indexes only -> python list
            result = [self.readElement() for i in range(size)]

            self.context.addObject(result)

            return result

        result = miniamf.MixedArray()
        self.context.addObject(result)

        while key:
            result[key] = self.readElement()
            key = self.readString()

        for i in range(size):
            result[i] = self.readElement()

        return result

    def _getClassDefinition(self, ref):
        """
        Reads class definition from the stream.
        """
        is_ref = ref & REFERENCE_BIT == 0
        ref >>= 1

        if is_ref:
            return self.context.getClassByReference(ref)

        name = self.readString()
        alias = None

        if name == '':
            name = miniamf.ASObject

        try:
            alias = miniamf.get_class_alias(name)
        except miniamf.UnknownClassAlias:
            if self.strict:
                raise

            alias = miniamf.TypedObjectClassAlias(name)

        class_def = ClassDefinition(alias)

        class_def.encoding = ref & 0x03
        class_def.attr_len = ref >> 2
        class_def.static_properties = []

        if class_def.attr_len > 0:
            for i in range(class_def.attr_len):
                key = self.readString()
                class_def.static_properties.append(key)

        self.context.addClass(class_def, alias.klass)

        return class_def

    def _readStatic(self, class_def, obj):
        for attr in class_def.static_properties:
            obj[attr] = self.readElement()

    def _readDynamic(self, class_def, obj):
        attr = self.readString()

        while attr:
            obj[attr] = self.readElement()
            attr = self.readString()

    def readObject(self):
        """
        Reads an object from the stream.

        @raise ReferenceError: Unknown reference found.
        @raise DecodeError: Unknown object encoding detected.
        """
        ref = self.readInteger(False)

        if ref & REFERENCE_BIT == 0:
            obj = self.context.getObject(ref >> 1)

            if obj is None:
                raise miniamf.ReferenceError(
                    'Unknown reference %d' % (ref >> 1,)
                )

            return obj

        ref >>= 1

        class_def = self._getClassDefinition(ref)
        alias = class_def.alias

        obj = alias.createInstance(codec=self)
        obj_attrs = dict()

        self.context.addObject(obj)

        if class_def.encoding == ObjectEncoding.EXTERNAL:
            obj.__readamf__(DataInput(self))
            return obj
        elif class_def.encoding == ObjectEncoding.DYNAMIC:
            self._readStatic(class_def, obj_attrs)
            self._readDynamic(class_def, obj_attrs)
        elif class_def.encoding == ObjectEncoding.STATIC:
            self._readStatic(class_def, obj_attrs)
        else:
            raise miniamf.DecodeError("Unknown object encoding")

        alias.applyAttributes(obj, obj_attrs, codec=self)

        return obj

    def readXML(self):
        """
        Reads an xml object from the stream.

        @return: An etree interface compatible object
        @see: L{xml.set_default_interface}
        """
        ref = self.readInteger(False)

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        x = xml.fromstring(
            self.stream.read(ref >> 1),
            forbid_dtd=self.context.forbid_dtd,
            forbid_entities=self.context.forbid_entities,
        )
        self.context.addObject(x)

        return x

    def readXMLString(self):
        """
        Reads a string from the data stream and converts it into
        an XML Tree.

        @see: L{readXML}
        """
        return self.readXML()

    def readByteArray(self):
        """
        Reads a string of data from the stream.

        Detects if the L{ByteArray} was compressed using C{zlib}.

        @see: L{ByteArray}
        @note: This is not supported in ActionScript 1.0 and 2.0.
        """
        ref = self.readInteger(False)

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        buffer = self.stream.read(ref >> 1)
        compressed = False

        if buffer[0:2] == ByteArray._zlib_header:
            try:
                buffer = zlib.decompress(buffer)
                compressed = True
            except zlib.error:
                pass

        obj = ByteArray(buffer)
        obj.compressed = compressed

        self.context.addObject(obj)

        return obj


class Encoder(codec.Encoder):
    """
    Encodes an AMF3 data stream.
    """

    def __init__(self, *args, **kwargs):
        self.string_references = kwargs.pop('string_references', True)

        codec.Encoder.__init__(self, *args, **kwargs)

    def buildContext(self, **kwargs):
        return Context(**kwargs)

    def getTypeFunc(self, data):
        """
        @see: L{codec.Encoder.getTypeFunc}
        """
        t = type(data)

        if t is int:
            return self.writeInteger
        if t is ByteArray:
            return self.writeByteArray
        if t is miniamf.MixedArray:
            return self.writeDict

        return codec.Encoder.getTypeFunc(self, data)

    def writeUndefined(self, n):
        """
        Writes an C{miniamf.Undefined} value to the stream.
        """
        self.stream.write(TYPE_UNDEFINED)

    def writeNull(self, n):
        """
        Writes a C{null} value to the stream.
        """
        self.stream.write(TYPE_NULL)

    def writeBoolean(self, n):
        """
        Writes a Boolean to the stream.
        """
        t = TYPE_BOOL_FALSE if n is False else TYPE_BOOL_TRUE

        self.stream.write(t)

    def _writeInteger(self, n):
        """
        AMF3 integers are encoded.

        @param n: The integer data to be encoded to the AMF3 data stream.
        @type n: integer data

        @see: U{Parsing Integers on OSFlash
        <http://osflash.org/documentation/amf3/parsing_integers>}
        for more info.
        """
        self.stream.write(encode_int(n))

    def writeInteger(self, n):
        """
        Writes an integer to the stream.

        @type   n: integer data
        @param  n: The integer data to be encoded to the AMF3 data stream.
        """
        if n < MIN_29B_INT or n > MAX_29B_INT:
            self.writeNumber(float(n))

            return

        self.stream.write(TYPE_INTEGER)
        self.stream.write(encode_int(n))

    def writeNumber(self, n):
        """
        Writes a float to the stream.

        @type n: C{float}
        """
        self.stream.write(TYPE_NUMBER)
        self.stream.write_double(n)

    def serialiseBytes(self, b):
        if len(b) == 0:
            self.stream.write_uchar(REFERENCE_BIT)

            return

        if self.string_references:
            ref = self.context.getStringReference(b)

            if ref != -1:
                self._writeInteger(ref << 1)

                return

            self.context.addString(b)

        self._writeInteger((len(b) << 1) | REFERENCE_BIT)
        self.stream.write(b)

    def serialiseString(self, s):
        """
        Writes a raw string to the stream.

        @type   s: string
        @param  s: The string data to be encoded to the AMF3 data stream.
        """
        if not isinstance(s, bytes):
            s = self.context.getBytesForString(s)

        self.serialiseBytes(s)

    def writeBytes(self, b):
        """
        Writes a raw string to the stream.
        """
        self.stream.write(TYPE_STRING)

        self.serialiseBytes(b)

    def writeString(self, s):
        """
        Writes a string to the stream. It will be B{UTF-8} encoded.
        """
        s = self.context.getBytesForString(s)

        self.writeBytes(s)

    def writeDate(self, n):
        """
        Writes a C{datetime} instance to the stream.

        Does not support C{datetime.time} instances because AMF3 has
        no way to encode time objects, so please use C{datetime.datetime}
        instead.

        @type n: L{datetime}
        @param n: The C{Date} data to be encoded to the AMF3 data stream.
        @raise EncodeError: A datetime.time instance was found
        """
        if isinstance(n, datetime.time):
            raise miniamf.EncodeError(
                'A datetime.time instance was found but AMF3 has no way to '
                'encode time objects. Please use datetime.datetime instead '
                '(got:%r)' % (n,)
            )

        self.stream.write(TYPE_DATE)

        ref = self.context.getObjectReference(n)

        if ref != -1:
            self._writeInteger(ref << 1)

            return

        self.context.addObject(n)

        self.stream.write_uchar(REFERENCE_BIT)

        if self.timezone_offset is not None:
            n -= self.timezone_offset

        ms = util.get_timestamp(n)
        self.stream.write_double(ms * 1000.0)

    def writeList(self, n):
        """
        Writes a C{tuple}, C{set} or C{list} to the stream.

        @type n: One of C{__builtin__.tuple}, C{__builtin__.set}
            or C{__builtin__.list}
        @param n: The C{list} data to be encoded to the AMF3 data stream.
        """

        self.stream.write(TYPE_ARRAY)

        ref = self.context.getObjectReference(n)

        if ref != -1:
            self._writeInteger(ref << 1)

            return

        self.context.addObject(n)

        self._writeInteger((len(n) << 1) | REFERENCE_BIT)
        self.stream.write(b'\x01')

        [self.writeElement(x) for x in n]

    def writeDict(self, n):
        """
        Writes a C{dict} to the stream.

        @type n: C{__builtin__.dict}
        @param n: The C{dict} data to be encoded to the AMF3 data stream.
        @raise ValueError: Non int/string key value found in the C{dict}
        @raise EncodeError: C{dict} contains empty string keys.
        """
        # Design bug in AMF3 that cannot read/write empty key strings
        # for more info
        if '' in n:
            raise miniamf.EncodeError("dicts cannot contain empty string keys")

        self.stream.write(TYPE_ARRAY)

        ref = self.context.getObjectReference(n)

        if ref != -1:
            self._writeInteger(ref << 1)

            return

        self.context.addObject(n)

        # The AMF3 spec demands that all string indices be listed first
        int_keys = []
        str_keys = []

        for x in n.keys():
            if isinstance(x, int):
                int_keys.append(x)
            elif isinstance(x, str):
                str_keys.append(x)
            else:
                raise ValueError("Non integer/string key value found in dict")

        # Make sure the integer keys are within range
        l = len(int_keys)

        for x in int_keys:
            if l < x <= 0:
                # treat as a string key
                str_keys.append(x)
                del int_keys[int_keys.index(x)]

        int_keys.sort()

        # If integer keys don't start at 0, they will be treated as strings
        if len(int_keys) > 0 and int_keys[0] != 0:
            for x in int_keys:
                str_keys.append(str(x))
                del int_keys[int_keys.index(x)]

        self._writeInteger(len(int_keys) << 1 | REFERENCE_BIT)

        str_keys.sort()

        for x in str_keys:
            self.serialiseString(x)
            self.writeElement(n[x])

        self.stream.write_uchar(0x01)

        for k in int_keys:
            self.writeElement(n[k])

    def writeObject(self, obj):
        """
        Writes an object to the stream.
        """

        self.stream.write(TYPE_OBJECT)

        ref = self.context.getObjectReference(obj)

        if ref != -1:
            self._writeInteger(ref << 1)

            return

        self.context.addObject(obj)

        # object is not referenced, serialise it
        kls = obj.__class__
        definition = self.context.getClass(kls)
        alias = None
        class_ref = False  # if the class definition is a reference

        if definition:
            class_ref = True
            alias = definition.alias
        else:
            alias = self.context.getClassAlias(kls)
            definition = ClassDefinition(alias)

            self.context.addClass(definition, alias.klass)

        if class_ref:
            self.stream.write(definition.reference)
        else:
            ref = 0

            if definition.encoding != ObjectEncoding.EXTERNAL:
                ref += definition.attr_len << 4

            final_reference = encode_int(
                ref |
                definition.encoding << 2 |
                REFERENCE_BIT << 1 |
                REFERENCE_BIT
            )

            self.stream.write(final_reference)

            definition.reference = encode_int(
                definition.reference << 2 | REFERENCE_BIT)

            if alias.anonymous:
                self.stream.write(b'\x01')
            else:
                self.serialiseString(alias.alias)

            # work out what the final reference for the class will be.
            # this is okay because the next time an object of the same
            # class is encoded, class_ref will be True and never get here
            # again.

        if alias.external:
            obj.__writeamf__(DataOutput(self))

            return

        attrs = alias.getEncodableAttributes(obj, codec=self)

        if alias.static_attrs:
            sattrs = sorted(alias.static_attrs)
            if not class_ref:
                for attr in sattrs:
                    self.serialiseString(attr)

            for attr in sattrs:
                value = attrs.pop(attr)

                self.writeElement(value)

            if definition.encoding == ObjectEncoding.STATIC:
                return

        if definition.encoding == ObjectEncoding.DYNAMIC:
            if attrs:
                try:
                    keys = sorted(attrs)
                except TypeError:
                    raise miniamf.EncodeError(
                        'Unable to encode %r (unsortable attrs: %r)'
                        % (obj, attrs))

                for key in keys:
                    value = attrs[key]
                    if isinstance(key, int):
                        key = str(key)
                    elif not isinstance(key, str):
                        raise miniamf.EncodeError(
                            'Unable to encode %r (key %r not supported)'
                            % (obj, key))

                    self.serialiseString(key)
                    self.writeElement(value)

            self.stream.write(b'\x01')

    def writeByteArray(self, n):
        """
        Writes a L{ByteArray} to the data stream.

        @param n: The L{ByteArray} data to be encoded to the AMF3 data stream.
        @type n: L{ByteArray}
        """
        self.stream.write(TYPE_BYTEARRAY)

        ref = self.context.getObjectReference(n)

        if ref != -1:
            self._writeInteger(ref << 1)

            return

        self.context.addObject(n)

        buf = n.encode()
        self._writeInteger(len(buf) << 1 | REFERENCE_BIT)
        self.stream.write(buf)

    def writeXML(self, n):
        """
        Writes a XML string to the data stream.

        @type   n: L{ET<xml.ET>}
        @param  n: The XML Document to be encoded to the AMF3 data stream.
        """
        self.stream.write(TYPE_XMLSTRING)
        ref = self.context.getObjectReference(n)

        if ref != -1:
            self._writeInteger(ref << 1)

            return

        self.context.addObject(n)

        self.serialiseString(xml.tostring(n))


def encode_int(n):
    """
    Encodes an int as a variable length signed 29-bit integer as defined by
    the spec.

    @param n: The integer to be encoded
    @return: The encoded string
    @raise OverflowError: C{c} is out of range.
    """
    try:
        return ENCODED_INT_CACHE[n]
    except KeyError:
        pass

    if n < MIN_29B_INT or n > MAX_29B_INT:
        raise OverflowError("Out of range")

    if n < 0:
        n += 0x20000000

    encoded = bytearray()
    real_value = None

    if n > 0x1fffff:
        real_value = n
        n >>= 1
        encoded.append(0x80 | ((n >> 21) & 0xff))

    if n > 0x3fff:
        encoded.append(0x80 | ((n >> 14) & 0xff))

    if n > 0x7f:
        encoded.append(0x80 | ((n >> 7) & 0xff))

    if real_value is not None:
        n = real_value

    if n > 0x1fffff:
        encoded.append(n & 0xff)
    else:
        encoded.append(n & 0x7f)

    encoded = bytes(encoded)
    ENCODED_INT_CACHE.__setitem__(n, encoded)
    return encoded


def decode_int(stream, signed=False):
    """
    Decode C{int}.
    """
    n = result = 0
    b = stream.read_uchar()

    while b & 0x80 != 0 and n < 3:
        result <<= 7
        result |= b & 0x7f
        b = stream.read_uchar()
        n += 1

    if n < 3:
        result <<= 7
        result |= b
    else:
        result <<= 8
        result |= b

        if result & 0x10000000 != 0:
            if signed:
                result -= 0x20000000
            else:
                result <<= 1
                result += 1

    return result


miniamf.register_class(ByteArray)
