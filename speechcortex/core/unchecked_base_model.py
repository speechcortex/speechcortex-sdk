# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Any, TypeVar

import pydantic

T = TypeVar("T")


class UncheckedBaseModel(pydantic.BaseModel):
    """
    Pydantic model base that tolerates unknown fields.

    Response models inherit from this so that new fields added by the server
    never break parsing: they are preserved on the model instead of being
    rejected.
    """

    model_config = pydantic.ConfigDict(extra="allow", frozen=True)


def construct_type(type_: Any, object_: Any) -> Any:
    """
    Validate ``object_`` against ``type_``, falling back to the raw value.

    ``type_`` may be a single model type or a union of response models.
    Used on websocket message boundaries: if the server sends a payload the
    current SDK does not fully understand, the raw (dict) value is returned
    instead of raising.
    """
    try:
        return pydantic.TypeAdapter(type_).validate_python(object_)
    except pydantic.ValidationError:
        return object_
