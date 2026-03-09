# Agent-Browser Advanced Features

Advanced features for specialized use cases: state persistence, recording, sessions, CDP integration, network control, cookies, storage, JavaScript evaluation, and media generation.

> **Note:** Use these only when the core workflow is insufficient. They add complexity and may have dependencies.

## State Management

Save and restore browser state (cookies, local storage, session storage) to persist logins and settings across runs.

```bash
# Save current browser state
agent-browser state save auth.json

# Restore previously saved state
agent-browser state load auth.json
```

**Typical use:** Avoid logging into a site multiple times. Run login once, save state, then reuse in subsequent automation runs.

## Recording

Record a video of the browser session for debugging or demonstration.

```bash
# Start recording
agent-browser record start --output session.webm

# Perform automation actions...
agent-browser open https://example.com
agent-browser click @e1

# Stop and finalize the recording
agent-browser record stop
```

**Note:** Recording adds significant performance overhead. Enable only when needed.

## Sessions

Isolate sessions with unique names; run multiple independent sessions simultaneously.

```bash
# Start a named session
agent-browser --session work open https://example.com

# Open another isolated session
agent-browser --session personal open https://mail.google.com
```

**Use case:** Run parallel automation tasks on the same machine without cookie contamination.

## Chrome DevTools Protocol (CDP)

Expose CDP endpoint for external tooling or manual debugging in Chrome DevTools.

```bash
# Start browser with CDP on port 9222
agent-browser --cdp 9222 open https://example.com

# In Chrome: chrome://inspect to connect and inspect
```

**Alternative:** Use `--devtools` to automatically open DevTools in headed mode.

## Network Control

Control network traffic: blocking, mocking, capturing HAR.

```bash
# Disable cache globally (helps avoid stale content)
agent-browser network cache false

# Block all images to speed up page load
agent-browser network route "*.png,*.jpg,*.jpeg,*.gif,*.svg" --abort

# Mock a specific API response
agent-browser network route "https://api.example.com/data" --mock '{"status":"ok","value":42}'

# Save network activity as a HAR file
agent-browser har save --output network.har
```

**Use with caution:** Network blocking can break page functionality if critical resources are blocked.

## Cookies & Storage

Direct manipulation of cookies, localStorage, and sessionStorage.

```bash
# Cookies
agent-browser cookies get
agent-browser cookies set "token" "abc123" --domain example.com
agent-browser cookies clear

# localStorage
agent-browser storage get local
agent-browser storage set local "theme" "dark"
agent-browser storage clear local

# sessionStorage
agent-browser storage get session
agent-browser storage set session "tempId" "xyz"
agent-browser storage clear session
```

## JavaScript Evaluation

Execute arbitrary JavaScript in the browser context and get results.

```bash
# Evaluate a simple expression
agent-browser eval "document.title"

# Execute a larger script block (can use ; to chain multiple lines)
agent-browser eval "document.querySelector('h1').textContent; window.location.href;"

# Wait for a specific condition in a loop (via wait --fn)
agent-browser wait --fn "window.someFlag === true"
```

**Useful for:** Advanced extraction, checking conditions, manipulating DOM when element refs are unavailable.

## Media Generation

Capture screenshots, generate PDFs, and record videos.

```bash
# Screenshot
agent-browser screenshot --output screenshot.png   # Full page
agent-browser screenshot --output card.png @e1    # Specific element

# PDF (of the current page)
agent-browser pdf --output page.pdf

# Full-page vs Viewport control
agent-browser screenshot --output full.png --full
agent-browser pdf --output view.pdf --print-background

# Video recording (as shown earlier)
agent-browser record start --output.webm; ... ; agent-browser record stop
```

## Other Useful Commands

```bash
# List all open windows/tabs (minimum required)
agent-browser list

# Get browser console logs
agent-browser console

# Get performance metrics (Timing API and more)
agent-browser perf

# Set viewport size
agent-browser viewport 1280 1024

# Emulate geolocation
agent-browser geolocation 37.7749 -122.4194

# Emulate user agent string
agent-browser useragent "MyBot/1.0"
```
