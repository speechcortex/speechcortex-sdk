# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""Client namespace routing tests (Deepgram-style listen layout)."""

import pytest

from speechcortex import AsyncSpeechCortexClient, SpeechCortexClient
from speechcortex.listen.batch.client import AsyncBatchV1Client, BatchV1Client
from speechcortex.listen.v1.client import AsyncRealtimeV1Client, RealtimeV1Client


@pytest.fixture
def url(monkeypatch):
    monkeypatch.setenv("SPEECHCORTEX_HOST", "wss://api.example.ai")
    return "wss://api.example.ai"


def test_listen_v1_routes_to_realtime_client(url):
    client = SpeechCortexClient(api_key="k")
    assert isinstance(client.listen.v1.client, RealtimeV1Client)
    assert callable(client.listen.v1.connect)


def test_listen_batch_routes_to_batch_client(url):
    client = SpeechCortexClient(api_key="k")
    assert isinstance(client.listen.batch.v1, BatchV1Client)


def test_async_client_twins(url):
    client = AsyncSpeechCortexClient(api_key="k")
    assert isinstance(client.listen.v1.client, AsyncRealtimeV1Client)
    assert isinstance(client.listen.batch.v1, AsyncBatchV1Client)


def test_routers_are_lazy_and_cached(url):
    client = SpeechCortexClient(api_key="k")
    assert client.listen.v1.client is client.listen.v1.client
    assert client.listen.batch.v1 is client.listen.batch.v1


def test_no_transcribe_namespace(url):
    client = SpeechCortexClient(api_key="k")
    assert not hasattr(client, "transcribe")
