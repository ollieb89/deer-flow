# Agent-Browser Core Commands

The agent-browser CLI provides intuitive structured commands for navigation, interaction, check states, and data extraction.

## Navigation

```bash
agent-browser open <url>      # Navigate to URL
agent-browser back            # Go back
agent-browser forward         # Go forward
agent-browser reload          # Reload page
agent-browser close           # Close browser
```

## Snapshot (Page Analysis)

Snapshots analyze the page and returns interactive elements with references (e.g., `@e1`, `@e2`).
Always snapshot after navigation or significant DOM changes (`--load networkidle` is very useful for waiting).

```bash
agent-browser snapshot            # Full accessibility tree
agent-browser snapshot -i         # Interactive elements only (recommended)
agent-browser snapshot -c         # Compact output
agent-browser snapshot -d 3       # Limit depth to 3
agent-browser snapshot -s "#main" # Scope to specific CSS selector
```

## Interactions (Using @refs from Snapshot)

```bash
agent-browser click @e1           # Click
agent-browser dblclick @e1        # Double-click
agent-browser focus @e1           # Focus element
agent-browser fill @e2 "text"     # Clear existing value and type text
agent-browser type @e2 "text"     # Type text without clearing existing value
agent-browser press Enter         # Press a keyboard key
agent-browser press Control+a     # Emulate a key combination
agent-browser keydown Shift       # Hold a key down
agent-browser keyup Shift         # Release a held key
agent-browser hover @e1           # Hover over an element
agent-browser check @e1           # Check a checkbox
agent-browser uncheck @e1         # Uncheck a checkbox
agent-browser select @e1 "value"  # Select an option in a dropdown
agent-browser scroll down 500     # Scroll the page down 500px
agent-browser scrollintoview @e1  # Scroll until element is visible
agent-browser drag @e1 @e2        # Drag element e1 and drop it on element e2
agent-browser upload @e1 file.pdf # Upload a file to a file input element
```

## Get Information

```bash
agent-browser get text @e1        # Get text content of an element
agent-browser get html @e1        # Get innerHTML of an element
agent-browser get value @e1       # Get input field value
agent-browser get attr @e1 href   # Get the value of a specific attribute (e.g., href)
agent-browser get title           # Get the page title
agent-browser get url             # Get the current URL
agent-browser get count ".item"   # Count occurrences matching a CSS selector
agent-browser get box @e1         # Get the bounding box of an element
```

## Check State

```bash
agent-browser is visible @e1      # True/False: is the element currently visible?
agent-browser is enabled @e1      # True/False: is the element enabled (not disabled)?
agent-browser is checked @e1      # True/False: is the checkbox or radio button checked?
```

## Wait Conditions

Pausing execution dynamically based on page state.

```bash
agent-browser wait @e1                     # Wait until an element is present and visible
agent-browser wait 2000                    # Wait precisely 2000 milliseconds
agent-browser wait --text "Success"        # Wait until the target text appears on screen
agent-browser wait --url "/dashboard"      # Wait until the URL changes to match the pattern
agent-browser wait --load networkidle      # Wait until all network requests resolve
agent-browser wait --fn "window.ready"     # Wait until the provided JavaScript evaluates to true
```

## Mouse Control

For granular, low-level coordinate interactions.

```bash
agent-browser mouse move 100 200      # Move the mouse to absolute coordinates (X:100, Y:200)
agent-browser mouse down left         # Emulate pressing the left mouse button down
agent-browser mouse up left           # Release the left mouse button
agent-browser mouse wheel 100         # Scroll the mouse wheel by 100 units
```

## Semantic Locators

Alternative to using specific references (`@e1`). Locate elements directly without generating a snapshot.

```bash
agent-browser find role button click --name "Submit"   # Find target by ARIA role and name
agent-browser find text "Sign In" click                # Find target by inner text
agent-browser find label "Email" fill "user@test.com"  # Find an input via its associated label
agent-browser find first ".item" click                 # Find the first element matching a selector
agent-browser find nth 2 "a" text                      # Find the Nth element (1-indexed)
```
