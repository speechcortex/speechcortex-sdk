# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""Socket-client behavior: event dispatch, parsing leniency, sending."""

import asyncio
import json
import threading
import time

from speechcortex.core.client_options import ClientOptions
from speechcortex.core.events import EventType
from speechcortex.listen.v1.client import AsyncRealtimeV1Client, RealtimeV1Client
from speechcortex.listen.v1.types import (
    Results,
    SpeechStarted,
    UtteranceEnd,
)

RESULTS_PAYLOAD = {
    "type": "Results",
    "channel_index": [0, 1],
    "duration": 1.52,
    "start": 0.0,
    "is_final": True,
    "speech_final": False,
    "channel": {
        "alternatives": [
            {
                "transcript": "hello world",
                "confidence": 0.99,
                "words": [
                    {"word": "hello", "start": 0.0, "end": 0.5, "confidence": 0.99},
                    {"word": "world", "start": 0.6, "end": 1.5, "confidence": 0.98,
                     "punctuated_word": "world."},
                ],
            }
        ]
    },
    "start_of_turn": {"event": True, "confidence": 0.87, "timestamp": 10.0},
    "metadata": {"request_id": "req-1", "model_uuid": "uuid-1"},
}



def _send_json(conn, payload):
    """Handler that sends one JSON message, then closes the connection."""

    async def _run():
        await conn.send(json.dumps(payload))

    return _run()


def _send_results(conn):
    return _send_json(conn, RESULTS_PAYLOAD)


def _send_mystery(conn):
    return _send_json(conn, {"type": "Mystery"})


def make_client(server) -> RealtimeV1Client:
    return RealtimeV1Client(config=ClientOptions(api_key="k", url=server.url))


def collect_events(server, seconds=2.0):
    """Connect, run start_listening in a thread, and collect events until CLOSE."""
    events = []
    lock = threading.Lock()
    closed = threading.Event()

    with make_client(server).connect() as connection:
        connection.on(
            EventType.MESSAGE,
            lambda data: (lock.acquire(), events.append(("MESSAGE", data)), lock.release()),
        )
        connection.on(
            EventType.CLOSE,
            lambda data: (lock.acquire(), events.append(("CLOSE", data)), lock.release(), closed.set()),
        )

        thread = threading.Thread(target=connection.start_listening, daemon=True)
        thread.start()
        closed.wait(timeout=seconds)
        thread.join(timeout=seconds)
    return events


def test_results_payload_dispatch_and_turn_info(ws_server):
    server = ws_server(
        handler=_send_results
    )
    events = collect_events(server)

    messages = [data for kind, data in events if kind == "MESSAGE"]
    assert len(messages) == 1
    result = messages[0]
    assert isinstance(result, Results)
    assert result.is_final is True
    assert result.channel.alternatives[0].transcript == "hello world"
    assert result.channel.alternatives[0].words[1].punctuated_word == "world."
    # Turn info is typed and present
    assert result.start_of_turn is not None
    assert result.start_of_turn.event is True
    assert result.start_of_turn.confidence == 0.87
    assert result.end_of_turn is None
    assert result.metadata.request_id == "req-1"
    assert events[-1][0] == "CLOSE"


def test_results_without_turn_info_is_none(ws_server):
    payload = {
        k: v
        for k, v in RESULTS_PAYLOAD.items()
        if not k.startswith(("start_of_turn", "end_of_turn"))
    }
    server = ws_server(handler=lambda conn: _send_json(conn, payload))
    events = collect_events(server)
    result = [d for kind, d in events if kind == "MESSAGE"][0]
    assert isinstance(result, Results)
    assert result.start_of_turn is None
    assert result.end_of_turn is None


def test_unknown_fields_are_preserved(ws_server):
    payload = {**RESULTS_PAYLOAD, "brand_new_server_field": {"a": 1}}
    server = ws_server(handler=lambda conn: _send_json(conn, payload))
    events = collect_events(server)
    result = [d for kind, d in events if kind == "MESSAGE"][0]
    assert isinstance(result, Results)
    assert result.brand_new_server_field == {"a": 1}


def test_speech_started_and_utterance_end_dispatch(ws_server):
    async def handler(conn):
        await conn.send(json.dumps({"type": "SpeechStarted", "channel": [0], "timestamp": 1.0}))
        await conn.send(json.dumps({"type": "UtteranceEnd", "channel": [0], "last_word_end": 2.5}))

    server = ws_server(handler=handler)
    events = collect_events(server)
    messages = [data for kind, data in events if kind == "MESSAGE"]
    assert isinstance(messages[0], SpeechStarted)
    assert isinstance(messages[1], UtteranceEnd)
    assert messages[1].last_word_end == 2.5


def test_unknown_message_type_is_delivered_as_raw_dict(ws_server):
    server = ws_server(handler=_send_mystery)
    events = collect_events(server)
    messages = [data for kind, data in events if kind == "MESSAGE"]
    assert messages == [{"type": "Mystery"}]


def test_send_media_reaches_server(ws_server):
    received = []

    async def handler(conn):
        async for message in conn:
            received.append(message)

    server = ws_server(handler=handler)
    with make_client(server).connect() as connection:
        connection.send_media(b"\x01\x02\x03")
        connection.send_media(b"\x04\x05\x06")
        time.sleep(0.3)

    assert received == [b"\x01\x02\x03", b"\x04\x05\x06"]


def test_send_keep_alive_reaches_server(ws_server):
    received = []

    async def handler(conn):
        async for message in conn:
            received.append(message)

    server = ws_server(handler=handler)
    with make_client(server).connect() as connection:
        connection.send_keep_alive()
        time.sleep(0.3)

    assert json.loads(received[0]) == {"type": "KeepAlive"}


def test_async_start_listening_events(ws_server):
    server = ws_server(handler=_send_results)
    client = AsyncRealtimeV1Client(config=ClientOptions(api_key="k", url=server.url))

    async def run():
        events = []
        async with client.connect() as connection:
            connection.on(EventType.MESSAGE, lambda data: events.append(data))
            connection.on(EventType.CLOSE, lambda data: events.append("CLOSE"))
            await connection.start_listening()
        return events

    events = asyncio.run(asyncio.wait_for(run(), timeout=10.0))

    assert isinstance(events[0], Results)
    assert events[-1] == "CLOSE"
