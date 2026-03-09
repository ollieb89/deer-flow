# Templates Memory Tier

**Purpose**: Reusable project templates and configuration patterns
**Inheritance**: Templates can be customized per project

## Template Structure

```
templates/
├── project-templates/
│   ├── web-app/
│   │   ├── setup.md
│   │   ├── structure.md
│   │   └── workflows.md
│   ├── library/
│   │   ├── setup.md
│   │   ├── testing.md
│   │   └── deployment.md
│   └── documentation/
│       ├── setup.md
│       ├── style-guide.md
│       └── workflows.md
├── config-templates/
│   ├── development.md
│   ├── testing.md
│   ├── staging.md
│   └── production.md
└── workflow-templates/
    ├── feature-branch.md
    ├── bug-fix.md
    ├── release.md
    └── review.md
```

## Template Format

```markdown
## [TPL-YYYYMMDD-XXX] template_name

**Created**: ISO-8601 timestamp
**Category**: project | config | workflow
**Priority**: low | medium | high
**Status**: active | deprecated

### Template
Template content and structure

### Variables
Available template variables for customization

### Usage
How to use and customize this template

### Examples
Instantiation examples

---
```

## Template Inheritance

```
Base Template → Project Customization → Instance
    ↓                ↓                ↓
  templates/     projects/name/    current/
  (immutable)   (overrides)      (runtime)
```

## Template Management

### Instantiation
- Templates are instantiated with project-specific variables
- Customizations are stored in project directory
- Base templates remain unchanged

### Versioning
- Templates have version numbers
- Changes are tracked in template metadata
- Backward compatibility maintained

### Discovery
- Templates discoverable by name, category, or keywords
- Search functionality for template matching
- Usage statistics for popular templates

---
*Templates provide reusable patterns with project-specific customization.*