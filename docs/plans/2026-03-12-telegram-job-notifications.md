# Telegram Job Notifications Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace "Working on it..." with a ❤️ Telegram reaction, add 15-min status pings while a LangGraph run is active, and prepend a "✅ Done" message before each agent response.

**Architecture:** `TelegramChannel` uses `set_message_reaction` instead of sending text. `ChannelManager` owns an `_active_runs` dict populated at the start/end of each `_handle_chat` call and a background `_status_ticker` asyncio task that publishes outbound pings every 15 min when runs are outstanding. On completion, `_handle_chat` publishes a short prefix message before the normal response.

**Tech Stack:** `python-telegram-bot` v20+, `asyncio`, existing `MessageBus`/`OutboundMessage` infrastructure.

---

## Task 1: Replace "Working on it..." with ❤️ reaction

**Files:**
- Modify: `backend/src/channels/telegram.py`
- Modify: `backend/tests/test_channels.py` (add new test class `TestTelegramReaction`)

### Step 1: Write the failing test

Add a new class `TestTelegramReaction` in `backend/tests/test_channels.py`, before `TestTelegramSendRetry`:

```python
class TestTelegramReaction:
    def test_running_reaction_calls_set_message_reaction(self):
        from src.channels.telegram import TelegramChannel

        async def go():
            bus = MessageBus()
            ch = TelegramChannel(bus=bus, config={"bot_token": "test-token"})

            mock_app = MagicMock()
            mock_bot = AsyncMock()
            mock_bot.set_message_reaction = AsyncMock(return_value=None)
            mock_app.bot = mock_bot
            ch._application = mock_app

            await ch._send_running_reaction("12345", 42)

            mock_bot.set_message_reaction.assert_called_once()
            call_kwargs = mock_bot.set_message_reaction.call_args[1]
            assert call_kwargs["chat_id"] == 12345
            assert call_kwargs["message_id"] == 42
            # Must not send a text message
            mock_bot.send_message.assert_not_called()

        _run(go())

    def test_running_reaction_silently_ignores_errors(self):
        from src.channels.telegram import TelegramChannel

        async def go():
            bus = MessageBus()
            ch = TelegramChannel(bus=bus, config={"bot_token": "test-token"})

            mock_app = MagicMock()
            mock_bot = AsyncMock()
            mock_bot.set_message_reaction = AsyncMock(side_effect=Exception("reactions not supported"))
            mock_app.bot = mock_bot
            ch._application = mock_app

            # Should not raise
            await ch._send_running_reaction("12345", 42)

        _run(go())
```

### Step 2: Run test to verify it fails

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py::TestTelegramReaction -v
```

Expected: FAIL with `AttributeError: '_send_running_reaction' not found`

### Step 3: Implement the change in `telegram.py`

In `backend/src/channels/telegram.py`:

**a)** Rename `_send_running_reply` → `_send_running_reaction` and replace the body:

```python
async def _send_running_reaction(self, chat_id: str, message_id: int) -> None:
    """React with ❤️ to the user's message to indicate processing."""
    if not self._application:
        return
    try:
        from telegram import ReactionTypeEmoji

        bot = self._application.bot
        await bot.set_message_reaction(
            chat_id=int(chat_id),
            message_id=message_id,
            reaction=[ReactionTypeEmoji(emoji="❤")],
        )
        logger.info("[Telegram] ❤️ reaction sent in chat=%s msg=%s", chat_id, message_id)
    except Exception:
        logger.debug("[Telegram] reaction not supported in chat=%s, skipping", chat_id)
```

**b)** Update call sites in `_cmd_generic` (line ~193) and `_on_text` (line ~228):

Change:
```python
asyncio.run_coroutine_threadsafe(self._send_running_reply(chat_id, update.message.message_id), self._main_loop)
```
To:
```python
asyncio.run_coroutine_threadsafe(self._send_running_reaction(chat_id, update.message.message_id), self._main_loop)
```

(Do this in both `_cmd_generic` and `_on_text`.)

### Step 4: Run tests to verify they pass

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py::TestTelegramReaction tests/test_channels.py::TestTelegramSendRetry -v
```

Expected: All PASS

### Step 5: Run the full test suite

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py -v
```

Expected: All PASS

### Step 6: Commit

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/src/channels/telegram.py backend/tests/test_channels.py
git commit -m "feat(telegram): replace 'Working on it...' with ❤️ message reaction"
```

---

## Task 2: Add active run tracking to `ChannelManager`

**Files:**
- Modify: `backend/src/channels/manager.py`
- Modify: `backend/tests/test_channels.py` (add `TestRunTracking` class + update existing tests)

### Step 1: Write the failing tests

Add `TestRunTracking` class in `backend/tests/test_channels.py`, after `TestHandleChatWithArtifacts`:

```python
class TestRunTracking:
    def test_run_registered_and_deregistered(self):
        """Active run is added to _active_runs during _handle_chat and removed after."""
        from src.channels.manager import ChannelManager

        async def go():
            bus = MessageBus()
            store = ChannelStore(path=Path(tempfile.mkdtemp()) / "store.json")
            manager = ChannelManager(bus=bus, store=store)

            run_started = asyncio.Event()
            run_released = asyncio.Event()

            async def slow_wait(*args, **kwargs):
                run_started.set()
                await run_released.wait()
                return {"messages": [{"type": "ai", "content": "done"}]}

            mock_client = _make_mock_langgraph_client()
            mock_client.runs.wait = slow_wait
            manager._client = mock_client

            bus.subscribe_outbound(lambda _: None)
            await manager.start()

            inbound = InboundMessage(channel_name="test", chat_id="c1", user_id="u1", text="hi")
            await bus.publish_inbound(inbound)

            # Wait for run to start
            await asyncio.wait_for(run_started.wait(), timeout=5.0)

            # Should have one active run
            assert len(manager._active_runs) == 1

            # Let the run finish
            run_released.set()
            await _wait_for(lambda: len(manager._active_runs) == 0)

            await manager.stop()

        _run(go())

    def test_no_runs_when_idle(self):
        from src.channels.manager import ChannelManager

        async def go():
            bus = MessageBus()
            store = ChannelStore(path=Path(tempfile.mkdtemp()) / "store.json")
            manager = ChannelManager(bus=bus, store=store)
            await manager.start()

            assert len(manager._active_runs) == 0

            await manager.stop()

        _run(go())
```

### Step 2: Run test to verify it fails

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py::TestRunTracking -v
```

Expected: FAIL with `AttributeError: 'ChannelManager' object has no attribute '_active_runs'`

### Step 3: Add `_RunInfo` dataclass and `_active_runs` to `ChannelManager`

In `backend/src/channels/manager.py`:

**a)** Add imports at the top (after existing imports):

```python
from dataclasses import dataclass, field
from datetime import datetime
```

**b)** Add `_RunInfo` dataclass before `ChannelManager` class definition:

```python
@dataclass
class _RunInfo:
    """Tracks an active LangGraph run for status pings."""

    chat_id: str
    channel_name: str
    started_at: datetime = field(default_factory=datetime.now)
    last_ping_at: datetime | None = None
```

**c)** In `ChannelManager.__init__`, add after `self._task`:

```python
self._active_runs: dict[str, _RunInfo] = {}  # key: f"{channel}:{chat_id}:{topic_id}"
self._ticker_task: asyncio.Task | None = None
```

**d)** In `_handle_chat`, add run registration at the start (after `thread_id` is determined) and deregistration after `runs.wait()` completes:

At the start of `_handle_chat`, after the thread_id logic:
```python
# Register this run for status tracking
run_key = f"{msg.channel_name}:{msg.chat_id}:{msg.topic_id or ''}"
self._active_runs[run_key] = _RunInfo(chat_id=msg.chat_id, channel_name=msg.channel_name)
```

After `result = await client.runs.wait(...)`:
```python
# Deregister run — it has completed
self._active_runs.pop(run_key, None)
```

Make sure `run_key` is defined before the `runs.wait()` call and that `self._active_runs.pop(run_key, None)` is called even if an exception occurs (use try/finally):

```python
run_key = f"{msg.channel_name}:{msg.chat_id}:{msg.topic_id or ''}"
self._active_runs[run_key] = _RunInfo(chat_id=msg.chat_id, channel_name=msg.channel_name)
try:
    result = await client.runs.wait(
        thread_id,
        self._assistant_id,
        input={"messages": [{"role": "human", "content": msg.text}]},
        config={"recursion_limit": 100},
        context={
            "thread_id": thread_id,
            "thinking_enabled": True,
            "is_plan_mode": False,
            "subagent_enabled": False,
        },
    )
finally:
    self._active_runs.pop(run_key, None)
```

Note: the response building and outbound publish logic stays AFTER the try/finally (it reads `result` set before the finally).

Actually, the structure should be:

```python
run_key = f"{msg.channel_name}:{msg.chat_id}:{msg.topic_id or ''}"
self._active_runs[run_key] = _RunInfo(chat_id=msg.chat_id, channel_name=msg.channel_name)
try:
    result = await client.runs.wait(...)
finally:
    self._active_runs.pop(run_key, None)

# Response handling continues here (result is still in scope)
response_text = _extract_response_text(result)
...
```

### Step 4: Run tests to verify they pass

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py::TestRunTracking tests/test_channels.py::TestChannelManager -v
```

Expected: All PASS

### Step 5: Run full test suite

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py -v
```

Expected: All PASS

### Step 6: Commit

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/src/channels/manager.py backend/tests/test_channels.py
git commit -m "feat(manager): add active run tracking with _RunInfo and _active_runs"
```

---

## Task 3: Add 15-minute status ticker

**Files:**
- Modify: `backend/src/channels/manager.py`
- Modify: `backend/tests/test_channels.py` (add `TestStatusTicker` class)

### Step 1: Write the failing tests

Add `TestStatusTicker` class in `backend/tests/test_channels.py`, after `TestRunTracking`:

```python
class TestStatusTicker:
    def test_ticker_pings_when_run_exceeds_threshold(self):
        """Ticker sends a status ping when a run has been active past the threshold."""
        from datetime import timedelta

        from src.channels.manager import ChannelManager, _RunInfo

        async def go():
            bus = MessageBus()
            store = ChannelStore(path=Path(tempfile.mkdtemp()) / "store.json")
            manager = ChannelManager(bus=bus, store=store, status_ping_interval_seconds=0.1)

            outbound_received = []
            bus.subscribe_outbound(lambda msg: outbound_received.append(msg))

            await manager.start()

            # Manually inject an "old" active run (started 20 minutes ago)
            old_start = datetime.now() - timedelta(minutes=20)
            manager._active_runs["test:chat1:"] = _RunInfo(
                chat_id="chat1",
                channel_name="test",
                started_at=old_start,
                last_ping_at=None,
            )

            # Wait for the ticker to fire
            await _wait_for(lambda: len(outbound_received) >= 1, timeout=3.0)
            await manager.stop()

            assert len(outbound_received) >= 1
            msg = outbound_received[0]
            assert msg.chat_id == "chat1"
            assert msg.channel_name == "test"
            assert "⚙️" in msg.text
            assert "working" in msg.text.lower() or "min" in msg.text.lower()

        _run(go())

    def test_ticker_does_not_ping_for_new_runs(self):
        """Ticker skips runs that started less than 15 minutes ago."""
        from src.channels.manager import ChannelManager, _RunInfo

        async def go():
            bus = MessageBus()
            store = ChannelStore(path=Path(tempfile.mkdtemp()) / "store.json")
            manager = ChannelManager(bus=bus, store=store, status_ping_interval_seconds=0.05)

            outbound_received = []
            bus.subscribe_outbound(lambda msg: outbound_received.append(msg))

            await manager.start()

            # Inject a fresh run (just started)
            manager._active_runs["test:chat1:"] = _RunInfo(
                chat_id="chat1",
                channel_name="test",
            )

            # Wait a bit — ticker should fire but not ping (run is too new)
            await asyncio.sleep(0.2)
            await manager.stop()

            assert len(outbound_received) == 0

        _run(go())

    def test_ticker_respects_15min_cooldown_between_pings(self):
        """Once pinged, ticker should not ping again for 15 minutes."""
        from datetime import timedelta

        from src.channels.manager import ChannelManager, _RunInfo

        async def go():
            bus = MessageBus()
            store = ChannelStore(path=Path(tempfile.mkdtemp()) / "store.json")
            manager = ChannelManager(bus=bus, store=store, status_ping_interval_seconds=0.05)

            outbound_received = []
            bus.subscribe_outbound(lambda msg: outbound_received.append(msg))

            await manager.start()

            # Inject old run that was pinged 5 minutes ago (not 15 yet)
            old_start = datetime.now() - timedelta(minutes=20)
            recent_ping = datetime.now() - timedelta(minutes=5)
            manager._active_runs["test:chat1:"] = _RunInfo(
                chat_id="chat1",
                channel_name="test",
                started_at=old_start,
                last_ping_at=recent_ping,
            )

            # Wait for multiple ticker cycles
            await asyncio.sleep(0.3)
            await manager.stop()

            # Should not have pinged (cooldown not expired)
            assert len(outbound_received) == 0

        _run(go())
```

Also add `from datetime import datetime` to imports in test file if not already present.

### Step 2: Run tests to verify they fail

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py::TestStatusTicker -v
```

Expected: FAIL with `TypeError: ChannelManager.__init__() got unexpected keyword argument 'status_ping_interval_seconds'`

### Step 3: Implement `_status_ticker` in `ChannelManager`

In `backend/src/channels/manager.py`:

**a)** Update `ChannelManager.__init__` to accept `status_ping_interval_seconds`:

```python
def __init__(
    self,
    bus: MessageBus,
    store: ChannelStore,
    *,
    max_concurrency: int = 5,
    langgraph_url: str = DEFAULT_LANGGRAPH_URL,
    gateway_url: str = DEFAULT_GATEWAY_URL,
    assistant_id: str = DEFAULT_ASSISTANT_ID,
    status_ping_interval_seconds: float = 60.0,
) -> None:
    ...
    self._status_ping_interval = status_ping_interval_seconds
    self._status_ping_threshold = 15 * 60  # 15 minutes in seconds
```

**b)** Update `start()` to launch the ticker:

```python
async def start(self) -> None:
    if self._running:
        return
    self._running = True
    self._semaphore = asyncio.Semaphore(self._max_concurrency)
    self._task = asyncio.create_task(self._dispatch_loop())
    self._ticker_task = asyncio.create_task(self._status_ticker())
    logger.info("ChannelManager started (max_concurrency=%d)", self._max_concurrency)
```

**c)** Update `stop()` to cancel the ticker:

```python
async def stop(self) -> None:
    self._running = False
    for task in (self._task, self._ticker_task):
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    self._task = None
    self._ticker_task = None
    logger.info("ChannelManager stopped")
```

**d)** Add `_status_ticker` method to `ChannelManager`:

```python
async def _status_ticker(self) -> None:
    """Background task that pings chats with long-running jobs every 15 minutes."""
    while self._running:
        try:
            await asyncio.sleep(self._status_ping_interval)
        except asyncio.CancelledError:
            break

        now = datetime.now()
        for run_key, info in list(self._active_runs.items()):
            elapsed_seconds = (now - info.started_at).total_seconds()
            since_last_ping = (now - info.last_ping_at).total_seconds() if info.last_ping_at else elapsed_seconds

            if elapsed_seconds >= self._status_ping_threshold and since_last_ping >= self._status_ping_threshold:
                elapsed_min = int(elapsed_seconds / 60)
                ping = OutboundMessage(
                    channel_name=info.channel_name,
                    chat_id=info.chat_id,
                    thread_id="",
                    text=f"⚙️ Still working — {elapsed_min}m elapsed.",
                )
                await self.bus.publish_outbound(ping)
                info.last_ping_at = now
                logger.info("[Manager] status ping sent to chat=%s (%dm elapsed)", info.chat_id, elapsed_min)
```

Add `from datetime import datetime` to imports in `manager.py` if not already present.

### Step 4: Run tests to verify they pass

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py::TestStatusTicker -v
```

Expected: All PASS

### Step 5: Run the full test suite

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py -v
```

Expected: All PASS

### Step 6: Commit

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/src/channels/manager.py backend/tests/test_channels.py
git commit -m "feat(manager): add 15-min status ticker for long-running LangGraph jobs"
```

---

## Task 4: Add completion prefix message + update existing tests

**Files:**
- Modify: `backend/src/channels/manager.py`
- Modify: `backend/tests/test_channels.py` (update `TestChannelManager.test_handle_chat_creates_thread` and artifact tests)

### Step 1: Update existing tests to expect 2 outbound messages

The completion prefix adds a message BEFORE the agent response. Update the following tests in `TestChannelManager` and `TestHandleChatWithArtifacts`:

**`test_handle_chat_creates_thread`** — change from expecting 1 outbound message to 2:

```python
await _wait_for(lambda: len(outbound_received) >= 2)
await manager.stop()

...

# Now expect 2 messages: prefix + response
assert len(outbound_received) == 2
assert "✅" in outbound_received[0].text
assert outbound_received[1].text == "Hello from agent!"
```

**`test_artifacts_appended_to_text`** — change from `>= 1` to `>= 2`, check index 1:

```python
await _wait_for(lambda: len(outbound_received) >= 2)
await manager.stop()

assert len(outbound_received) == 2
assert "Here is your report." in outbound_received[1].text
assert "report.md" in outbound_received[1].text
assert outbound_received[1].artifacts == ["/mnt/user-data/outputs/report.md"]
```

**`test_artifacts_only_no_text`** — same pattern, check index 1:

```python
await _wait_for(lambda: len(outbound_received) >= 2)
await manager.stop()

assert len(outbound_received) == 2
assert outbound_received[1].text != "(No response from agent)"
assert "output.csv" in outbound_received[1].text
assert outbound_received[1].artifacts == ["/mnt/user-data/outputs/output.csv"]
```

**`test_only_last_turn_artifacts_returned`** — update to expect 4 total (2 per turn), check indices 1 and 3:

```python
await _wait_for(lambda: len(outbound_received) >= 4)
await manager.stop()

assert len(outbound_received) == 4

# Turn 1: prefix at [0], response at [1]
assert "report.md" in outbound_received[1].text
assert outbound_received[1].artifacts == ["/mnt/user-data/outputs/report.md"]

# Turn 2: prefix at [2], response at [3]
assert "chart.png" in outbound_received[3].text
assert "report.md" not in outbound_received[3].text
assert outbound_received[3].artifacts == ["/mnt/user-data/outputs/chart.png"]
```

Also add a new test for the completion message itself:

```python
class TestCompletionPrefix:
    def test_completion_prefix_sent_before_response(self):
        """A '✅ Done' message is published before the agent response."""
        from src.channels.manager import ChannelManager

        async def go():
            bus = MessageBus()
            store = ChannelStore(path=Path(tempfile.mkdtemp()) / "store.json")
            manager = ChannelManager(bus=bus, store=store)

            mock_client = _make_mock_langgraph_client()
            manager._client = mock_client

            outbound_received = []
            bus.subscribe_outbound(lambda msg: outbound_received.append(msg))
            await manager.start()

            await bus.publish_inbound(
                InboundMessage(channel_name="test", chat_id="c1", user_id="u1", text="do something")
            )
            await _wait_for(lambda: len(outbound_received) >= 2)
            await manager.stop()

            # First message is the completion prefix
            assert "✅" in outbound_received[0].text
            assert "done" in outbound_received[0].text.lower()

            # Second message is the actual agent response
            assert outbound_received[1].text == "Hello from agent!"

        _run(go())
```

### Step 2: Run the updated tests to verify they fail

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py::TestChannelManager::test_handle_chat_creates_thread tests/test_channels.py::TestCompletionPrefix -v
```

Expected: `test_handle_chat_creates_thread` FAIL (gets 1 message, expects 2), `TestCompletionPrefix` FAIL.

### Step 3: Implement completion prefix in `_handle_chat`

In `backend/src/channels/manager.py`, in `_handle_chat`, after the try/finally block (after `self._active_runs.pop(run_key, None)`):

```python
# Publish completion prefix before the agent response
done_msg = OutboundMessage(
    channel_name=msg.channel_name,
    chat_id=msg.chat_id,
    thread_id=thread_id,
    text="✅ Done — here's the result:",
    thread_ts=msg.thread_ts,
)
await self.bus.publish_outbound(done_msg)
```

Then the existing response publishing code follows unchanged.

### Step 4: Run tests to verify they pass

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/test_channels.py -v
```

Expected: All PASS

### Step 5: Commit

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/src/channels/manager.py backend/tests/test_channels.py
git commit -m "feat(manager): send completion prefix before agent response"
```

---

## Final Verification

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
PYTHONPATH=. uv run pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: All tests PASS with no regressions.
