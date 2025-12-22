# Copyright 2024 Zeus SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

import json
import logging
import threading
import websockets
import asyncio
from typing import Dict, Optional, Callable, Any
from urllib.parse import urlencode

from ....utils import verboselogs
from ....options import ZeusClientOptions
from ....errors import ZeusError, ZeusWebSocketError
from ..enums import LiveTranscriptionEvents
from .response import (
    OpenResponse,
    LiveResultResponse,
    MetadataResponse,
    SpeechStartedResponse,
    UtteranceEndResponse,
    CloseResponse,
    ErrorResponse,
    UnhandledResponse,
)
from .options import RealtimeOptions


class RealtimeClient:
    """
    WebSocket client for Zeus real-time transcription.
    
    This client handles WebSocket connections to the Zeus API for live audio transcription.
    """

    def __init__(self, config: ZeusClientOptions):
        if config is None:
            raise ZeusError("Config is required")

        self._logger = verboselogs.VerboseLogger(__name__)
        self._logger.addHandler(logging.StreamHandler())
        self._logger.setLevel(config.verbose)

        self._config = config
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._event_handlers: Dict[LiveTranscriptionEvents, list] = {
            event: [] for event in LiveTranscriptionEvents.__members__.values()
        }
        
        self._exit_event = threading.Event()
        self._keep_alive_thread: Optional[threading.Thread] = None
        self._receive_thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def on(self, event: LiveTranscriptionEvents, handler: Callable) -> None:
        """
        Register an event handler for a specific event type.
        
        Args:
            event: The event type to listen for
            handler: Callback function to handle the event
        """
        self._logger.info("event subscribed: %s", event)
        if event in LiveTranscriptionEvents.__members__.values() and callable(handler):
            self._event_handlers[event].append(handler)

    def _emit(self, event: LiveTranscriptionEvents, *args, **kwargs) -> None:
        """Emit an event to all registered handlers"""
        for handler in self._event_handlers[event]:
            try:
                handler(self, *args, **kwargs)
            except Exception as e:
                self._logger.error("Error in event handler: %s", e)

    def start(self, options: Optional[RealtimeOptions] = None, **kwargs) -> bool:
        """
        Start the WebSocket connection.
        
        Args:
            options: RealtimeOptions for configuring the transcription
            **kwargs: Additional keyword arguments
            
        Returns:
            bool: True if connection started successfully
        """
        self._logger.debug("RealtimeClient.start ENTER")

        if options is None:
            options = RealtimeOptions()

        if not options.check():
            raise ZeusError("Invalid LiveOptions")

        try:
            # Build WebSocket URL
            params = options.to_dict()
            query_string = urlencode(params)

            # Construct WebSocket URL: base URL + realtime path (configurable) + query params
            # The base URL from config should already have the protocol (wss:// or ws://)
            realtime_path = getattr(self._config, "realtime_path", "/transcribe/realtime")
            url = f"{self._config.url}{realtime_path}?{query_string}"
            
            self._logger.info("Connecting to: %s", url)

            # Start asyncio loop in a separate thread
            self._loop = asyncio.new_event_loop()
            self._receive_thread = threading.Thread(
                target=self._run_websocket, 
                args=(url,)
            )
            self._receive_thread.start()

            # Start keep-alive thread if enabled
            if self._config.is_keep_alive_enabled():
                self._logger.notice("keepalive is enabled")
                self._keep_alive_thread = threading.Thread(target=self._keep_alive)
                self._keep_alive_thread.start()

            self._logger.notice("WebSocket connection started")
            return True

        except Exception as e:
            self._logger.error("Failed to start WebSocket: %s", e)
            return False

    def _run_websocket(self, url: str):
        """Run the WebSocket connection in the asyncio loop"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_and_listen(url))

    async def _connect_and_listen(self, url: str):
        """Connect to WebSocket and listen for messages"""
        try:
            # Use headers from config (which already includes proper auth)
            headers = self._config.headers.copy() if self._config.headers else {}

            async with websockets.connect(url, additional_headers=headers) as websocket:
                self._websocket = websocket
                self._logger.notice("WebSocket connected")

                # Emit Open event
                open_response = OpenResponse()
                self._emit(LiveTranscriptionEvents.Open, open=open_response)

                # Listen for messages
                close_code = None
                close_reason = None
                
                while not self._exit_event.is_set():
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=1.0
                        )
                        self._process_message(message)
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed as e:
                        close_code = e.code if hasattr(e, 'code') else None
                        close_reason = e.reason if hasattr(e, 'reason') else None
                        self._logger.notice(f"WebSocket connection closed: code={close_code}, reason={close_reason}")
                        break

        except Exception as e:
            self._logger.error("WebSocket error: %s", e)
            error_code = None
            if hasattr(e, 'code'):
                error_code = e.code
            error_response = ErrorResponse(
                type="Error",
                code=error_code,
                message=str(e),
                description="WebSocket connection error"
            )
            self._emit(LiveTranscriptionEvents.Error, error=error_response)
        finally:
            self._websocket = None
            close_response = CloseResponse(
                code=close_code if 'close_code' in locals() else None,
                reason=close_reason if 'close_reason' in locals() else None
            )
            self._emit(LiveTranscriptionEvents.Close, close=close_response)

    def _process_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            if not message:
                return

            data = json.loads(message)
            response_type = data.get("type")
            
            if response_type == "Results":
                result = LiveResultResponse.from_json(message)
                self._emit(LiveTranscriptionEvents.Transcript, result=result)
            elif response_type == "Metadata":
                metadata = MetadataResponse.from_json(message)
                self._emit(LiveTranscriptionEvents.Metadata, metadata=metadata)
            elif response_type == "SpeechStarted":
                speech_started = SpeechStartedResponse.from_json(message)
                self._emit(LiveTranscriptionEvents.SpeechStarted, speech_started=speech_started)
            elif response_type == "UtteranceEnd":
                utterance_end = UtteranceEndResponse.from_json(message)
                self._emit(LiveTranscriptionEvents.UtteranceEnd, utterance_end=utterance_end)
            elif response_type == "Error":
                error = ErrorResponse.from_json(message)
                self._emit(LiveTranscriptionEvents.Error, error=error)
            else:
                self._logger.warning("Unknown message type: %s", response_type)
                unhandled = UnhandledResponse(type="Unhandled", raw=message)
                self._emit(LiveTranscriptionEvents.Unhandled, unhandled=unhandled)

        except Exception as e:
            self._logger.error("Error processing message: %s", e)
            error_response = ErrorResponse(
                type="Error",
                message=str(e),
                description="Error processing message"
            )
            self._emit(LiveTranscriptionEvents.Error, error=error_response)

    def send(self, data: bytes) -> bool:
        """
        Send audio data to the WebSocket.
        
        Args:
            data: Audio data bytes
            
        Returns:
            bool: True if data was sent successfully
        """
        if self._websocket is None:
            self._logger.error("WebSocket not connected")
            return False

        try:
            future = asyncio.run_coroutine_threadsafe(
                self._websocket.send(data),
                self._loop
            )
            future.result(timeout=5.0)
            return True
        except Exception as e:
            self._logger.error("Error sending data: %s", e)
            return False

    def keep_alive(self) -> bool:
        """Send a keep-alive message"""
        if self._websocket is None:
            return False

        try:
            message = json.dumps({"type": "KeepAlive"})
            future = asyncio.run_coroutine_threadsafe(
                self._websocket.send(message),
                self._loop
            )
            future.result(timeout=5.0)
            self._logger.debug("KeepAlive sent")
            return True
        except Exception as e:
            self._logger.error("Error sending keep-alive: %s", e)
            return False

    def _keep_alive(self):
        """Keep-alive thread function"""
        while not self._exit_event.is_set():
            self._exit_event.wait(timeout=5.0)
            if not self._exit_event.is_set():
                self.keep_alive()

    def finish(self) -> bool:
        """
        Close the WebSocket connection and clean up resources.
        
        Returns:
            bool: True if cleanup was successful
        """
        self._logger.debug("ListenWebSocketClient.finish ENTER")

        self._exit_event.set()

        # Send close frame
        if self._websocket:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._websocket.close(),
                    self._loop
                )
                future.result(timeout=5.0)
            except Exception as e:
                self._logger.error("Error closing websocket: %s", e)

        # Wait for threads
        if self._receive_thread:
            self._receive_thread.join(timeout=5.0)
        if self._keep_alive_thread:
            self._keep_alive_thread.join(timeout=5.0)

        # Stop the loop
        if self._loop:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except:
                pass

        self._logger.notice("WebSocket connection closed")
        return True
