---
name: superpowers
description: Use when starting a new project, refactoring, or implementing a multi-step feature. This skill implements a strict agentic workflow (Brainstorming → Planning → Execution) to ensure reliability and maintainability.
---

# Superpowers Skill

This skill implements the `superpowers` methodology for high-quality, reliable agentic software development. It enforces a structured lifecycle to minimize errors and maintain a clean codebase.

## The Lifecycle

1.  **Brainstorming**: Deep context gathering, requirement clarification, and writing a comprehensive design document.
2.  **Writing Plans**: Breaking the design into extremely granular (2-5 minute), bite-sized tasks.
3.  **Executing Plans**: Sequential implementation of tasks with mandatory verification checkpoints.

---

## Phase 1: Brainstorming

**Trigger**: Before any implementation begins, especially for new features or complex refactors.

**Objective**: Create a `docs/designs/YYYY-MM-DD-<feature-name>.md` file.

**Instructions**:
- Read all relevant context files.
- Ask clarifying questions to the human partner if anything is ambiguous.
- Draft a Design Document including:
    - **Goal**: What are we building?
    - **Requirements**: Functional and non-functional.
    - **Proposed Architecture**: Components, data flow, and tech stack.
    - **Unresolved Questions/Risks**.

**Handoff**: Once the design doc is approved by the human, proceed to **Phase 2: Writing Plans**.

---

## Phase 2: Writing Plans

**Trigger**: Once a design doc is finalized and approved.

**Objective**: Create a `docs/plans/YYYY-MM-DD-<feature-name>.md` file.

**Instructions**:
- Break down the design into **bite-sized tasks** (2-5 minutes of work each).
- Follow the TDD (Test Driven Development) pattern for each task:
    1. Write a failing test.
    2. Run to verify failure.
    3. Implement minimal code to pass.
    4. Verify passing.
    5. Commit.
- **Reference**: See [writing-plans.md](file:///home/ob/Development/Tools/vibe_coding/deer-flow/.agents/skills/superpowers/references/writing-plans.md) for the exact plan format.

**Handoff**: Once the plan is approved, proceed to **Phase 3: Executing Plans**.

---

## Phase 3: Executing Plans

**Trigger**: Once the implementation plan is approved.

**Objective**: Execute the plan task-by-task.

**Instructions**:
- Execute tasks in batches (default: 3 tasks).
- For each task:
    1. Mark as in-progress.
    2. Follow the steps exactly (write test → verify fail → implement → verify pass).
    3. Mark as completed and commit.
- **Checkpoint**: After each batch, report progress to the human partner and wait for feedback.

**Reference**: See [executing-plans.md](file:///home/ob/Development/Tools/vibe_coding/deer-flow/.agents/skills/superpowers/references/executing-plans.md) for execution details.

---

## General Rules

- **DRY (Don't Repeat Yourself)**: Avoid redundant logic.
- **YAGNI (You Ain't Gonna Need It)**: Don't over-engineer; build only what is required.
- **Exact File Paths**: Always use absolute paths in plans and execution.
- **Stop on Blockers**: If a test fails unexpectedly or instructions are unclear, STOP and ask for clarification.
