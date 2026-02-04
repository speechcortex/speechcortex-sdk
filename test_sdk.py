#!/usr/bin/env python3
# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Simple test to verify SpeechCortex SDK installation and basic functionality.
"""

import sys
import os

# Add parent directory to path for local development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("Testing SpeechCortex SDK...")
print("-" * 50)

# Test 1: Import the SDK
print("\n1. Testing imports...")
try:
    from speechcortex import SpeechCortexClient, LiveOptions, LiveTranscriptionEvents
    print("✓ Successfully imported speechcortex package")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Check version
print("\n2. Checking version...")
try:
    import speechcortex
    print(f"✓ SpeechCortex SDK version: {speechcortex.__version__}")
except Exception as e:
    print(f"✗ Failed to get version: {e}")

# Test 3: Initialize client
print("\n3. Testing client initialization...")
try:
    # Test with dummy API key
    client = SpeechCortexClient(api_key="test_key_12345")
    print("✓ Successfully initialized SpeechCortexClient")
    print(f"   API URL: {client._config.url}")
    print(f"   Headers: {client._config.headers}")
except Exception as e:
    print(f"✗ Failed to initialize client: {e}")
    sys.exit(1)

# Test 4: Access WebSocket client
print("\n4. Testing WebSocket client access...")
try:
    ws_client = client.listen.websocket.v("1")
    print("✓ Successfully accessed WebSocket client")
    print(f"   Client type: {type(ws_client).__name__}")
except Exception as e:
    print(f"✗ Failed to access WebSocket client: {e}")
    sys.exit(1)

# Test 5: Create LiveOptions
print("\n5. Testing LiveOptions...")
try:
    options = LiveOptions(
        model="zeus-v1",
        language="en-US",
        smart_format=True,
        interim_results=True,
    )
    print("✓ Successfully created LiveOptions")
    print(f"   Options dict: {options.to_dict()}")
except Exception as e:
    print(f"✗ Failed to create LiveOptions: {e}")
    sys.exit(1)

# Test 6: Test event handler registration
print("\n6. Testing event handler registration...")
try:
    def dummy_handler(self, result, **kwargs):
        pass
    
    ws_client.on(LiveTranscriptionEvents.Transcript, dummy_handler)
    print("✓ Successfully registered event handler")
except Exception as e:
    print(f"✗ Failed to register event handler: {e}")
    sys.exit(1)

# Test 7: Check Microphone import
print("\n7. Testing Microphone import...")
try:
    from speechcortex import Microphone
    print("✓ Microphone class imported successfully")
    print("   Note: pyaudio must be installed to use Microphone")
except Exception as e:
    print(f"⚠  Microphone import warning: {e}")
    print("   This is expected if pyaudio is not installed")

print("\n" + "-" * 50)
print("✓ All core tests passed!")
print("\nNext steps:")
print("1. Set your API key: export SPEECHCORTEX_API_KEY=your_actual_key")
print("2. Update the API URL in .env or code if needed")
print("3. Run the microphone example: python examples/microphone/main.py")
print("4. For microphone example, install: pip install pyaudio python-dotenv")
