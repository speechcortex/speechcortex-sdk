# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Compatibility layer for the ``websockets`` library across versions.

- websockets >= 14 uses ``additional_headers`` for both the asyncio and sync clients.
- websockets 12-13 use ``extra_headers``.

Both connect helpers try ``additional_headers`` first and fall back to
``extra_headers`` so the SDK works across the supported range.
"""

import typing

try:
    # websockets >= 14
    from websockets.asyncio.client import connect as _async_connect
except ImportError:  # pragma: no cover - depends on installed websockets version
    from websockets import connect as _async_connect  # type: ignore[no-redef]

from websockets.sync.client import connect as _sync_connect

_HEADER_PARAM_NAMES = ("additional_headers", "extra_headers")


def _connect_with_headers(connect_func: typing.Any, url: str, headers: dict[str, str]):
    last_error: TypeError
    for param in _HEADER_PARAM_NAMES:
        try:
            return connect_func(url, **{param: headers})
        except TypeError as exc:
            # Wrong keyword argument name for this websockets version.
            last_error = exc
    raise last_error


def sync_connect(url: str, headers: dict[str, str]):
    """Open a synchronous websocket connection (``websockets.sync.client``)."""
    return _connect_with_headers(_sync_connect, url, headers)


def async_connect(url: str, headers: dict[str, str]):
    """Open an asynchronous websocket connection."""
    return _connect_with_headers(_async_connect, url, headers)


def status_code_from_handshake_error(exc: Exception) -> int | None:
    """
    Extract the HTTP status code from a websocket handshake failure.

    websockets >= 12 raises ``InvalidStatus`` (with ``exc.response.status_code``);
    older versions raise ``InvalidStatusCode`` (with ``exc.status_code``).
    """
    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) is not None:
        status_code: int = response.status_code
        return status_code
    status: int | None = getattr(exc, "status_code", None)
    return status
