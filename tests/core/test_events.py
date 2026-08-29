# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import asyncio

from speechcortex.core.events import EventEmitterMixin, EventType


def test_sync_callback_receives_data():
    emitter = EventEmitterMixin()
    seen = []
    emitter.on(EventType.MESSAGE, seen.append)
    emitter._emit(EventType.MESSAGE, {"type": "Results"})
    assert seen == [{"type": "Results"}]


def test_multiple_callbacks_all_called():
    emitter = EventEmitterMixin()
    a, b = [], []
    emitter.on(EventType.OPEN, a.append)
    emitter.on(EventType.OPEN, b.append)
    emitter._emit(EventType.OPEN, None)
    assert a == [None] and b == [None]


def test_async_callback_is_awaited():
    emitter = EventEmitterMixin()
    seen = []

    async def handler(data):
        seen.append(data)

    emitter.on(EventType.MESSAGE, handler)
    asyncio.run(emitter._emit_async(EventType.MESSAGE, "x"))
    assert seen == ["x"]


def test_sync_callback_works_in_async_emit():
    emitter = EventEmitterMixin()
    seen = []
    emitter.on(EventType.MESSAGE, seen.append)
    asyncio.run(emitter._emit_async(EventType.MESSAGE, 1))
    assert seen == [1]


def test_emit_with_no_subscribers_is_noop():
    emitter = EventEmitterMixin()
    emitter._emit(EventType.ERROR, Exception("nobody listens"))
    asyncio.run(emitter._emit_async(EventType.ERROR, Exception("nobody listens")))
