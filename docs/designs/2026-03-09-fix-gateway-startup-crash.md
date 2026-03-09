# Design: Fixing Gateway Startup Configuration Crash

**Goal**: Resolve the immediate crash at gateway startup by improving traceability and finding the root cause of the `get_app_config()` failure.

## 1. Problem Description
The gateway application (FastAPI) crashes during the `lifespan` startup because `get_app_config()` throws an exception. The current error handling uses `sys.exit(1)` and only logs the exception message, losing the traceback and context needed for debugging.

## 2. Proposed Changes

### 2.1. Improve Traceability in `backend/src/gateway/app.py`
- Replace `logger.error` + `sys.exit(1)` with `logger.exception` + `raise RuntimeError("Gateway configuration failed during startup") from e`.
- Update `init_db` to use `logger.warning("Failed to initialize database: %s", e, exc_info=True)` to preserve traceback without killing the app (unless it's critical).
- Add more explicit logging of what is being loaded.

### 2.2. Root Cause Investigation
- Inspect `backend/src/config/app_config.py`.
- Look for Pydantic `BaseSettings` and required fields without defaults.
- Check `.env` loading logic and path resolution.
- Verify environment variables.

### 2.3. Root Cause Resolution
- Once identified, fix the missing or invalid configuration.
- Potential fixes:
    - Adding default values for missing required fields.
    - Fixing path resolution for `.env` files.
    - Correcting invalid environment variable values.

## 3. Risks
- Exposing secrets in logs: We must be careful not to log sensitive fields in the configuration object.
- Breaking other services: If `app_config` is shared, changes might affect other services.

## 4. Unresolved Questions
- Why exactly is `get_app_config` failing? (Will be answered during implementation)
- Is `init_db` failure critical? Currently it's a `logger.warning`, but the app might fail later if DB is unreachable.
