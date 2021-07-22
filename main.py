import json
import struct
import math
import sys
import io
from typing import Generator
from functools import partial


MIN_POSITIVE_FIXINT_FIRST_BYTE = b'\x00'
MAX_POSITIVE_FIXINT_FIRST_BYTE = b'\x7F'
MIN_FIXMAP_FIRST_BYTE = b'\x80'
MAX_FIXMAP_FIRST_BYTE = b'\x8F'
MIN_FIXARRAY_FIRST_BYTE = b'\x90'
MAX_FIXARRAY_FIRST_BYTE = b'\x9F'
MIN_FIXSTR_FIRST_BYTE = b'\xA0'
MAX_FIXSTR_FIRST_BYTE = b'\xBF'
NIL_FIRST_BYTE = b'\xC0'
FALSE_FIRST_BYTE = b'\xC2'
TRUE_FIRST_BYTE = b'\xC3'
UINT8_FIRST_BYTE = b'\xCC'
UINT16_FIRST_BYTE = b'\xCD'
UINT32_FIRST_BYTE = b'\xCE'
UINT64_FIRST_BYTE = b'\xCF'
INT8_FIRST_BYTE = b'\xD0'
INT16_FIRST_BYTE = b'\xD1'
INT32_FIRST_BYTE = b'\xD2'
INT64_FIRST_BYTE = b'\xD3'
FLOAT32_FIRST_BYTE = b'\xCA'
FLOAT64_FIRST_BYTE = b'\xCB'
STR8_FIRST_BYTE = b'\xD9'
STR16_FIRST_BYTE = b'\xDA'
STR32_FIRST_BYTE = b'\xDB'
ARRAY16_FIRST_BYTE = b'\xDC'
ARRAY32_FIRST_BYTE = b'\xDD'
MAP16_FIRST_BYTE = b'\xDE'
MAP32_FIRST_BYTE = b'\xDF'
MIN_NEGATIVE_FIXINT_FIRST_BYTE = b'\xE0'
MAX_NEGATIVE_FIXINT_FIRST_BYTE = b'\xFF'


def _is_byte_in_range(b: bytes, low: bytes, high: bytes) -> bool:
    if (0xFF - (high[0] - low[0])) & b[0] == low[0]:
        return True
    return False


is_positive_fixint = partial(_is_byte_in_range,
                             low=MIN_POSITIVE_FIXINT_FIRST_BYTE,
                             high=MAX_POSITIVE_FIXINT_FIRST_BYTE)
is_negative_fixint = partial(_is_byte_in_range,
                             low=MIN_NEGATIVE_FIXINT_FIRST_BYTE,
                             high=MAX_NEGATIVE_FIXINT_FIRST_BYTE)
is_fixmap = partial(_is_byte_in_range,
                    low=MIN_FIXMAP_FIRST_BYTE,
                    high=MAX_FIXMAP_FIRST_BYTE)
is_fixarray = partial(_is_byte_in_range,
                    low=MIN_FIXARRAY_FIRST_BYTE,
                    high=MAX_FIXARRAY_FIRST_BYTE)
is_fixstr = partial(_is_byte_in_range,
                    low=MIN_FIXSTR_FIRST_BYTE,
                    high=MAX_FIXSTR_FIRST_BYTE)


def pack_nil() -> bytes:
    return NIL_FIRST_BYTE


def pack_bool(b: bool) -> bytes:
    return TRUE_FIRST_BYTE if b else FALSE_FIRST_BYTE


def pack_int(i: int) -> bytes:
    if 0 <= i <= MAX_POSITIVE_FIXINT_FIRST_BYTE[0]:
        return struct.pack("B", i)
    elif MAX_POSITIVE_FIXINT_FIRST_BYTE[0] < i <= 0xFF:
        return struct.pack(">cB", UINT8_FIRST_BYTE, i)
    elif 0xFF < i <= 0xFFFF:
        return struct.pack(">cH", UINT16_FIRST_BYTE, i)
    elif 0xFFFF < i <= 0xFFFFFFFF:
        return struct.pack(">cI", UINT32_FIRST_BYTE, i)
    elif 0xFFFFFFFF < i <= 0xFFFFFFFFFFFFFFFF:
        return struct.pack(">cQ", UINT64_FIRST_BYTE, i)
    elif struct.unpack('b', MIN_NEGATIVE_FIXINT_FIRST_BYTE)[0] <= i < 0:
        return struct.pack('b', i)
    elif -0x80 <= i < struct.unpack('b', MIN_NEGATIVE_FIXINT_FIRST_BYTE)[0]:
        return struct.pack(">cb", INT8_FIRST_BYTE, i)
    elif -0x8000 <= i < -0x80:
        return struct.pack(">ch", INT16_FIRST_BYTE, i)
    elif -0x80000000 <= i < -0x8000:
        return struct.pack(">ci", INT32_FIRST_BYTE, i)
    elif -0x8000000000000000 <= i < -0x80000000:
        return struct.pack(">cq", INT64_FIRST_BYTE, i)

    raise ValueError(
        'a value of an Integer object is limited from -(2^63) upto (2^64)-1')


def pack_float(f: float, single_precision=False):
    if not math.isfinite(f):
        raise NotImplementedError('NaN, Inf, -Inf are not specific in spec')
    if single_precision:
        return struct.pack(">cf", FLOAT32_FIRST_BYTE, f)
    return struct.pack(">cd", FLOAT64_FIRST_BYTE, f)


def pack_str_header(strlen: int) -> bytes:
    if strlen <= MAX_FIXSTR_FIRST_BYTE[0] - MIN_FIXSTR_FIRST_BYTE[0]:
        return struct.pack('B', MIN_FIXSTR_FIRST_BYTE[0] + strlen)
    elif 0x1F < strlen <= 0xFF:
        return struct.pack('>cB', STR8_FIRST_BYTE, strlen)
    elif 0xFF < strlen <= 0xFFFF:
        return struct.pack('>cH', STR16_FIRST_BYTE, strlen)
    elif 0xFFFF < strlen <= 0xFFFFFFFF:
        return struct.pack('>cI', STR32_FIRST_BYTE, strlen)

    raise ValueError('maximum byte size of a String object is (2^32)-1')


def pack_array_header(arrlen: int) -> bytes:
    if arrlen <= MAX_FIXARRAY_FIRST_BYTE[0] - MIN_FIXARRAY_FIRST_BYTE[0]:
        return struct.pack('B', MIN_FIXARRAY_FIRST_BYTE[0] + arrlen)
    elif 0xFF < arrlen <= 0xFFFF:
        return struct.pack('>cH', ARRAY16_FIRST_BYTE, arrlen)
    elif 0xFFFF < arrlen <= 0xFFFFFFFF:
        return struct.pack('>cI', ARRAY32_FIRST_BYTE, arrlen)

    raise ValueError(
        'maximum number of elements of an Array object is (2^32)-1')


def pack_map_header(maplen: int) -> bytes:
    if maplen <= MAX_FIXMAP_FIRST_BYTE[0] - MIN_FIXMAP_FIRST_BYTE[0]:
        return struct.pack('B', MIN_FIXMAP_FIRST_BYTE[0] + maplen)
    elif 0xFF < maplen <= 0xFFFF:
        return struct.pack('>cH', MAP16_FIRST_BYTE, maplen)
    elif 0xFFFF < maplen <= 0xFFFFFFFF:
        return struct.pack('>cI', MAP32_FIRST_BYTE, maplen)

    raise ValueError(
        'maximum number of key-value associations of a Map object is (2^32)-1')


def _pack_obj(obj) -> Generator[bytes, None, None]:
    if obj is None:
        yield pack_nil()
    elif isinstance(obj, bool):
        yield pack_bool(obj)
    elif isinstance(obj, int):
        yield pack_int(obj)
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError('NaN, Inf, -Inf are not allowed on JSON')
        yield pack_float(obj)
    elif isinstance(obj, str):
        yield pack_str_header(len(obj))
        yield obj.encode('utf-8')
    elif isinstance(obj, list):
        yield pack_array_header(len(obj))
        for o in obj:
            yield from _pack_obj(o)
    elif isinstance(obj, dict):
        yield pack_map_header(len(obj))
        for k, v in obj.items():
            if not isinstance(k, str):
                raise ValueError('only str key of map is allowed on JSON')
            yield from _pack_obj(k)
            yield from _pack_obj(v)
    else:
        raise ValueError('not supported type on JSON')


def json_to_msgpack(j: str) -> bytes:
    # TODO: enhancement for large json
    obj = json.loads(j)
    return b''.join(_pack_obj(obj))


def _unpack_to_json(stream: io.BufferedIOBase, buffer_can_be_empty=True
                    ) -> Generator[str, None, None]:
    if (b := stream.read(1)) == b'':
        # eof
        if buffer_can_be_empty:
            return
        else:
            raise ValueError('buffer shortage')

    def read_with_check(wanted):
        avail = stream.read(wanted)
        if len(avail) != wanted:
            raise ValueError('buffer shortage')
        return avail

    def is_serialized_json_str(s: str):
        return len(s) >= 2 and s.startswith('"') and s.endswith('"')

    def unpack_array(datalen):
        yield '['
        for i in range(datalen):
            yield from _unpack_to_json(stream, buffer_can_be_empty=False)
            if i < datalen - 1:
                yield ','
        yield ']'

    def unpack_map(datalen):
        yield '{'
        for i in range(datalen*2):
            if i & 1 == 0:
                key_gen = _unpack_to_json(stream, buffer_can_be_empty=False)
                key = next(key_gen)
                if not is_serialized_json_str(key):
                    raise ValueError('key of map in json only be string')
                yield key
                yield ':'
            else:
                yield from _unpack_to_json(stream, buffer_can_be_empty=False)
                if i < datalen * 2 - 1:
                    yield ','
        yield '}'

    if b == NIL_FIRST_BYTE:
        yield 'null'
    elif b == FALSE_FIRST_BYTE:
        yield 'false'
    elif b == TRUE_FIRST_BYTE:
        yield 'true'
    elif is_positive_fixint(b):
        yield str(b[0])
    elif b == UINT8_FIRST_BYTE:
        yield str(struct.unpack('B', read_with_check(1))[0])
    elif b == UINT16_FIRST_BYTE:
        yield str(struct.unpack('>H', read_with_check(2))[0])
    elif b == UINT32_FIRST_BYTE:
        yield str(struct.unpack('>I', read_with_check(4))[0])
    elif b == UINT64_FIRST_BYTE:
        yield str(struct.unpack('>Q', read_with_check(4))[0])
    elif is_negative_fixint(b):
        yield str(struct.unpack('b', b)[0])
    elif b == INT8_FIRST_BYTE:
        yield str(struct.unpack('b', read_with_check(1))[0])
    elif b == INT16_FIRST_BYTE:
        yield str(struct.unpack('>h', read_with_check(2))[0])
    elif b == INT32_FIRST_BYTE:
        yield str(struct.unpack('>i', read_with_check(4))[0])
    elif b == INT64_FIRST_BYTE:
        yield str(struct.unpack('>q', read_with_check(8))[0])
    elif b == FLOAT32_FIRST_BYTE:
        yield str(struct.unpack('>f', read_with_check(4))[0])
    elif b == FLOAT64_FIRST_BYTE:
        yield str(struct.unpack('>d', read_with_check(8))[0])
    elif is_fixstr(b):
        datalen = (MAX_FIXSTR_FIRST_BYTE[0] - MIN_FIXSTR_FIRST_BYTE[0]) & b[0]
        yield '"' + read_with_check(datalen).decode('utf-8') + '"'
    elif b == STR8_FIRST_BYTE:
        datalen = struct.unpack('B', read_with_check(1))[0]
        yield '"' + read_with_check(datalen).decode('utf-8') + '"'
    elif b == STR16_FIRST_BYTE:
        datalen = struct.unpack('>H', read_with_check(2))[0]
        yield '"' + read_with_check(datalen).decode('utf-8') + '"'
    elif b == STR32_FIRST_BYTE:
        datalen = struct.unpack('>I', read_with_check(4))[0]
        yield '"' + read_with_check(datalen).decode('utf-8') + '"'
    elif is_fixarray(b):
        datalen = (MAX_FIXARRAY_FIRST_BYTE[0] - MIN_FIXARRAY_FIRST_BYTE[0]
                   ) & b[0]
        yield from unpack_array(datalen)
    elif b == ARRAY16_FIRST_BYTE:
        datalen = struct.unpack('>H', read_with_check(2))[0]
        yield from unpack_array(datalen)
    elif b == ARRAY32_FIRST_BYTE:
        datalen = struct.unpack('>I', read_with_check(4))[0]
        yield from unpack_array(datalen)
    elif is_fixmap(b):
        datalen = (MAX_FIXMAP_FIRST_BYTE[0] - MIN_FIXMAP_FIRST_BYTE[0]
                   ) & b[0]
        yield from unpack_map(datalen)
    elif b == MAP16_FIRST_BYTE:
        datalen = struct.unpack('>H', read_with_check(2))[0]
        yield from unpack_map(datalen)
    elif b == MAP32_FIRST_BYTE:
        datalen = struct.unpack('>I', read_with_check(4))[0]
        yield from unpack_map(datalen)
    else:
        raise ValueError(
            'type of messagepack is not supported by json')


def msgpack_to_json(stream: io.BufferedIOBase) -> str:
    return ''.join(_unpack_to_json(stream))


def _main(input, output, unpack=False):
    if unpack:
        if input is sys.stdin:
            # format be like:
            # AB 68 65 6C 6C 6F 20 77 6F 72 6C 64
            stream = io.BytesIO(bytes.fromhex(input.readline()))
        else:
            stream = input

        for unpack_json in _unpack_to_json(stream):
            output.write(unpack_json)

    else:
        from textwrap import wrap
        if input is sys.stdin:
            json_str = input.readline()
        else:
            json_str = input.read()

        if len(json_str) <= io.DEFAULT_BUFFER_SIZE:
            # if data is relatively small, just load packed result into memory.
            packed_result = json_to_msgpack(json_str)
            if output is sys.stdout:
                output.write(' '.join(wrap(packed_result.hex(), 2)))
            else:
                output.write(packed_result)
        else:
            for packed_obj in _pack_obj(json.loads(json_str)):
                if output is sys.stdout:
                    output.write(' '.join(wrap(packed_obj.hex(), 2)) + ' ')
                else:
                    output.write(packed_obj)

    input.close()
    output.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='JSON Messagepack Convert')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--unpack', '-u',
                       action='store_true',
                       help='convert messagepack to json')
    parser.add_argument('--output', '-o',
                        nargs='?',
                        default=sys.stdout,
                        help='Write to FILE instead of stdout')
    parser.add_argument('input',
                        nargs='?',
                        default=sys.stdin,
                        help='If file is a single dash `-` or absent, reads from the stdin')
    args = parser.parse_args()
    if isinstance(args.input, str):
        if args.input == '-':
            args.input = sys.stdin
        elif args.unpack:
            args.input = open(args.input, 'rb')
        else:
            args.input = open(args.input, 'r')

    if isinstance(args.output, str):
        if args.unpack:
            args.output = open(args.output, 'w')
        else:
            args.output = open(args.output, 'wb')

    _main(args.input, args.output, args.unpack)
