# Agent-Browser Skill Grader

## Purpose
Evaluates test execution results against defined assertions. Grades each test case pass/fail and provides detailed feedback.

## Inputs
From each test run directory:
- `prompt.txt`: original user prompt
- `assertions.json`: list of expected assertions
- `result.json`: actual execution result (success, commands, outputs)
- `log.txt`: full execution log

## Grading Process

1. Load all assertion items for the test case.
2. For each assertion, check if it's satisfied by the actual result.
   - Use simple string matching on commands/outputs.
   - Command assertions: look for specific commands in the `commands` list.
   - Output assertions: look for key phrases in `output` or `log`.
   - File assertions: check if files exist in workspace (currently not implemented but could check `result`).
3. An assertion passes if the expected pattern is found; otherwise fails.
4. Overall status: PASS if all assertions pass; FAIL otherwise.
5. Record grading details: which assertions passed/failed, any error messages, timing.

## Notes
- Avoid overly strict matching; be tolerant to minor variations (e.g., command flags order, whitespace).
- When assertion is about qualitative outcome (e.g., "item extracted"), infer from success flag and presence of non-empty output.
- For multi-step processes, break down into concrete assertions during test design.

</agent_browser_eval_grader>
