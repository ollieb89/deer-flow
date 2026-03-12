# Design: Telegram Job Notifications

**Date**: 2026-03-12
**Scope**: `backend/src/channels/telegram.py`, `backend/src/channels/manager.py`

## Problem

1. The Telegram channel sends a text message "Working on it..." when a message is received — clutters the chat and violates Bambi's SOUL (which says to react with ❤️, not text).
2. Long-running LangGraph runs give no feedback while in progress — user doesn't know if Bambi is still working or has crashed.
3. When a run completes, there's no clear "done" signal — the response just appears.

## Solution

Three focused changes using Approach B (ChannelManager owns tracking, TelegramChannel owns delivery):

---

## 1. ❤️ Reaction Instead of "Working on it..."

**File**: `backend/src/channels/telegram.py`

Replace `_send_running_reply` with `_send_running_reaction`:
- Calls `bot.set_message_reaction(chat_id, message_id, reaction=[ReactionTypeEmoji(emoji="❤")])`
- Falls back silently on exception (reactions may not work in all chat types)
- Called in both `_on_text` and `_cmd_generic` instead of the old method

No new configuration needed.

---

## 2. 15-Minute Status Pings

**File**: `backend/src/channels/manager.py`

### Data structures

```python
@dataclass
class _RunInfo:
    chat_id: str
    channel_name: str
    started_at: datetime
    last_ping_at: datetime | None = None
```

`ChannelManager` gains `_active_runs: dict[str, _RunInfo]` (key = `f"{channel}:{chat_id}:{topic_id or ''}"`) and `_ticker_task: asyncio.Task | None`.

### Lifecycle

- `start()`: creates `asyncio.create_task(self._status_ticker())`
- `stop()`: cancels and awaits `_ticker_task`
- `_handle_chat()`: registers `_RunInfo` at start, deregisters at completion

### Ticker logic

```
loop every 60 seconds:
  for each active run:
    elapsed = now - started_at
    since_last_ping = now - (last_ping_at or started_at)
    if elapsed >= 15min AND since_last_ping >= 15min:
      publish OutboundMessage: "⚙️ Still working — {elapsed}m elapsed."
      update last_ping_at = now
```

Ping is sent to the same `chat_id` and `channel_name` as the original message. No `thread_ts` set (sends as a new top-level message in the chat, not a reply).

---

## 3. Completion Prefix

**File**: `backend/src/channels/manager.py`

In `_handle_chat`, after `runs.wait()` completes and before publishing the response:

1. Deregister the run from `_active_runs`
2. Publish `OutboundMessage(text="✅ Done — here's the result:")` to same chat
3. Publish the normal response `OutboundMessage`

---

## Out of Scope

- Subagent background task tracking (subagent_enabled=False in channel context)
- Multi-channel support (Slack/Feishu) — ticker is channel-agnostic via MessageBus, so it works, but not explicitly tested
- Configuration for ping interval (hardcoded 15 min for now)

## Files Changed

| File | Change |
|------|--------|
| `backend/src/channels/telegram.py` | Replace `_send_running_reply` with `_send_running_reaction` |
| `backend/src/channels/manager.py` | Add `_RunInfo`, `_active_runs`, `_ticker_task`, register/deregister in `_handle_chat`, completion prefix |
