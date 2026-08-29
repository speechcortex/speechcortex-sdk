# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT


# exceptions for microphone
class SpeechCortexMicrophoneError(Exception):
    """
    Exception raised for known errors related to Microphone library.

    Attributes:
        message (str): The error message describing the exception.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.name = "SpeechCortexMicrophoneError"
        self.message = message

    def __str__(self):
        return f"{self.name}: {self.message}"
