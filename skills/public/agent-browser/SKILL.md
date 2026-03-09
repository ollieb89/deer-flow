---
name: agent-browser
description: Fast Rust-based headless browser automation CLI with Node.js fallback for AI agents. Automate web workflows, scrape data, submit forms, manage sessions, and record browser interactions.
version: 1.0.0
author: ClawBo Skill
tags:
  - browser
  - automation
  - scraping
  - testing
  - web
---

# agent-browser

**Trigger contexts:** When the user wants to automate a website, scrape data, submit forms, test web interfaces, record browser sessions, extract information, or perform any browser-based automation.

**Pushy/alternative contexts:** Use this for reliable, scriptable browser automation with built-in element references and state management. Prefer over generic scraping when you need interactive element targeting, session persistence, or video recording.

## Compatibility

The skill expects the `agent-browser` CLI to be installed globally (`npm install -g agent-browser`). Browser binaries will be downloaded automatically on first use via `agent-browser install`. Compatible with Linux, macOS, and Windows (via WSL or native Node). Supports Chrome/Chromium, Firefox, and WebKit backends.

## Instructions

### Prerequisite Check

Before any browser operation, verify the CLI is available:

```bash
command -v agent-browser >/dev/null 2>&1 || {
  echo "⚠️  agent-browser CLI not found."
  echo "Install: npm install -g agent-browser"
  echo "Setup browsers: agent-browser install"
  exit 1
}
```

Optionally check browser availability: `agent-browser info`.

### Core Workflow Pattern

Most automation tasks follow this loop:

1. **Navigate**: `agent-browser open <url>`
2. **Snapshot**: `agent-browser snapshot -i` (get interactive elements with refs like `@e1`, `@e2`)
3. **Interact**: Use refs to perform actions (`click`, `fill`, `select`, etc.)
4. **Wait**: Wait for navigation/load if needed (`agent-browser wait --load networkidle`)
5. **Repeat**: Snapshot again after DOM changes to get updated refs

**Important notes:**
- Refs are stable within a page load but change on navigation; always re-snapshot after navigation
- Use `fill` (not `type`) to clear input fields before typing
- Append `--json` for machine-readable output if parsing

### Execution Model

The skill executes commands directly via `run_in_terminal` and returns results. For transparency, it may echo commands and outputs to the user. Commands are built dynamically based on the user's request.

### Handling Common Scenarios

**Form submission:**
- Snapshot to locate elements by their label/text
- `fill @ref "value"` for text inputs
- `click` the submit button
- `wait --load networkidle` for completion
- Optionally `snapshot -i` to verify success

**Authentication persistence:**
- Perform login once
- `agent-browser state save auth.json`
- On subsequent runs: `agent-browser state load auth.json` before `open`

**Data extraction:**
- Use `get text @ref` or `get html @ref` to retrieve content
- Use `snapshot -s "<css>"` to scope to a specific container
- Chain multiple `get` commands to build structured data

**Multi-step workflows:**
- Maintain the same session; don't close between steps
- Snapshot after each navigation to refresh refs
- Use `wait` conditions to ensure page readiness before interacting

**Error handling:**
- If an element is not found, take a new snapshot to find the correct ref
- If navigation fails, verify the URL and retry with `--headed` for debugging
- If commands fail silently, use `--headed` to visually see the browser

### Advanced Features (Optional)

The CLI also supports:
- Video recording: `agent-browser record start output.webm` → perform actions → `record stop`
- Network interception: `agent-browser network route <url> --abort`
- Session isolation: `agent-browser --session <name> open <url>`
- DevTools Protocol: `agent-browser --cdp 9222 snapshot`
- Screenshots/PDFs: `agent-browser screenshot path.png` or `agent-browser pdf output.pdf`

These are used when explicitly requested; they are not in the default automation path.

### Output Format

Results are presented as:
- Command outputs (stdout/stderr)
- Extracted data (text, HTML, attributes)
- Status messages (success, errors, warnings)
- For automation, use `--json` flag and parse the output

### Example Prompt-to-Execution

User: "Fill out the login form on https://example.com/login with user@example.com and password123 and tell me if it succeeds."

Skill actions:
1. `agent-browser open https://example.com/login`
2. `agent-browser snapshot -i` → parse refs for email, password, submit
3. `agent-browser fill @e1 "user@example.com"`
4. `agent-browser fill @e2 "password123"`
5. `agent-browser click @e3`
6. `agent-browser wait --load networkidle`
7. `agent-browser snapshot -i` to check for dashboard/link
8. Return success/failure and any error messages

### When Not to Use

- For heavy JavaScript-rendered SPAs without proper snapshot support, consider adding explicit waits
- If the target site has strong anti-bot measures, use `--headed` and manual verification
- For massive-scale scraping across hundreds of pages, a dedicated crawler may be more appropriate
