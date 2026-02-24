# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from setuptools import setup, find_packages
import sys

if sys.version_info < (3, 10):
    sys.exit("Sorry, Python < 3.10 is not supported")

with open("README.md", "r", encoding="utf-8") as fh:
    LONG_DESCRIPTION = fh.read()

DESCRIPTION = "The official Python SDK for SpeechCortex ASR platform."

setup(
    name="speechcortex-sdk",
    version="0.1.dev2",
    author="SpeechCortex Team",
    author_email="team@speechcortex.com",
    url="https://github.com/speechcortex/speechcortex-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/speechcortex/speechcortex-sdk/issues",
        "Source Code": "https://github.com/speechcortex/speechcortex-sdk",
        "Documentation": "https://github.com/speechcortex/speechcortex-sdk#readme",
    },
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(exclude=["tests", "examples"]),
    install_requires=[
        "httpx>=0.25.2",
        "websockets>=12.0",
        "dataclasses-json>=0.6.3",
        "typing_extensions>=4.9.0",
        "aiohttp>=3.9.1",
        "aiofiles>=23.2.1",
        "aenum>=3.1.0",
        "deprecation>=2.1.0",
    ],
    keywords=["speechcortex", "asr", "speech-to-text", "speech recognition"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
)
