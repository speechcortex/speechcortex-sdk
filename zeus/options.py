# Copyright 2024 Zeus SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import sys
import re
import os
from typing import Dict, Optional
import logging
import numbers

from .utils import verboselogs
from .errors import ZeusApiKeyError

try:
    from . import __version__
except ImportError:
    __version__ = "0.1.0"


class ZeusClientOptions:  # pylint: disable=too-many-instance-attributes
    """
    Represents options for configuring a Zeus client.

    This class allows you to customize various options for interacting with the Zeus API.

    Attributes:
        api_key: (Optional) A Zeus API key used for authentication. Default uses the `ZEUS_API_KEY` environment variable.
        url: (Optional) The URL used to interact with Zeus API. Defaults to `https://api.zeus.com`.
        verbose: (Optional) The logging level for the client. Defaults to `verboselogs.WARNING`.
    headers: (Optional) Headers for initializing the client.
    options: (Optional) Additional options for initializing the client.
    realtime_path: (Optional) Path for realtime websocket endpoint. Defaults to `/transcribe/realtime`.
    """

    _logger: verboselogs.VerboseLogger
    _inspect_listen: bool = False

    def __init__(
        self,
        api_key: str = "",
        url: str = "",
        verbose: int = verboselogs.WARNING,
        headers: Optional[Dict] = None,
        options: Optional[Dict] = None,
        realtime_path: str = "/transcribe/realtime",
    ):
        self._logger = verboselogs.VerboseLogger(__name__)
        self._logger.addHandler(logging.StreamHandler())

        if api_key is None:
            api_key = ""

        self.verbose = verbose
        self.api_key = api_key

        if headers is None:
            headers = {}
        self._update_headers(headers=headers)

        if len(url) == 0:
            url = "wss://rt-zeus-mldev.internalobserve.com"
        self.url = self._get_url(url).rstrip('/')

        if options is None:
            options = {}
        self.options = options

        # Normalize realtime path (ensure starts with '/'; strip trailing '?')
        if realtime_path is None or realtime_path == "":
            realtime_path = "/transcribe/realtime"
        if not realtime_path.startswith("/"):
            realtime_path = "/" + realtime_path
        # keep any query string the user might provide
        self.realtime_path = realtime_path

        if self.is_auto_flush_reply_enabled():
            self._inspect_listen = True

    def set_apikey(self, api_key: str):
        """
        set_apikey: Sets the API key for the client.

        Args:
            api_key: The Zeus API key used for authentication.
        """
        self.api_key = api_key
        self._update_headers()

    def _get_url(self, url) -> str:
        # Check if URL already has a protocol (http, https, ws, wss)
        if not re.match(r"^(https?|wss?)://", url, re.IGNORECASE):
            url = "wss://" + url
        return url

    def _update_headers(self, headers: Optional[Dict] = None):
        self.headers = {}
        self.headers["Accept"] = "application/json"
        if self.api_key:
            self.headers["Authorization"] = f"Basic {self.api_key}"
        elif "Authorization" in self.headers:
            del self.headers["Authorization"]
        self.headers[
            "User-Agent"
        ] = f"zeus-sdk/{__version__} python/{sys.version_info[0]}.{sys.version_info[1]}"
        # Overwrite / add any headers that were passed in
        if headers:
            self.headers.update(headers)

    def is_keep_alive_enabled(self) -> bool:
        """
        is_keep_alive_enabled: Returns True if the client is configured to keep the connection alive.
        """
        return self.options.get("keepalive", False) or self.options.get(
            "keep_alive", False
        )

    def is_auto_flush_reply_enabled(self) -> bool:
        """
        is_auto_flush_reply_enabled: Returns True if the client is configured to auto-flush for listen.
        """
        auto_flush_reply_delta = float(self.options.get("auto_flush_reply_delta", 0))
        return (
            isinstance(auto_flush_reply_delta, numbers.Number)
            and auto_flush_reply_delta > 0
        )

    def is_inspecting_listen(self) -> bool:
        """
        is_inspecting_listen: Returns True if the client is inspecting listen messages.
        """
        return self._inspect_listen


class ClientOptionsFromEnv(ZeusClientOptions):
    """
    This class extends ZeusClientOptions and will attempt to use environment variables first before defaults.
    """

    _logger: verboselogs.VerboseLogger

    def __init__(
        self,
        api_key: str = "",
        url: str = "",
        verbose: int = verboselogs.WARNING,
        headers: Optional[Dict] = None,
        options: Optional[Dict] = None,
        realtime_path: str = "/transcribe/realtime",
    ):
        self._logger = verboselogs.VerboseLogger(__name__)
        self._logger.addHandler(logging.StreamHandler())
        self._logger.setLevel(verboselogs.WARNING)  # temporary set for setup

        if api_key is None:
            api_key = ""

        if api_key == "":
            api_key = os.getenv("ZEUS_API_KEY", "")
            if api_key == "":
                self._logger.critical("Zeus API KEY is not set")
                raise ZeusApiKeyError("Zeus API KEY is not set")

        if url == "":
            url = os.getenv("ZEUS_HOST", "wss://rt-zeus-mldev.internalobserve.com")
            self._logger.notice(f"Zeus host is set to {url}")

        if verbose == verboselogs.WARNING:
            _loglevel = os.getenv("ZEUS_LOGGING", "")
            if _loglevel != "":
                loglevel_map = {
                    "NOTSET": verboselogs.NOTSET,
                    "SPAM": verboselogs.SPAM,
                    "DEBUG": verboselogs.DEBUG,
                    "VERBOSE": verboselogs.VERBOSE,
                    "NOTICE": verboselogs.NOTICE,
                    "WARNING": verboselogs.WARNING,
                    "SUCCESS": verboselogs.SUCCESS,
                    "ERROR": verboselogs.ERROR,
                    "CRITICAL": verboselogs.CRITICAL,
                }
                verbose = loglevel_map.get(_loglevel.upper(), verboselogs.WARNING)
                self._logger.notice(f"Logging level is set to {_loglevel}")

        if headers is None:
            headers = {}
            for x in range(0, 20):
                header = os.getenv(f"ZEUS_HEADER_{x}", None)
                if header is not None:
                    headers[header] = os.getenv(f"ZEUS_HEADER_VALUE_{x}", None)
                    self._logger.debug(
                        "Zeus header %s is set with value %s",
                        header,
                        headers[header],
                    )
                else:
                    break
            if len(headers) == 0:
                self._logger.notice("Zeus headers are not set")
                headers = None

        if options is None:
            options = {}
            for x in range(0, 20):
                param = os.getenv(f"ZEUS_PARAM_{x}", None)
                if param is not None:
                    options[param] = os.getenv(f"ZEUS_PARAM_VALUE_{x}", None)
                    self._logger.debug(
                        "Zeus option %s is set with value %s", param, options[param]
                    )
                else:
                    break
            if len(options) == 0:
                self._logger.notice("Zeus options are not set")
                options = None

        if realtime_path == "/transcribe/realtime":
            realtime_path = os.getenv("ZEUS_REALTIME_PATH", realtime_path)
            if realtime_path:
                self._logger.notice(f"Realtime path is set to {realtime_path}")

        super().__init__(
            api_key=api_key,
            url=url,
            verbose=verbose,
            headers=headers,
            options=options,
            realtime_path=realtime_path,
        )
