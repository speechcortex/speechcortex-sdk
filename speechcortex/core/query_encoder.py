# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Any


def _coerce_query_value(value: Any) -> Any:
    # urllib.parse.urlencode stringifies bools via str(), producing "True"/"False";
    # the SpeechCortex websocket endpoint expects lowercase.
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


# Flattens dicts to be of the form {"key[subkey][subkey2]": value} where value is not a dict
def traverse_query_dict(
    dict_flat: dict[str, Any], key_prefix: str | None = None
) -> list[tuple[str, Any]]:
    result = []
    for k, v in dict_flat.items():
        key = f"{key_prefix}[{k}]" if key_prefix is not None else k
        if isinstance(v, dict):
            result.extend(traverse_query_dict(v, key))
        elif isinstance(v, list):
            for arr_v in v:
                if isinstance(arr_v, dict):
                    result.extend(traverse_query_dict(arr_v, key))
                else:
                    result.append((key, _coerce_query_value(arr_v)))
        else:
            result.append((key, _coerce_query_value(v)))
    return result


def single_query_encoder(query_key: str, query_value: Any) -> list[tuple[str, Any]]:
    if isinstance(query_value, dict):
        return traverse_query_dict(query_value, query_key)
    elif isinstance(query_value, list):
        encoded_values: list[tuple[str, Any]] = []
        for value in query_value:
            if isinstance(value, dict):
                encoded_values.extend(single_query_encoder(query_key, value))
            else:
                encoded_values.append((query_key, _coerce_query_value(value)))
        return encoded_values

    return [(query_key, _coerce_query_value(query_value))]


def encode_query(query: dict[str, Any] | None) -> list[tuple[str, Any]] | None:
    if query is None:
        return None

    encoded_query = []
    for k, v in query.items():
        encoded_query.extend(single_query_encoder(k, v))
    return encoded_query
