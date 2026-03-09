# Projects Memory Tier

**Purpose**: Per-project patterns and configurations
**Organization**: One subdirectory per project

## Project Structure

```
projects/
├── project-name-1/
│   ├── patterns.md      # Project-specific patterns
│   ├── corrections.md   # Project corrections
│   └── config.md        # Project configuration
├── project-name-2/
│   ├── patterns.md
│   ├── corrections.md
│   └── config.md
└── ...
```

## Project Pattern Format

```markdown
## [PRJ-YYYYMMDD-XXX] pattern_name

**Logged**: ISO-8601 timestamp
**Project**: project-name
**Priority**: low | medium | high
**Status**: active | deprecated

### Pattern
Description of the pattern or workflow

### Context
When this pattern applies

### Example
Usage examples or code snippets

---
```

## Auto-Detection

Projects are automatically detected based on:
- Git repository name
- Directory path patterns
- Explicit configuration

---
*Projects are loaded context-aware based on current working directory.*