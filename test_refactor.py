#!/usr/bin/env python3
"""
Quick test to verify the refactoring works correctly.
Tests the new transcribe.realtime() API structure.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from speechcortex import (
    SpeechCortexClient,
    RealtimeOptions,
    TranscriptionEvents,
)


def test_client_api():
    """Test that the new API structure is accessible"""
    print("Testing SpeechCortex SDK refactored API...\n")
    
    # Test 1: Client initialization
    print("✓ Test 1: Client initialization")
    try:
        client = SpeechCortexClient()
        print("  Client created successfully")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        assert False, e
    
    # Test 2: Access transcribe router
    print("\n✓ Test 2: Access transcribe router")
    try:
        transcribe = client.transcribe
        print(f"  Transcribe router: {type(transcribe).__name__}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        assert False, e
    
    # Test 3: Access realtime client
    print("\n✓ Test 3: Access realtime client")
    try:
        connection = client.transcribe.realtime()
        print(f"  Realtime client: {type(connection).__name__}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        assert False, e
    
    # Test 4: Create RealtimeOptions
    print("\n✓ Test 4: Create RealtimeOptions")
    try:
        options = RealtimeOptions(
            model="zeus-v1",
            language="en-US",
            smart_format=True,
            punctuate=True,
        )
        print(f"  Options created: model={options.model}, language={options.language}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        assert False, e
    
    # Test 5: Access TranscriptionEvents enum
    print("\n✓ Test 5: Access TranscriptionEvents enum")
    try:
        events = [
            TranscriptionEvents.Open,
            TranscriptionEvents.Transcript,
            TranscriptionEvents.Metadata,
            TranscriptionEvents.Close,
            TranscriptionEvents.Error,
        ]
        print(f"  Events accessible: {len(events)} events")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        assert False, e
    
    print("\n" + "="*60)
    print("✅ All tests passed! Refactoring successful!")
    print("="*60)
    print("\nAPI usage:")
    print("  connection = client.transcribe.realtime()")
    print("  options = RealtimeOptions(...)")
    print("  connection.on(TranscriptionEvents.Transcript, handler)")
    print("="*60)
    # All assertions passed
    return None


if __name__ == "__main__":
    test_client_api()
    sys.exit(0)
