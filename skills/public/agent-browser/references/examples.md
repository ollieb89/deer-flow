# Agent-Browser Workflow Patterns

Common automation scenarios with step-by-step commands and explanations. These patterns are the foundation for many real-world tasks.

## Pattern 1: Simple Form Fill and Submit

**Goal:** Fill in a login form and submit.

```bash
# 1. Navigate
agent-browser open https://example.com/login

# 2. Snapshot to locate elements
agent-browser snapshot -i
# Find refs for username, password, and submit button (e.g., @e1, @e2, @e3)

# 3. Fill inputs
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"

# 4. Submit
agent-browser click @e3

# 5. Wait for navigation to complete
agent-browser wait --load networkidle
```

**Tips:**
- Use `fill` (clears field) not `type`.
- Always snapshot after navigation to refresh refs.

## Pattern 2: Authenticated Session Persistence

**Goal:** Log in once, reuse session in future runs.

```bash
# First run: Perform login
agent-browser open https://example.com/login
agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @3
agent-browser wait --load networkidle

# Save state for reuse
agent-browser state save auth.json
```

**Future runs:**
```bash
# Load previous session, skipping login
agent-browser state load auth.json
agent-browser open https://example.com/dashboard
# ... proceed directly to dashboard
```

## Pattern 3: Data Extraction from a List

**Goal:** Extract item names and prices from an e-commerce page.

```bash
agent-browser open https://shop.com/products
agent-browser wait --load networkidle

# Snapshot the container of items
agent-browser snapshot -s ".product-item"

# Or iterate: get count of items
count=$(agent-browser get count ".product-item" | tail -1 | jq -r .value)
# Then for i in $(seq 1 $count); do get each item; done

# Example manual extraction
agent-browser get text ".product-name" > names.txt
agent-browser get text ".product-price" > prices.txt
# Or get per-element by ref from snapshot:
agent-browser get text @e1  # first product name
agent-browser get text @e2  # first product price
```

**Better approach:**
```bash
# Use eval to extract structured data in one go
agent-browser eval "Array.from(document.querySelectorAll('.product-item')).map(el => {
  const name = el.querySelector('.product-name')?.textContent.trim();
  const price = el.querySelector('.product-price')?.textContent.trim();
  return {name, price};
})"
```

## Pattern 4: Pagination / Infinite Scroll

**Goal:** Load all items by scrolling or clicking "Next".

**Option A: Click "Next" until no more pages**
```bash
while true; do
  # Extract data from current page
  # ...
  # Try to find and click Next button
  agent-browser snapshot -i > /dev/null 2>&1
  # Parse output for Next button ref (e.g., @next)
  if agent-browser click @next; then
    agent-browser wait --load networkidle
  else
    break
  fi
done
```

**Option B: Infinite scroll (scroll to bottom repeatedly)**
```bash
prev_height=0
while true; do
  agent-browser scroll down 1000
  agent-browser wait 1000  # wait for loading
  # Check if new content loaded by comparing height
  height=$(agent-browser eval "document.body.scrollHeight")
  if [[ "$height" == "$prev_height" ]]; then
    break
  fi
  prev_height=$height
done
```

## Pattern 5: Complex Multi-Step Workflow

**Example:** Search for a product, filter by category, sort, extract data.

```bash
agent-browser open https://shop.com
agent-browser fill search-input "laptop"
agent-browser press Enter
agent-browser wait --load networkidle

# Filter
agent-browser click @filter-laptops
agent-browser wait 2000

# Sort
agent-browser select @sort "price_asc"

# Wait for results to refresh
agent-browser wait --text "Showing"

# Extract data
agent-browser eval "Array.from(document.querySelectorAll('.product-item')).map(...)"
```

## Pattern 6: Debugging with Headed Mode

If something goes wrong, run with `--headed` to see the browser:

```bash
agent-browser --headed open https://example.com
agent-browser --headed snapshot -i
agent-browser --headed click @e1
```

**Also useful:**
- `--devtools` opens Chrome DevTools automatically
- `--slowmo` slows down actions to human-speed for observation

## Pattern 7: Record a Session for Demos

```bash
agent-browser record start demo.webm
agent-browser open https://example.com
agent-browser click @button
agent-browser record stop
```

## Pattern 8: API Testing + UI Verification (Network Interception)

Mock an API endpoint and then verify the UI reacts appropriately.

```bash
# Mock the backend response
agent-browser network route "/api/price" --mock '{"price":999}'

# Trigger UI fetch
agent-browser click @refresh

# Verify the displayed price
price=$(agent-browser get text @price-display)
if [[ "$price" == "999" ]]; then
  echo "UI correctly reflected mocked API response"
else
  echo "Unexpected price: $price"
fi
```

## Pattern 9: Handling Dynamic Elements (No Stale Refs)

Always snapshot after navigation or full-page updates to refresh element refs. Never reuse old `@eX` references across page loads.

**Robust flow:**
```bash
agent-browser open /page1
agent-browser snapshot -i
# use @e1, @e2

agent-browser click @link-to-page2
agent-browser wait --load networkidle

# MUST re-snapshot to get fresh refs
agent-browser snapshot -i
# Now use new @refs for page2
```

## Pattern 10: Error Handling and Retries

Wrap actions with retries for flaky elements or network.

```bash
max_attempts=3
for i in $(seq 1 $max_attempts); do
  if agent-browser click @submit; then
    break
  else
    agent-browser wait 1000
    agent-browser snapshot -i
  fi
done

# If still failed, take screenshot and report
if ! agent-browser is visible @success; then
  agent-browser screenshot failure.png
  echo "Action failed after $max_attempts attempts"
fi
```

## Pattern 11: Structured Data Extraction via Eval

Combine data from multiple elements into a single JSON structure:

```bash
agent-browser eval "Array.from(document.querySelectorAll('.item')).map(item => {
  const name = item.querySelector('.name')?.textContent.trim();
  const qty = item.querySelector('.qty')?.textContent.trim();
  return {name, qty};
})"
```

This returns a JSON array that can be directly consumed by subsequent tools.

## Pattern 12: Conditional Actions

Use `eval` or `is visible` to decide next steps:

```bash
if agent-browser is visible @popup-close; then
  agent-browser click @popup-close
fi

if agent-browser is enabled @next; then
  agent-browser click @next
fi
```

## Pattern 13: Keyboard Only Interactions

For search boxes, keyboard shortcuts, and forms:

```bash
agent-browser fill @search "browser automation"
agent-browser press Enter

# Select all and copy
agent-browser focus @editor
agent-browser press Control+a
agent-browser press Control+c
```

## Pattern 14: Upload Files

```bash
# Ensure <input type="file"> is targeted
agent-browser upload @file-input /path/to/document.pdf
```

## Pattern 15: Scoping Snapshots

Use `-s` to limit snapshot to a specific container to avoid clutter.

```bash
# Only snapshot inside a specific div
agent-browser snapshot -s "#results"

# Get interactive elements in a modal
agent-browser snapshot -i -s ".modal.active"
```

## When to Use Advanced Features

- **State save/load:** Persistent sessions across separate CLI invocations.
- **Recording:** Need to review UI behavior or show demo.
- **Sessions:** Parallel isolated workflows on same machine.
- **CDP:** Deep debugging or integration with external tools.
- **Network control:** Mocking APIs, blocking ads/content, performance testing.
- **Cookies/storage:** Direct manipulation before page load or testing edge cases.

Prefer core features (`open`, `snapshot`, `click`, `fill`, `wait`) wherever possible—they are stable and straightforward.
