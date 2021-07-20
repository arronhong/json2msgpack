import pytest

from main import (
    pack_int,
    pack_float,
    pack_str_header,
    pack_array_header,
    pack_map_header,
    json_to_msgpack
)


@pytest.mark.parametrize('input,expected', [
    (0, b'\x00'),
    (127, b'\x7F'),
    (255, b'\xCC\xFF'),
    (65535, b'\xCD\xFF\xFF'),
    (4294967295, b'\xCE\xFF\xFF\xFF\xFF'),
    (18446744073709551615, b'\xCF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'),
    (-32, b'\xE0'),
    (-128, b'\xD0\x80'),
    (-32768, b'\xD1\x80\x00'),
    (-2147483648, b'\xD2\x80\x00\x00\x00'),
    (-9223372036854775808, b'\xD3\x80\x00\x00\x00\x00\x00\x00\x00'),
])
def test_pack_int(input, expected):
    assert expected == pack_int(input)


@pytest.mark.parametrize('input,expected', [
    (1.5, b'\xCB\x3F\xF8\x00\x00\x00\x00\x00\x00'),
    (-1.5, b'\xCB\xBF\xF8\x00\x00\x00\x00\x00\x00'),
])
def test_pack_float(input, expected):
    assert expected == pack_float(input, single_precision=False)


@pytest.mark.parametrize('input,expected', [
    (0, b'\xA0'),
    (31, b'\xBF'),
    (255, b'\xD9\xFF'),
    (65535, b'\xDA\xFF\xFF'),
    (4294967295, b'\xDB\xFF\xFF\xFF\xFF'),
])
def test_pack_str_header(input, expected):
    assert expected == pack_str_header(input)


@pytest.mark.parametrize('input,expected', [
    (0, b'\x90'),
    (15, b'\x9F'),
    (65535, b'\xDC\xFF\xFF'),
    (4294967295, b'\xDD\xFF\xFF\xFF\xFF'),
])
def test_pack_array_header(input, expected):
    assert expected == pack_array_header(input)


@pytest.mark.parametrize('input,expected', [
    (0, b'\x80'),
    (15, b'\x8F'),
    (65535, b'\xDE\xFF\xFF'),
    (4294967295, b'\xDF\xFF\xFF\xFF\xFF'),
])
def test_pack_map_header(input, expected):
    assert expected == pack_map_header(input)


@pytest.mark.parametrize('input,expected', [
    ('{"compact":true,"schema":0}', b'\x82\xa7compact\xc3\xa6schema\x00'),
    ('[{"a":false, "b": 71264123, "c": [], "d": {}, "e": ""}, {}, [], null, true]', b'\x95\x85\xa1a\xc2\xa1b\xce\x04?g{\xa1c\x90\xa1d\x80\xa1e\xa0\x80\x90\xc0\xc3'),
])
def test_json_to_msgpack(input, expected):
    assert expected == json_to_msgpack(input)
