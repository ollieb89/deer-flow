# Domains Memory Tier

**Purpose**: Domain-specific patterns and best practices
**Organization**: Categorized by domain type

## Domain Structure

```
domains/
├── code/
│   ├── patterns.md      # Programming patterns
│   ├── best-practices.md # Language-agnostic best practices
│   └── anti-patterns.md # Common mistakes to avoid
├── writing/
│   ├── patterns.md      # Writing patterns
│   ├── style-guide.md   # Writing style guide
│   └── templates/       # Document templates
├── comms/
│   ├── patterns.md      # Communication patterns
│   ├── templates/       # Communication templates
│   └── etiquette.md     # Communication etiquette
├── research/
│   ├── patterns.md      # Research patterns
│   ├── sources.md       # Trusted sources
│   └── methods.md       # Research methodologies
└── analysis/
    ├── patterns.md      # Analysis patterns
    ├── frameworks.md    # Analysis frameworks
    └── tools.md         # Analysis tools
```

## Domain Pattern Format

```markdown
## [DOM-YYYYMMDD-XXX] domain_pattern

**Logged**: ISO-8601 timestamp
**Domain**: domain-name
**Priority**: low | medium | high
**Applicability**: broad | specific

### Pattern
Description of the domain pattern

### Best Practices
Recommended approaches and methods

### Examples
Real-world applications

### Resources
Related tools, documentation, or references

---
```

## Domain Detection

Domains are automatically applied based on:
- File extensions (.ts → code, .md → writing)
- Task context (analysis, research, etc.)
- Content type (code review, documentation, etc.)

---
*Domain patterns are loaded based on current task context.*