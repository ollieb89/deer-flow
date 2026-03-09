# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design and get user approval.

> [!IMPORTANT]
> Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it. This applies to EVERY project regardless of perceived simplicity.

## Checklist

Completing these items in order is MANDATORY:

1. **Explore project context** — check files, docs, recent commits.
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria.
3. **Propose 2-3 approaches** — with trade-offs and your recommendation.
4. **Present design** — in sections scaled to their complexity, get user approval after each section.
5. **Write design doc** — save to `docs/designs/YYYY-MM-DD-<topic>-design.md` and commit.
6. **Transition to implementation** — proceed to the **Writing Plans** phase of the `superpowers` skill.

## The Process

### Understanding the idea
- Check out the current project state first (files, docs, recent commits).
- Ask questions one at a time to refine the idea.
- Prefer multiple choice questions when possible.
- Only one question per message.
- Focus on: purpose, constraints, success criteria.

### Exploring approaches
- Propose 2-3 different approaches with trade-offs.
- Lead with your recommended option and explain why.

### Presenting the design
- Scale each section to its complexity.
- Ask after each section whether it looks right so far.
- Cover: architecture, components, data flow, error handling, testing.

## After the Design

### Documentation
- Write the validated design to `docs/designs/YYYY-MM-DD-<topic>-design.md`.
- Commit the design document to git.

### Implementation
- Proceed to the **Writing Plans** phase. Do NOT start implementation without a plan.
