import json
import datetime
import typing

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


"""TBD move to zed/zed.py and add decoder"""


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


def _encode_value(value) -> typing.Union[list, str]:
    if isinstance(value, dict):
        return [_encode_value(_v) for _, _v in value.items()]
    elif isinstance(value, list):
        return [_encode_value(_v) for _v in value]
    elif isinstance(value, set):
        return [_encode_value(_v) for _v in value]
    elif isinstance(value, datetime.datetime):
        return value.isoformat().replace("+00:00", "") + "Z"
    # TBD check stringification for other primitive types
    elif str(type(value)) in _py_to_zed_primitive_type:
        return str(value)
    else:
        raise Exception(f"cannot encode value of type {type(value)}")


if __name__ == '__main__':
    test = [
        12,
        {},
        [],
        {"watt": "12"},
        {"watt": "12", "user": ["alice"]},
    ]
    print("\n".join((encode(test))))
    # import zed
    # TBD fix zed.py/decoder handle null fields
    # print(list(zed.decode_raw(json.loads(line) for line in (encode(test)))))
