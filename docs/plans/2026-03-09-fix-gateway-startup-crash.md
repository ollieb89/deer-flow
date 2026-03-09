# Implementation Plan: Fix Gateway Startup Configuration Crash

**Goal**: Improve startup error handling and fix the `get_app_config()` failure.

## Tasks

- [ ] **Task 1: Improve Traceability in `backend/src/gateway/app.py`**
    - [ ] 1.1 Update `lifespan` in `backend/src/gateway/app.py` to use `logger.exception` and `raise RuntimeError` for `get_app_config` failure.
    - [ ] 1.2 Update `lifespan` in `backend/src/gateway/app.py` to use `logger.warning` with `exc_info=True` for `init_db` failure.
    - [ ] 1.3 Add more explicit logging of config load attempt.
    - [ ] 1.4 Verify passing (run server and check logs).

- [ ] **Task 2: Root Cause Investigation of `get_app_config`**
    - [ ] 2.1 Locate `get_app_config` and its settings model.
    - [ ] 2.2 Inspect `backend/src/config/app_config.py` content.
    - [ ] 2.3 Search for field requirements or path issues.

- [ ] **Task 3: Root Cause Resolution**
    - [ ] 3.1 Implement fix in `backend/src/config/app_config.py` (e.g., set absolute path for `.env` or add defaults).
    - [ ] 3.2 Verify passing (run server and confirm configuration loads successfully).
    - [ ] 3.3 Confirm `init_db` also works correctly.

## Verification
- Run the gateway and observe logs.
- Ensure no `sys.exit(1)` occurs without a clear traceback.
- Verify `get_app_config()` succeeds.
