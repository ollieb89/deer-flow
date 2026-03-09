# DeerFlow Skills System

The Skills system provides a mechanism for agents to access optimized workflows, best practices, and specialized tools. Skills are structured as directories containing a `SKILL.md` file and any accompanying resources.

## Skill Categories

Skills are organized into three primary categories based on their scope and location:

### 1. Public Skills (`skills/public/`)
- **Location**: `skills/public/[skill-name]/`
- **Purpose**: General-purpose, shared skills available across the entire project.
- **Examples**: `agent-browser`, `standard-formatting`, `github-workflows`.
- **Discovery**: Scanned automatically by the system.
- **Enablement**: Must be enabled globally (e.g., in `skills-lock.json`) to be usable.

### 2. Custom Skills (`skills/custom/`)
- **Location**: `skills/custom/[skill-name]/`
- **Purpose**: User-defined global skills specific to your project or team.
- **Discovery**: Scanned automatically alongside public skills.
- **Enablement**: Must be enabled globally to be usable.

### 3. Agent-Local Skills (`agents/[name]/skills/`)
- **Location**: `agents/[agent-name]/skills/[skill-name]/`
- **Purpose**: Specialized skills exclusive to a specific custom agent.
- **Discovery**: Automatically discovered when that specific agent is loaded.
- **Enablement**: **Automatically enabled** for that agent by default.

## Configuration and Filtering

By default, an agent has access to **all globally enabled skills** plus its own **agent-local skills**. You can restrict this in the agent's configuration.

### Restricting Skills for an Agent
In `agents/[agent-name]/config.yaml`:
```yaml
name: my-agent
skills:
  - my-local-skill      # Found in agent's own skills/ dir
  - agent-browser       # Found in skills/public/ (must be enabled globally)
```

### Overriding Subagent Skills
In the root `config.yaml`:
```yaml
subagents:
  bash:
    skills:
      - bash-optimization
```

## Creating a New Skill

A skill directory must contain a `SKILL.md` file with the following frontmatter:

```markdown
---
name: "Skill Name"
description: "Brief description of what this skill does"
---

# Instructions
Detailed workflow instructions for the agent go here...
```

For more details on agent-specific setup, see the [Skills Walkthrough](file:///home/ob/.gemini/antigravity/brain/360ea817-15d3-41c8-bb55-8c0df71b1698/walkthrough.md).
