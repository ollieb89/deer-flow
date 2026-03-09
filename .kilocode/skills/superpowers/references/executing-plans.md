# Executing Plans

## Overview

Load the plan, review it critically, execute tasks in batches, and report for review between batches.

**Core principle:** Batch execution with checkpoints for human review.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 1: Load and Review Plan
1. Read the implementation plan file (`docs/plans/YYYY-MM-DD-<feature-name>.md`).
2. Review it critically — identify any questions or concerns about the plan.
3. If concerns: Raise them with your human partner before starting.
4. If no concerns: Proceed to implementation.

### Step 2: Execute Batch
**Default: First 3 tasks**

For each task:
1. Mark as in-progress.
2. Follow each step exactly (plan has bite-sized tasks).
3. Run verifications as specified.
4. Mark as completed and commit.

### Step 3: Report
When the batch is complete:
- Show what was implemented.
- Show verification output.
- Say: "Ready for feedback."

### Step 4: Continue
Based on feedback:
- Apply changes if needed.
- Execute the next batch.
- Repeat until complete.

### Step 5: Complete Development
After all tasks are complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- Follow the workflow to verify tests and present options.

## When to Stop and Ask for Help
**STOP executing immediately when:**
- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear).
- Plan has critical gaps.
- You don't understand an instruction.
- Verification fails repeatedly.

**Ask for clarification rather than guessing.**
