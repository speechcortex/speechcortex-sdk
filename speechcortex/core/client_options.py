# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import logging
import os
import re
import sys

from .environment import DEFAULT_BATCH_PATH, DEFAULT_REALTIME_PATH

_logger = logging.getLogger("speechcortex")

_LOG_LEVEL_NAMES = {
    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _resolve_log_level(verbose: int) -> int:
    """Resolve the verbose level, honoring SPEECHCORTEX_LOGGING by name."""
    if verbose != logging.WARNING:
        return verbose
    level_name = os.getenv("SPEECHCORTEX_LOGGING", "")
    if level_name:
        return _LOG_LEVEL_NAMES.get(level_name.upper(), logging.WARNING)
    return verbose


class ClientOptions:
    """
    Options for configuring a SpeechCortex client.

    Attributes:
        api_key: SpeechCortex API key. Defaults to the ``SPEECHCORTEX_API_KEY``
            environment variable.
        url: Base URL of the SpeechCortex API (``wss://`` or ``https://``).
            Required — defaults to the ``SPEECHCORTEX_HOST`` environment variable.
        realtime_path: Path of the realtime websocket endpoint.
        batch_path: Path of the batch transcription REST endpoints.
        headers: Additional headers merged over the client defaults.
        verbose: Logging level for the ``speechcortex`` logger. Defaults to
            the ``SPEECHCORTEX_LOGGING`` environment variable or ``WARNING``.
    """

    def __init__(
        self,
        api_key: str = "",
        url: str = "",
        realtime_path: str = DEFAULT_REALTIME_PATH,
        batch_path: str = DEFAULT_BATCH_PATH,
        headers: dict[str, str] | None = None,
        verbose: int = logging.WARNING,
    ) -> None:
        self.api_key = api_key or os.getenv("SPEECHCORTEX_API_KEY", "")
        self.verbose = _resolve_log_level(verbose)

        url = url or os.getenv("SPEECHCORTEX_HOST", "")
        if not url:
            raise ValueError(
                "SpeechCortex URL is required. "
                "Set SPEECHCORTEX_HOST environment variable or pass url parameter."
            )
        self.url = self._normalize_url(url).rstrip("/")

        if not realtime_path:
            realtime_path = os.getenv("SPEECHCORTEX_REALTIME_PATH", DEFAULT_REALTIME_PATH)
        if not realtime_path.startswith("/"):
            realtime_path = "/" + realtime_path
        self.realtime_path = realtime_path

        if not batch_path:
            batch_path = os.getenv("SPEECHCORTEX_BATCH_PATH", DEFAULT_BATCH_PATH)
        if not batch_path.startswith("/"):
            batch_path = "/" + batch_path
        self.batch_path = batch_path

        self.extra_headers = dict(headers) if headers else {}

    @staticmethod
    def _normalize_url(url: str) -> str:
        # Check if URL already has a protocol (http, https, ws, wss)
        if not re.match(r"^(https?|wss?)://", url, re.IGNORECASE):
            return "wss://" + url
        return url

    @property
    def rest_base_url(self) -> str:
        """The config URL converted to an http(s) base for REST calls."""
        raw = self.url
        if raw.startswith("wss://"):
            return raw.replace("wss://", "https://", 1)
        if raw.startswith("ws://"):
            return raw.replace("ws://", "http://", 1)
        return raw

    @property
    def _user_agent(self) -> str:
        from ..version import __version__

        return (
            f"speechcortex-sdk/{__version__} "
            f"python/{sys.version_info[0]}.{sys.version_info[1]}"
        )

    def get_websocket_headers(self) -> dict[str, str]:
        """
        Headers for realtime websocket connections.

        The realtime endpoint authenticates with ``Authorization: Basic <key>``
        where ``<key>`` is the pre-encoded API key (sent as-is, not base64'd).
        """
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": self._user_agent,
        }
        if self.api_key:
            headers["Authorization"] = f"Basic {self.api_key}"
        headers.update(self.extra_headers)
        return headers

    def get_rest_headers(self) -> dict[str, str]:
        """
        Headers for batch REST calls.

        The batch endpoints authenticate with ``X-API-Key``.
        """
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": self._user_agent,
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        headers.update(self.extra_headers)
        return headers
