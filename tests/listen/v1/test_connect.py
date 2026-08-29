# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""Wire-format tests: the exact query string and headers on the websocket handshake."""

import asyncio

import pytest

from speechcortex.core.client_options import ClientOptions
from speechcortex.core.request_options import RequestOptions
from speechcortex.listen.v1.client import AsyncRealtimeV1Client, RealtimeV1Client

API_KEY = "test-api-key"


def make_client(server) -> RealtimeV1Client:
    config = ClientOptions(api_key=API_KEY, url=server.url)
    return RealtimeV1Client(config=config)


def make_async_client(server) -> AsyncRealtimeV1Client:
    config = ClientOptions(api_key=API_KEY, url=server.url)
    return AsyncRealtimeV1Client(config=config)


def test_default_query_string_is_pinned(ws_server):
    server = ws_server()
    with make_client(server).connect():
        pass
    path, _ = server.requests[0]
    assert path == (
        "/transcribe/realtime"
        "?model=cove&language=en-US&interim_results=true"
        "&encoding=linear16&sample_rate=16000&channels=1&utterance_end_ms=1000"
    )


def test_model_can_be_overridden_or_omitted(ws_server):
    server = ws_server()
    with make_client(server).connect(model="custom-model"):
        pass
    path, _ = server.requests[0]
    assert "model=custom-model" in path

    server2 = ws_server()
    with make_client(server2).connect(model=None):
        pass
    path2, _ = server2.requests[0]
    assert "model=" not in path2


def test_turn_detection_params_sent_when_enabled(ws_server):
    server = ws_server()
    with make_client(server).connect(
        turn_detection=True,
        turn_detection_threshold=0.65,
        turn_detection_timeout_ms=1500,
    ):
        pass
    path, _ = server.requests[0]
    assert path.endswith(
        "&turn_detection=true&turn_detection_threshold=0.65&turn_detection_timeout_ms=1500"
    )


def test_turn_detection_defaults(ws_server):
    server = ws_server()
    with make_client(server).connect(turn_detection=True):
        pass
    path, _ = server.requests[0]
    assert "turn_detection=true" in path
    assert "turn_detection_threshold=0.6" in path
    assert "turn_detection_timeout_ms=2000" in path


def test_turn_detection_params_omitted_when_disabled(ws_server):
    server = ws_server()
    with make_client(server).connect(turn_detection=False):
        pass
    path, _ = server.requests[0]
    assert "turn_detection" not in path
    assert "turn_detection_threshold" not in path
    assert "turn_detection_timeout_ms" not in path


def test_bg_speech_filter_string_sent(ws_server):
    server = ws_server()
    with make_client(server).connect(bg_speech_filter="balanced"):
        pass
    path, _ = server.requests[0]
    assert "bg_speech_filter=balanced" in path


def test_bg_speech_filter_false_omitted(ws_server):
    server = ws_server()
    with make_client(server).connect(bg_speech_filter=False):
        pass
    path, _ = server.requests[0]
    assert "bg_speech_filter" not in path


def test_extra_params_merged_last(ws_server):
    server = ws_server()
    with make_client(server).connect(extra={"brand_new_param": "on", "flag": True}):
        pass
    path, _ = server.requests[0]
    assert "brand_new_param=on" in path
    assert "flag=true" in path


def test_additional_query_parameters_merged(ws_server):
    server = ws_server()
    request_options: RequestOptions = {"additional_query_parameters": {"extra_param": 7}}
    with make_client(server).connect(request_options=request_options):
        pass
    path, _ = server.requests[0]
    assert "extra_param=7" in path


def test_auth_header_sent(ws_server):
    server = ws_server()
    with make_client(server).connect():
        pass
    _, headers = server.requests[0]
    assert headers["authorization"] == f"Basic {API_KEY}"


def test_custom_realtime_path(ws_server):
    server = ws_server()
    config = ClientOptions(api_key=API_KEY, url=server.url, realtime_path="/v2/realtime")
    with RealtimeV1Client(config=config).connect():
        pass
    path, _ = server.requests[0]
    assert path.startswith("/v2/realtime?")


def test_handshake_401_raises_api_error(ws_server):
    server = ws_server(reject_status=401)
    with pytest.raises(Exception) as exc_info:
        with make_client(server).connect():
            pass
    from speechcortex.core.api_error import ApiError

    assert isinstance(exc_info.value, ApiError)
    assert exc_info.value.status_code == 401
    assert "credentials" in str(exc_info.value)


def test_handshake_403_raises_api_error(ws_server):
    from speechcortex.core.api_error import ApiError

    server = ws_server(reject_status=403)
    with pytest.raises(ApiError) as exc_info:
        with make_client(server).connect():
            pass
    assert exc_info.value.status_code == 403


def test_async_connect_default_query_string(ws_server):
    server = ws_server()

    async def run():
        async with make_async_client(server).connect():
            pass

    asyncio.run(run())
    path, headers = server.requests[0]
    assert path == (
        "/transcribe/realtime"
        "?model=cove&language=en-US&interim_results=true"
        "&encoding=linear16&sample_rate=16000&channels=1&utterance_end_ms=1000"
    )
    assert headers["authorization"] == f"Basic {API_KEY}"
