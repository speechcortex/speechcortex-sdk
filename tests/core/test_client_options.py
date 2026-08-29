# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import logging

import pytest

from speechcortex.core.client_options import ClientOptions
from speechcortex.version import __version__


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in (
        "SPEECHCORTEX_API_KEY",
        "SPEECHCORTEX_HOST",
        "SPEECHCORTEX_REALTIME_PATH",
        "SPEECHCORTEX_BATCH_PATH",
        "SPEECHCORTEX_LOGGING",
    ):
        monkeypatch.delenv(var, raising=False)


def test_url_is_required():
    with pytest.raises(ValueError, match="URL is required"):
        ClientOptions(url="")


def test_url_from_env(monkeypatch):
    monkeypatch.setenv("SPEECHCORTEX_HOST", "wss://api.example.ai")
    options = ClientOptions(api_key="k")
    assert options.url == "wss://api.example.ai"


def test_url_protocol_is_added_when_missing():
    options = ClientOptions(api_key="k", url="api.example.ai")
    assert options.url == "wss://api.example.ai"


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("SPEECHCORTEX_API_KEY", "env-key")
    options = ClientOptions(url="wss://api.example.ai")
    assert options.api_key == "env-key"


def test_paths_normalized():
    options = ClientOptions(api_key="k", url="wss://api.example.ai", realtime_path="transcribe")
    assert options.realtime_path == "/transcribe"
    assert options.batch_path == "/api/v1/transcription"


def test_realtime_path_from_env(monkeypatch):
    monkeypatch.setenv("SPEECHCORTEX_REALTIME_PATH", "/custom/rt")
    options = ClientOptions(api_key="k", url="wss://api.example.ai", realtime_path="")
    assert options.realtime_path == "/custom/rt"


def test_verbose_from_env(monkeypatch):
    monkeypatch.setenv("SPEECHCORTEX_LOGGING", "DEBUG")
    options = ClientOptions(api_key="k", url="wss://api.example.ai")
    assert options.verbose == logging.DEBUG


def test_websocket_headers_use_basic_auth():
    options = ClientOptions(api_key="the-key", url="wss://api.example.ai")
    headers = options.get_websocket_headers()
    assert headers["Authorization"] == "Basic the-key"
    assert __version__ in headers["User-Agent"]
    assert headers["User-Agent"].startswith("speechcortex-sdk/")


def test_websocket_headers_without_key():
    options = ClientOptions(url="wss://api.example.ai")
    assert "Authorization" not in options.get_websocket_headers()


def test_rest_headers_use_x_api_key():
    options = ClientOptions(api_key="the-key", url="wss://api.example.ai")
    headers = options.get_rest_headers()
    assert headers["X-API-Key"] == "the-key"
    assert "Authorization" not in headers


def test_extra_headers_override_defaults():
    options = ClientOptions(
        api_key="k",
        url="wss://api.example.ai",
        headers={"X-Custom": "1", "Accept": "text/plain"},
    )
    headers = options.get_rest_headers()
    assert headers["X-Custom"] == "1"
    assert headers["Accept"] == "text/plain"


def test_rest_base_url_converts_scheme():
    assert (
        ClientOptions(api_key="k", url="wss://api.example.ai").rest_base_url
        == "https://api.example.ai"
    )
    assert (
        ClientOptions(api_key="k", url="ws://api.example.ai").rest_base_url
        == "http://api.example.ai"
    )
    assert (
        ClientOptions(api_key="k", url="https://api.example.ai").rest_base_url
        == "https://api.example.ai"
    )
