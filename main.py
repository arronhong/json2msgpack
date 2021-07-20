import json
import struct
import math
import argparse
import sys
import io
from typing import Generator
from textwrap import wrap


MIN_POSITIVE_FIXINT_FIRST_BYTE = b'\x00'
MIN_FIXMAP_FIRST_BYTE = b'\x80'
MIN_FIXARRAY_FIRST_BYTE = b'\x90'
MIN_FIXSTR_FIRST_BYTE = b'\xA0'
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


def pack_nil() -> bytes:
    return NIL_FIRST_BYTE


def pack_bool(b: bool) -> bytes:
    return TRUE_FIRST_BYTE if b else FALSE_FIRST_BYTE


def pack_int(i: int) -> bytes:
    if 0 <= i <= 0x7F:
        return struct.pack(
            "B", int.from_bytes(MIN_POSITIVE_FIXINT_FIRST_BYTE, 'big') | i)
    elif 0x80 <= i <= 0xFF:
        return struct.pack(">cB", UINT8_FIRST_BYTE, i)
    elif 0xFF < i <= 0xFFFF:
        return struct.pack(">cH", UINT16_FIRST_BYTE, i)
    elif 0xFFFF < i <= 0xFFFFFFFF:
        return struct.pack(">cI", UINT32_FIRST_BYTE, i)
    elif 0xFFFFFFFF < i <= 0xFFFFFFFFFFFFFFFF:
        return struct.pack(">cQ", UINT64_FIRST_BYTE, i)
    elif -0x20 <= i < 0:
        return struct.pack(
            'b', int.from_bytes(MIN_NEGATIVE_FIXINT_FIRST_BYTE, 'big') | i)
    elif -0x80 <= i < -0x20:
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
    if strlen <= 0x1F:
        return struct.pack(
            'B', int.from_bytes(MIN_FIXSTR_FIRST_BYTE, 'big') | strlen)
    elif 0x1F < strlen <= 0xFF:
        return struct.pack('>cB', STR8_FIRST_BYTE, strlen)
    elif 0xFF < strlen <= 0xFFFF:
        return struct.pack('>cH', STR16_FIRST_BYTE, strlen)
    elif 0xFFFF < strlen <= 0xFFFFFFFF:
        return struct.pack('>cI', STR32_FIRST_BYTE, strlen)

    raise ValueError('maximum byte size of a String object is (2^32)-1')


def pack_array_header(arrlen: int) -> bytes:
    if arrlen <= 0x0F:
        return struct.pack(
            'B', int.from_bytes(MIN_FIXARRAY_FIRST_BYTE, 'big') | arrlen)
    elif 0xFF < arrlen <= 0xFFFF:
        return struct.pack('>cH', ARRAY16_FIRST_BYTE, arrlen)
    elif 0xFFFF < arrlen <= 0xFFFFFFFF:
        return struct.pack('>cI', ARRAY32_FIRST_BYTE, arrlen)

    raise ValueError(
        'maximum number of elements of an Array object is (2^32)-1')


def pack_map_header(maplen: int) -> bytes:
    if maplen <= 0x0F:
        return struct.pack(
            'B', int.from_bytes(MIN_FIXMAP_FIRST_BYTE, 'big') | maplen)
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
    obj = json.loads(j)
    return b''.join(_pack_obj(obj))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='JSON Messagepack Convert')
    parser.add_argument('--output', '-o',
                        type=argparse.FileType(mode='bw',
                                               bufsize=io.DEFAULT_BUFFER_SIZE),
                        nargs='?',
                        default=sys.stdout,
                        help='Write to FILE instead of stdout')
    parser.add_argument('input',
                        type=argparse.FileType(mode='r',
                                               bufsize=io.DEFAULT_BUFFER_SIZE),
                        nargs='?',
                        default=sys.stdin,
                        help='If file is a single dash `-` or absent, reads from the stdin')
    args = parser.parse_args()

    if args.input is sys.stdin:
        json_str = args.input.readline()
    else:
        json_str = args.input.read()

    if len(json_str) <= io.DEFAULT_BUFFER_SIZE:
        packed_result = json_to_msgpack(json_str)
        if args.output is sys.stdout:
            args.output.write(' '.join(wrap(packed_result.hex(), 2)))
        else:
            args.output.write(packed_result)
    else:
        for packed_obj in _pack_obj(json.loads(json_str)):
            if args.output is sys.stdout:
                args.output.write(' '.join(wrap(packed_obj.hex(), 2)) + ' ')
            else:
                args.output.write(packed_obj)

    args.input.close()
    args.output.close()
