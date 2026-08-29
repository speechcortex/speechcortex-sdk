# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Any


def remove_none_from_dict(d: dict[str, Any] | None) -> dict[str, Any]:
    if not d:
        return {}
    return {k: v for k, v in d.items() if v is not None}
