# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from speechcortex.core.api_error import ApiError, redact_sensitive_headers


def test_authorization_is_masked():
    headers = {"Authorization": "Basic secret-key", "dg-request-id": "abc"}
    redacted = redact_sensitive_headers(headers)
    assert redacted["Authorization"] == "<redacted>"
    assert redacted["dg-request-id"] == "abc"


def test_x_api_key_is_masked_case_insensitively():
    redacted = redact_sensitive_headers({"X-API-Key": "sk", "x-aPi-kEy": "sk"})
    assert redacted == {"X-API-Key": "<redacted>", "x-aPi-kEy": "<redacted>"}


def test_api_error_masks_headers_in_construction_and_str():
    err = ApiError(
        status_code=401,
        headers={"Authorization": "Basic super-secret"},
        body="invalid credentials",
    )
    assert err.headers["Authorization"] == "<redacted>"
    assert "super-secret" not in str(err)


def test_api_error_attributes():
    err = ApiError(status_code=404, body="nope")
    assert err.status_code == 404
    assert err.body == "nope"
    assert "404" in str(err)


def test_api_error_with_no_headers():
    err = ApiError(status_code=500, body="boom")
    assert err.headers == {}
