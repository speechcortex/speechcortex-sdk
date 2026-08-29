# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Any

# Header names whose values must never appear in exceptions, logs or tracebacks.
_SENSITIVE_HEADERS = ("authorization", "x-api-key", "proxy-authorization")


def redact_sensitive_headers(headers: dict[str, Any] | None) -> dict[str, Any]:
    """Return a copy of ``headers`` with credential values masked."""
    redacted: dict[str, Any] = {}
    for key, value in (headers or {}).items():
        if str(key).lower() in _SENSITIVE_HEADERS:
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


class ApiError(Exception):
    """
    Raised when the SpeechCortex API returns an error or a connection
    cannot be established.

    Credential-bearing headers are masked at construction time so the error
    is safe to log or send to an error tracker.

    Attributes:
        status_code: HTTP (or handshake-equivalent) status code.
        headers: Response/request headers associated with the failure.
        body: Response body or human-readable description of the failure.
    """

    def __init__(
        self,
        *,
        status_code: int | None = None,
        headers: dict[str, Any] | None = None,
        body: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = redact_sensitive_headers(dict(headers) if headers else None)
        self.body = body
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        message = "SpeechCortex API error"
        if self.status_code is not None:
            message += f" (status {self.status_code})"
        if self.body is not None:
            message += f": {self.body}"
        return message
