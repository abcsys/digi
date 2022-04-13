import typing
import datetime
import dateutil.parser
import durationpy
import binascii
import decimal
import ipaddress
import json

"""TBD patch upstream zed/zed.py"""

_py_to_zed_primitive_type = {
    "<class 'int'>": "int64",
    "<class 'datetime.timedelta'>": "duration",
    "<class 'datetime.datetime'>": "time",
    "<class 'float'>": "float64",
    "<class 'decimal.Decimal'>": "decimal",
    "<class 'bool'>": "bool",  # TBD check zed/zed.py 'bool' -> 'T'
    "<class 'bytes'>": "bytes",
    "<class 'str'>": "string",
    "<class 'ipaddress.IPv4Address'>": "ip",
    "<class 'ipaddress.IPv4Network'>": "net",
    "<class 'type'>": "type",
    "<class 'NoneType'>": "null",
}


class __Counter:
    def __init__(self):
        self.ctr = 29

    def get_and_inc(self):
        self.ctr += 1
        return self.ctr


def encode(objs: typing.List[dict]) -> str:
    id_ctr, types = __Counter(), dict()
    for obj in objs:
        yield json.dumps({
            "type": _encode_type(id_ctr, obj),
            "value": _encode_value(obj),
        })


def _encode_type(id_ctr, value) -> dict:
    # TBD ref type
    if isinstance(value, dict):
        return {
            "kind": "record",
            "fields": [
                {"name": _f, "type": _encode_type(id_ctr, _v)}
                for _f, _v in value.items()
            ] if len(value) > 0 else None,
            "id": id_ctr.get_and_inc()
        }
    elif isinstance(value, list):
        return {
            "kind": "array",
            "type": _encode_type(id_ctr, value[0] if len(value) > 0 else None),
            "id": id_ctr.get_and_inc()
        }
    elif isinstance(value, set):
        return {
            "kind": "set",
            "type": _encode_type(id_ctr, value[0] if len(value) > 0 else None),
            "id": id_ctr.get_and_inc()
        }
    else:  # primitive type
        typ = str(type(value))
        if typ not in _py_to_zed_primitive_type:
            raise Exception(f"unknown zed primitive type for {typ}")
        return {
            "kind": "primitive",
            "name": _py_to_zed_primitive_type[typ],
        }


def _encode_value(value) -> typing.Union[list, str, None]:
    if isinstance(value, dict):
        return [_encode_value(_v) for _, _v in value.items()]
    elif isinstance(value, list):
        return [_encode_value(_v) for _v in value]
    elif isinstance(value, set):
        return [_encode_value(_v) for _v in value]
    elif isinstance(value, datetime.datetime):
        return encode_datetime(value)
    elif isinstance(value, datetime.timedelta):
        return durationpy.to_str(value)
    elif str(type(value)) in _py_to_zed_primitive_type:
        if value is None:
            return None
        if type(value) == bool:
            return str(value).lower()
        else:
            return str(value)
    else:
        raise Exception(f"cannot encode value of type {type(value)}")


def encode_datetime(value: datetime.datetime) -> str:
    return value.isoformat().replace("+00:00", "") + "Z"


class QueryError(Exception):
    """Raised by Client.query() when a query fails."""
    pass


def decode_raw(raw):
    types = {}
    for msg in raw:
        typ, value = msg['type'], msg['value']
        if isinstance(typ, dict):
            yield _decode_value(_decode_type(types, typ), value)
        elif typ == 'QueryError':
            raise QueryError(value['error'])


def _decode_type(types, typ):
    kind = typ['kind']
    if kind == 'ref':
        return types[typ['id']]
    if kind == 'primitive':
        return typ
    elif kind == 'record':
        if typ['fields'] is None:
            # XXX
            pass
        for f in typ['fields']:
            f['type'] = _decode_type(types, f['type'])
    elif kind in ['array', 'set']:
        typ['type'] = _decode_type(types, typ['type'])
    elif kind == 'map':
        typ['key_type'] = _decode_type(types, typ['key_type'])
        typ['val_type'] = _decode_type(types, typ['val_type'])
    elif kind == 'union':
        typ['types'] = [_decode_type(types, t) for t in typ['types']]
    elif kind == 'enum':
        pass
    elif kind in ['error', 'named']:
        typ['type'] = _decode_type(types, typ['type'])
    else:
        raise Exception(f'unknown type kind {kind}')
    types[typ['id']] = typ
    return typ


def _decode_value(typ, value):
    if value is None:
        return None
    kind = typ['kind']
    if kind == 'primitive':
        name = typ['name']
        if name in ['uint8', 'uint16', 'uint32', 'uint64',
                    'int8', 'int16', 'int32', 'int64']:
            return int(value)
        if name == 'duration':
            return durationpy.from_str(value)
        if name == 'time':
            return dateutil.parser.isoparse(value)
        if name in ['float16', 'float32', 'float64']:
            return float(value)
        if name == 'decimal':
            return decimal.Decimal(value)
        if name == 'bool':
            return value in {'T', 'true'}  # TBD patch upstream
        if name == 'bytes':
            return binascii.a2b_hex(value[2:])
        if name == 'string':
            return value
        if name == 'ip':
            return ipaddress.ip_address(value)
        if name == 'net':
            return ipaddress.ip_network(value)
        if name in 'type':
            return value
        if name == 'null':
            return None
        raise Exception(f'unknown primitive name {name}')
    if kind == 'record':
        return {f['name']: _decode_value(f['type'], v)
                for f, v in zip(typ['fields'], value)}
    if kind == 'array':
        return [_decode_value(typ['type'], v) for v in value]
    if kind == 'set':
        return {_decode_value(typ['type'], v) for v in value}
    if kind == 'map':
        key_type, val_type = typ['key_type'], typ['val_type']
        return {_decode_value(key_type, v[0]): _decode_value(val_type, v[1])
                for v in value}
    if kind == 'union':
        type_index, val = value
        return _decode_value(typ['types'][int(type_index)], val)
    if kind == 'enum':
        return typ['symbols'][int(value)]
    if kind in ['error', 'named']:
        return _decode_value(typ['type'], value)
    raise Exception(f'unknown type kind {kind}')


if __name__ == '__main__':
    test = [
        12,
        {},
        [],
        {"watt": "12"},
        {"watt": "12", "user": {"alice": True}},
    ]
    print("\n".join((encode(test))))
    # import zed
    # TBD fix zed.py/decoder handle null fields
    # print(list(zed.decode_raw(json.loads(line) for line in (encode(test)))))
