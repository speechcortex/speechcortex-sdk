# Copyright 2024 SpeechCortex SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

"""
Async batch transcription client for SpeechCortex SDK.

This client provides a pure async interface for post-call/batch transcription,
allowing users to submit audio files or presigned URLs, poll for status, and
retrieve transcription results using aiohttp.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Union
from uuid import UUID

import aiohttp
import aiofiles

from ....options import SpeechCortexClientOptions
from ....errors import SpeechCortexError, SpeechCortexApiKeyError
from .options import BatchOptions, TranscriptionConfig
from .response import JobDetails, TranscriptionResult, TranscriptionStatus
from .exceptions import (
    BatchError,
    JobNotFoundError,
    JobFailedError,
    TranscriptionNotReadyError,
    BatchTimeoutError,
)


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class BatchClient:
    """
    Async client for SpeechCortex batch/post-call transcription.

    This client provides a pure async interface for submitting transcription jobs,
    polling for status, and retrieving results. It uses aiohttp for non-blocking
    HTTP communication.

    Supports async context manager for automatic resource cleanup.

    Example:
        >>> from speechcortex import SpeechCortexClient
        >>>
        >>> client = SpeechCortexClient(api_key="your_key")
        >>> batch = client.transcribe.batch()
        >>>
        >>> async with batch:
        ...     job = await batch.submit_job(
        ...         presigned_url="https://example.com/audio.mp3",
        ...         language="en-US"
        ...     )
        ...     result = await batch.wait_for_completion(job.job_id)
        ...     print(result.transcription)
    """

    def __init__(self, config: SpeechCortexClientOptions) -> None:
        """
        Initialize the batch transcription client.

        Args:
            config: SpeechCortexClientOptions containing API key, URL, etc.

        Raises:
            SpeechCortexError: If config is None.
            SpeechCortexApiKeyError: If API key is missing.
        """
        if config is None:
            raise SpeechCortexError("Config is required")

        if not config.api_key:
            raise SpeechCortexApiKeyError("API key is required for batch transcription")

        self._config = config
        self._api_key = config.api_key

        # Derive the REST base URL from the config URL
        # Config URL may be wss:// for realtime; we need https:// for REST
        raw_url = config.url.rstrip("/")
        if raw_url.startswith("wss://"):
            raw_url = raw_url.replace("wss://", "https://", 1)
        elif raw_url.startswith("ws://"):
            raw_url = raw_url.replace("ws://", "http://", 1)
        self._base_url = raw_url

        # Batch API path
        self._batch_path = config.batch_path

        # Session is lazily created
        self._session: Optional[aiohttp.ClientSession] = None
        self._closed = False

        logger.debug(
            "BatchClient initialized (base_url=%s, batch_path=%s)",
            self._base_url,
            self._batch_path,
        )

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------
    async def __aenter__(self) -> BatchClient:
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with automatic cleanup."""
        await self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def submit_job(
        self,
        presigned_url: Optional[str] = None,
        audio_file: Optional[Union[str, Path, BinaryIO, bytes]] = None,
        config: Optional[TranscriptionConfig] = None,
        **kwargs: Any,
    ) -> JobDetails:
        """
        Submit a transcription job.

        Either presigned_url or audio_file must be provided, but not both.

        Args:
            presigned_url: Presigned URL to audio file (S3, etc.)
            audio_file: Audio file path, file-like object, or bytes.
            config: TranscriptionConfig with transcription parameters.
            **kwargs: Additional transcription parameters (language, model, etc.)

        Returns:
            JobDetails object with job_id and initial status.

        Raises:
            BatchError: If job submission fails.
            SpeechCortexApiKeyError: If API key is invalid.
            ValueError: If neither or both of presigned_url / audio_file are provided.
        """
        if presigned_url and audio_file:
            raise ValueError("Cannot specify both presigned_url and audio_file")
        if not presigned_url and not audio_file:
            raise ValueError("Must provide either presigned_url or audio_file")

        # Build transcription config
        if config is None:
            config = TranscriptionConfig()

        # Override config with kwargs
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        query_params = config.to_query_params()

        try:
            if presigned_url:
                return await self._submit_presigned_url(presigned_url, query_params)
            else:
                return await self._submit_file_upload(audio_file, query_params)  # type: ignore[arg-type]
        except SpeechCortexApiKeyError:
            raise
        except BatchError:
            raise
        except Exception as e:
            raise BatchError(f"Failed to submit job: {e}") from e

    async def get_status(self, job_id: Union[str, UUID]) -> TranscriptionStatus:
        """
        Get the current status of a transcription job.

        Args:
            job_id: Job identifier (UUID string or UUID object).

        Returns:
            TranscriptionStatus object with current status.

        Raises:
            JobNotFoundError: If job is not found.
            BatchError: If request fails.
        """
        job_id_str = str(job_id)
        url = f"{self._base_url}{self._batch_path}/status/{job_id_str}"

        logger.debug("Getting status for job: %s", job_id_str)

        try:
            data = await self._request("GET", url)
            return TranscriptionStatus.from_dict(data)
        except JobNotFoundError:
            raise
        except Exception as e:
            raise BatchError(f"Failed to get status: {e}") from e

    async def get_transcription(self, job_id: Union[str, UUID]) -> TranscriptionResult:
        """
        Get the transcription result for a completed job.

        Args:
            job_id: Job identifier (UUID string or UUID object).

        Returns:
            TranscriptionResult object with transcription data.

        Raises:
            JobNotFoundError: If job is not found.
            TranscriptionNotReadyError: If job is not completed yet.
            JobFailedError: If job failed.
            BatchError: If request fails.
        """
        job_id_str = str(job_id)
        url = f"{self._base_url}{self._batch_path}/get_transcription/{job_id_str}"

        logger.debug("Getting transcription for job: %s", job_id_str)

        try:
            data = await self._request("GET", url, allow_202=True)

            # 202 means job is not ready yet (handled via status code in _request)
            if data.get("_status_code") == 202:
                status = data.get("status", "unknown")
                raise TranscriptionNotReadyError(job_id_str, status)

            # Check if job failed
            if data.get("status", "").upper() == "FAILED":
                error_msg = data.get("message", "Transcription failed")
                raise JobFailedError(job_id_str, error_msg)

            return TranscriptionResult.from_dict(data)

        except (JobNotFoundError, TranscriptionNotReadyError, JobFailedError):
            raise
        except BatchError:
            raise
        except Exception as e:
            raise BatchError(f"Failed to get transcription: {e}") from e

    async def wait_for_completion(
        self,
        job_id: Union[str, UUID],
        options: Optional[BatchOptions] = None,
        **kwargs: Any,
    ) -> TranscriptionResult:
        """
        Wait for a job to complete and return the result.

        This method polls the job status at regular intervals until the job
        completes or fails. Uses asyncio.wait_for for timeout handling.

        Args:
            job_id: Job identifier (UUID string or UUID object).
            options: BatchOptions with polling configuration.
            **kwargs: Additional options (polling_interval, timeout).

        Returns:
            TranscriptionResult object with transcription data.

        Raises:
            BatchTimeoutError: If job doesn't complete within timeout.
            JobFailedError: If job fails.
            BatchError: If request fails.
        """
        if options is None:
            options = BatchOptions()

        polling_interval = kwargs.get("polling_interval", options.polling_interval)
        timeout = kwargs.get("timeout", options.timeout)
        job_id_str = str(job_id)

        logger.info(
            "Waiting for job completion: %s (polling_interval=%.1fs, timeout=%s)",
            job_id_str,
            polling_interval,
            timeout or "none",
        )

        try:
            await asyncio.wait_for(
                self._poll_job_status(job_id_str, polling_interval),
                timeout=timeout,
            )
            return await self.get_transcription(job_id_str)

        except asyncio.TimeoutError:
            raise BatchTimeoutError(job_id_str, timeout) from None

    async def transcribe(
        self,
        presigned_url: Optional[str] = None,
        audio_file: Optional[Union[str, Path, BinaryIO, bytes]] = None,
        config: Optional[TranscriptionConfig] = None,
        options: Optional[BatchOptions] = None,
        **kwargs: Any,
    ) -> TranscriptionResult:
        """
        Convenience method: submit job and wait for completion.

        Combines submit_job() and wait_for_completion() in a single call.

        Args:
            presigned_url: Presigned URL to audio file.
            audio_file: Audio file path, file-like object, or bytes.
            config: TranscriptionConfig with transcription parameters.
            options: BatchOptions with polling configuration.
            **kwargs: Additional parameters (language, model, polling_interval, timeout, etc.)

        Returns:
            TranscriptionResult object with transcription data.

        Raises:
            BatchError: If any step fails.
        """
        # Extract polling options from kwargs
        polling_kwargs: Dict[str, Any] = {}
        for key in ("polling_interval", "timeout"):
            if key in kwargs:
                polling_kwargs[key] = kwargs.pop(key)

        # Submit job
        job = await self.submit_job(
            presigned_url=presigned_url,
            audio_file=audio_file,
            config=config,
            **kwargs,
        )

        logger.debug("Waiting for job completion (job_id=%s)", job.job_id)

        # Wait for completion
        result = await self.wait_for_completion(
            job.job_id,
            options=options,
            **polling_kwargs,
        )

        logger.info("Transcription completed successfully (job_id=%s)", job.job_id)
        return result

    async def close(self) -> None:
        """
        Close the HTTP session and cleanup resources.

        Safe to call multiple times.
        """
        if self._session and not self._closed:
            try:
                await self._session.close()
            except Exception:
                pass  # best-effort cleanup
            finally:
                self._session = None
                self._closed = True
                logger.debug("BatchClient session closed")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _ensure_session(self) -> None:
        """Create aiohttp session lazily."""
        if self._session is None and not self._closed:
            timeout = aiohttp.ClientTimeout(total=300.0, connect=30.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
            logger.debug("aiohttp session created")

    def _get_headers(self) -> Dict[str, str]:
        """Build common request headers."""
        return {
            "X-API-Key": self._api_key,
            "User-Agent": (
                f"speechcortex-sdk python/{sys.version_info.major}.{sys.version_info.minor}"
            ),
        }

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[aiohttp.FormData] = None,
        allow_202: bool = False,
    ) -> Dict[str, Any]:
        """
        Send an HTTP request and return JSON response.

        Args:
            method: HTTP method (GET, POST).
            url: Full URL.
            params: Query parameters.
            json_data: JSON body.
            form_data: Multipart form data.
            allow_202: If True, return 202 responses with _status_code marker.

        Returns:
            JSON response as dict.

        Raises:
            SpeechCortexApiKeyError: On 401.
            JobNotFoundError: On 404.
            BatchError: On other errors.
        """
        await self._ensure_session()
        assert self._session is not None

        headers = self._get_headers()

        kwargs: Dict[str, Any] = {"headers": headers, "params": params}
        if json_data is not None:
            kwargs["json"] = json_data
        if form_data is not None:
            # Don't set Content-Type for multipart — aiohttp handles it
            kwargs["data"] = form_data

        logger.debug("HTTP %s %s", method, url)

        try:
            async with self._session.request(method, url, **kwargs) as response:
                if response.status == 401:
                    raise SpeechCortexApiKeyError("Invalid API key")

                if response.status == 404:
                    raise JobNotFoundError("unknown", "Resource not found")

                if response.status == 202 and allow_202:
                    data = await response.json()
                    data["_status_code"] = 202
                    return data

                if response.status >= 400:
                    error_text = await response.text()
                    logger.error("HTTP %d: %s", response.status, error_text)
                    raise BatchError(f"HTTP {response.status}: {error_text}")

                return await response.json()

        except (SpeechCortexApiKeyError, JobNotFoundError, BatchError):
            raise
        except aiohttp.ClientError as e:
            raise BatchError(f"Request failed: {e}") from e
        except asyncio.TimeoutError:
            raise BatchError(f"Request timeout: {method} {url}") from None
        except Exception as e:
            raise BatchError(f"Unexpected error: {e}") from e

    async def _submit_presigned_url(
        self, presigned_url: str, query_params: Dict[str, Any]
    ) -> JobDetails:
        """Submit job with presigned URL."""
        url = f"{self._base_url}{self._batch_path}/transcribe"

        logger.debug("Submitting job with presigned URL: %s", url)

        data = await self._request(
            "POST",
            url,
            params=query_params,
            json_data={"presigned_url": presigned_url},
        )

        if "job_id" not in data:
            error_msg = data.get("message", "No job_id in response")
            raise BatchError(f"Job submission failed: {error_msg}")

        logger.info("Job submitted successfully: %s", data.get("job_id"))
        return JobDetails.from_dict(data)

    async def _submit_file_upload(
        self,
        audio_file: Union[str, Path, BinaryIO, bytes],
        query_params: Dict[str, Any],
    ) -> JobDetails:
        """Submit job with file upload."""
        url = f"{self._base_url}{self._batch_path}/transcribe/upload"

        logger.debug("Submitting job with file upload: %s", url)

        form = aiohttp.FormData()

        if isinstance(audio_file, (str, Path)):
            file_path = Path(audio_file)
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")

            async with aiofiles.open(file_path, "rb") as f:
                file_content = await f.read()
            form.add_field(
                "audio_file",
                file_content,
                filename=file_path.name,
                content_type="audio/mpeg",
            )
        elif isinstance(audio_file, bytes):
            form.add_field(
                "audio_file",
                audio_file,
                filename="audio.mp3",
                content_type="audio/mpeg",
            )
        else:
            # File-like object
            content = audio_file.read()
            filename = getattr(audio_file, "name", "audio.mp3")
            if hasattr(filename, "split"):
                filename = os.path.basename(filename)
            form.add_field(
                "audio_file",
                content,
                filename=filename,
                content_type="audio/mpeg",
            )

        data = await self._request(
            "POST",
            url,
            params=query_params,
            form_data=form,
        )

        if "job_id" not in data:
            error_msg = data.get("message", "No job_id in response")
            raise BatchError(f"Job submission failed: {error_msg}")

        logger.info("Job submitted successfully: %s", data.get("job_id"))
        return JobDetails.from_dict(data)

    async def _poll_job_status(self, job_id: str, polling_interval: float) -> None:
        """Poll job status until completion or failure."""
        logger.debug(
            "Starting status polling for job_id=%s (interval=%.1fs)",
            job_id,
            polling_interval,
        )
        poll_count = 0

        while True:
            poll_count += 1
            status = await self.get_status(job_id)
            status_upper = status.status.upper()

            logger.debug(
                "Job %s status: %s (poll #%d)", job_id, status_upper, poll_count
            )

            if status_upper == "COMPLETED":
                logger.info("Job completed (job_id=%s, polls=%d)", job_id, poll_count)
                return

            if status_upper == "FAILED":
                error_msg = status.error_message or "Job failed"
                raise JobFailedError(job_id, error_msg)

            await asyncio.sleep(polling_interval)
