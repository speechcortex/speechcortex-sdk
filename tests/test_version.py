# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import speechcortex
from speechcortex.version import __version__


def test_version_is_single_sourced():
    assert speechcortex.__version__ == __version__


def test_version_is_a_string():
    assert isinstance(__version__, str)
    assert __version__.count(".") == 2
