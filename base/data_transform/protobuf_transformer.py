# -*- coding: utf-8 -*-

from collections.abc import Sequence

from google.protobuf import json_format


def dict_to_protobuf(protobuf_json: dict, protobuf_cls: object) -> object:
    if protobuf_json is None:
        return
    return json_format.ParseDict(protobuf_json, protobuf_cls(), ignore_unknown_fields=True)


def batch_dict_to_protobuf(protobuf_json_list: list, protobuf_cls: object) -> list:
    if protobuf_json_list is None:
        return
    if not isinstance(protobuf_json_list, Sequence):
        raise ValueError('protobuf_json_list of type "{}" is not iterable.'.format(type(protobuf_json_list)))
    return [dict_to_protobuf(protobuf_json, protobuf_cls) for protobuf_json in protobuf_json_list]


def protobuf_to_dict(protobuf: object, preserving_proto_field_name: bool = False) -> dict:
    if protobuf is None:
        return None
    dict = json_format.MessageToDict(protobuf, including_default_value_fields=True, preserving_proto_field_name=preserving_proto_field_name)
    return dict


def batch_protobuf_to_dict(protobuf_list: list, preserving_proto_field_name: bool = False) -> list:
    if protobuf_list is None:
        return
    if not isinstance(protobuf_list, Sequence):
        raise ValueError('protobuf_list of type "{}" is not iterable.'.format(type(protobuf_list)))
    return [protobuf_to_dict(protobuf, preserving_proto_field_name=preserving_proto_field_name) for protobuf in protobuf_list]
