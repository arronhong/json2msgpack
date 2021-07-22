import io

import pytest

from main import (
    pack_int,
    pack_float,
    pack_str_header,
    pack_array_header,
    pack_map_header,
    json_to_msgpack,
    is_positive_fixint,
    is_fixstr,
    is_fixarray,
    is_fixmap,
    is_negative_fixint,
    msgpack_to_json
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
    ('{"compact":true,"schema":0}',
     b'\x82\xa7compact\xc3\xa6schema\x00'),
    ('[{"a":false, "b": 71264123, "c": [], "d": {}, "e": ""}, {}, [], null, true]',
     b'\x95\x85\xa1a\xc2\xa1b\xce\x04?g{\xa1c\x90\xa1d\x80\xa1e\xa0\x80\x90\xc0\xc3'),
    ('{"int":1,"float":0.5,"boolean":true,"null":null,"string":"foo bar","array":["foo","bar",-66666,-123.4567,[],{}],"object":{"foo":1,"baz":0.5,"bar":{"foo bar":[]}}}',
     b'\x87\xA3\x69\x6E\x74\x01\xA5\x66\x6C\x6F\x61\x74\xCB\x3F\xE0\x00\x00\x00\x00\x00\x00\xA7\x62\x6F\x6F\x6C\x65\x61\x6E\xC3\xA4\x6E\x75\x6C\x6C\xC0\xA6\x73\x74\x72\x69\x6E\x67\xA7\x66\x6F\x6F\x20\x62\x61\x72\xA5\x61\x72\x72\x61\x79\x96\xA3\x66\x6F\x6F\xA3\x62\x61\x72\xD2\xFF\xFE\xFB\x96\xCB\xC0\x5E\xDD\x3A\x92\xA3\x05\x53\x90\x80\xA6\x6F\x62\x6A\x65\x63\x74\x83\xA3\x66\x6F\x6F\x01\xA3\x62\x61\x7A\xCB\x3F\xE0\x00\x00\x00\x00\x00\x00\xA3\x62\x61\x72\x81\xA7\x66\x6F\x6F\x20\x62\x61\x72\x90'),
])
def test_json_to_msgpack(input, expected):
    assert expected == json_to_msgpack(input)


@pytest.mark.parametrize('input,expected', [
    (b'\x7f', True),
    (b'\xff', False)
])
def test_is_positive_fixint(input, expected):
    assert expected == is_positive_fixint(input)


@pytest.mark.parametrize('input,expected', [
    (b'\xE0', True),
    (b'\xDF', False)
])
def test_is_negative_fixint(input, expected):
    assert expected == is_negative_fixint(input)


@pytest.mark.parametrize('input,expected', [
    (b'\x8F', True),
    (b'\x90', False)
])
def test_is_fixmap(input, expected):
    assert expected == is_fixmap(input)


@pytest.mark.parametrize('input,expected', [
    (b'\x9F', True),
    (b'\xA0', False)
])
def test_is_fixarray(input, expected):
    assert expected == is_fixarray(input)


@pytest.mark.parametrize('input,expected', [
    (b'\xA0', True),
    (b'\xCF', False)
])
def test_is_fixstr(input, expected):
    assert expected == is_fixstr(input)


@pytest.mark.parametrize('expected,input', [
    ('{"compact":true,"schema":0}',
     b'\x82\xa7compact\xc3\xa6schema\x00'),
    ('[{"a":false,"b":71264123,"c":[],"d":{},"e":""},{},[],null,true]',
     b'\x95\x85\xa1a\xc2\xa1b\xce\x04?g{\xa1c\x90\xa1d\x80\xa1e\xa0\x80\x90\xc0\xc3'),
    ('{"int":1,"float":0.5,"boolean":true,"null":null,"string":"foo bar","array":["foo","bar",-66666,-123.4567,[],{}],"object":{"foo":1,"baz":0.5,"bar":{"foo bar":[]}}}',
     b'\x87\xA3\x69\x6E\x74\x01\xA5\x66\x6C\x6F\x61\x74\xCB\x3F\xE0\x00\x00\x00\x00\x00\x00\xA7\x62\x6F\x6F\x6C\x65\x61\x6E\xC3\xA4\x6E\x75\x6C\x6C\xC0\xA6\x73\x74\x72\x69\x6E\x67\xA7\x66\x6F\x6F\x20\x62\x61\x72\xA5\x61\x72\x72\x61\x79\x96\xA3\x66\x6F\x6F\xA3\x62\x61\x72\xD2\xFF\xFE\xFB\x96\xCB\xC0\x5E\xDD\x3A\x92\xA3\x05\x53\x90\x80\xA6\x6F\x62\x6A\x65\x63\x74\x83\xA3\x66\x6F\x6F\x01\xA3\x62\x61\x7A\xCB\x3F\xE0\x00\x00\x00\x00\x00\x00\xA3\x62\x61\x72\x81\xA7\x66\x6F\x6F\x20\x62\x61\x72\x90'),
])
def test_msgpack_to_json(input, expected):
    stream = io.BytesIO(input)
    assert expected == msgpack_to_json(stream)


@pytest.mark.parametrize('input',[
    b'\x91\xc4\x00'
])
def test_msgpack_to_json_with_incompatible_type(input):
    stream = io.BytesIO(input)
    with pytest.raises(ValueError):
        msgpack_to_json(stream)
