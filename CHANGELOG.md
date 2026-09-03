# Changelog

## 0.2.1 — 2026-09-03

### Added

- `Finalize` and `CloseStream` control message models.
- `send_finalize()` and `send_close_stream()` on sync/async realtime socket clients.
- `Results.from_finalize` for finalize-flush responses (Deepgram parity).

## 0.2.0 — 2026-08-29

Deepgram-v7-style restructure of the SDK: context-manager `connect()`,
individual keyword options, typed pydantic response models, sync + async
twins, and a cleaned-up package layout.

### Breaking changes

The API namespace now follows Deepgram's listen/speak layout:
`client.listen.v1` for realtime streaming, `client.listen.batch.v1` for batch
jobs. A `client.speak` namespace (TTS) and `client.manage` (API keys/projects)
will be added when those endpoints land. The websocket connect layer lives in
`speechcortex.transport`, and user-facing helpers (`Microphone`) in
`speechcortex.helpers`.

| Old (0.1.x) | New (0.2.0) |
|---|---|
| `conn = client.transcribe.realtime(); conn.on(...); conn.start(RealtimeOptions(...)); conn.send(b); conn.finish()` | `with client.listen.v1.connect(...) as conn:` — context exit closes the connection |
| `client.transcribe.batch()` (async) | `client.listen.batch.v1` (property); sync twin added |
| `LiveTranscriptionEvents.Transcript/Metadata/...` with `(self, result=..., **kwargs)` handlers | `EventType.MESSAGE` with single-argument handlers; discriminate with `isinstance(message, Results)` |
| `conn.send(data)` returning `bool` (silent `False` before connect) | `conn.send_media(data)` — raises if the socket is closed |
| `conn.keep_alive()` + auto keep-alive thread | explicit `conn.send_keep_alive()`; no background threads |
| `RealtimeOptions(...)` / `LiveOptions` / `extras=` | individual keyword arguments + `extra=` dict |
| realtime `model` defaulted to `zeus-v1` | `model` defaults to `cove` |
| `start_of_turn` always a default `TurnInfo()` | `start_of_turn`/`end_of_turn` are `None` when the server omits them — check before use |
| dataclass_json response models | pydantic v2 models (unknown server fields preserved) |
| `SpeechCortexApiError(message, status)` | `ApiError(status_code=..., headers=..., body=...)` with credential redaction |
| `SpeechCortexClientOptions` | `ClientOptions` (same env vars) |
| `client.listen.websocket.v("1")`, `SpeechCortex` alias, `TranscriptionEvents` alias | removed |
| `BatchOptions` / `TranscriptionConfig` dataclasses | keyword arguments; `wait_for_completion(job_id, polling_interval=3.0, timeout=None)` |
| `Unhandled` event | removed — unknown message types arrive on `MESSAGE` as raw dicts |
| `SpeechCortexWebSocketError`, vendored `verboselogs`, `LiveTranscriptionEvents` | removed — std `logging` on the `speechcortex` logger |

### Fixed

- Booleans in query strings are now consistently lowercase (`"true"`/`"false"`); previously mixed with `"True"`.
- Batch file uploads infer the multipart content type from the file extension instead of hardcoding `audio/mpeg`.
- Version is single-sourced in `speechcortex/version.py` (was duplicated in three places).
- Batch response parsing deduplicated; UUID/timestamp parsing via one pydantic validator.

### Added

- `AsyncSpeechCortexClient` and async twins for realtime and batch clients.
- `RequestOptions` (`timeout`, `additional_headers`, `additional_query_parameters`) on every method.
- Real test suite (`pytest`, in-process websocket server, respx-mocked batch endpoints).
- `py.typed` (PEP 561) so type checkers use the SDK's annotations.

### Internal

- Realtime client no longer spawns a background thread/asyncio loop; sync twin uses `websockets.sync`, async twin uses `websockets.asyncio`.
- Batch client uses `httpx` instead of aiohttp/aiofiles.
- Auth header construction centralized; realtime keeps `Authorization: Basic`, batch keeps `X-API-Key` (server contract).
