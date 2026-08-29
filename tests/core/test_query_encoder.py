# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from speechcortex.core.query_encoder import encode_query


def test_bools_coerced_to_lowercase():
    # urlencode would otherwise produce "True"/"False"
    assert encode_query({"a": True}) == [("a", "true")]
    assert encode_query({"a": False}) == [("a", "false")]


def test_scalars_pass_through():
    assert encode_query({"model": "zeus-v1", "sample_rate": 16000}) == [
        ("model", "zeus-v1"),
        ("sample_rate", 16000),
    ]


def test_nested_dicts_are_flattened():
    assert encode_query({"a": {"b": {"c": 1}}}) == [("a[b][c]", 1)]


def test_lists_are_repeated():
    assert encode_query({"a": [1, 2]}) == [("a", 1), ("a", 2)]


def test_none_returns_none():
    assert encode_query(None) is None


def test_empty_dict_returns_empty_list():
    assert encode_query({}) == []
