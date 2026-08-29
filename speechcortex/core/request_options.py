# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Any

from typing_extensions import TypedDict


class RequestOptions(TypedDict, total=False):
    """
    Request-specific configuration that can be passed as the last argument
    of any client method.

    Attributes:
        timeout: Request timeout in seconds.
        additional_headers: Extra headers merged over the client defaults.
        additional_query_parameters: Extra query parameters merged over the
            method's own parameters.
    """

    timeout: float | None
    additional_headers: dict[str, str] | None
    additional_query_parameters: dict[str, Any] | None


def get_request_options_value(
    request_options: RequestOptions | None,
    key: str,
    default: None | dict[str, Any] | float = None,
) -> Any:
    """Convenience accessor that tolerates a None request_options."""
    if request_options is None:
        return default
    value = request_options.get(key)
    return default if value is None else value
