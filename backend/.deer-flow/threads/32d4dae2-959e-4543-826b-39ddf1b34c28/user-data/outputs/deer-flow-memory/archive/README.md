# Archive Memory Tier

**Purpose**: Decayed patterns and historical data
**Retention**: Configurable retention period (default: 90 days)

## Archive Structure

```
archive/
├── by-date/
│   ├── 2025-03/
│   │   ├── patterns-2025-03.md
│   │   ├── corrections-2025-03.md
│   │   └── metadata-2025-03.md
│   └── 2025-04/
├── by-project/
│   ├── project-name/
│   │   ├── patterns-archive.md
│   │   └── corrections-archive.md
│   └── ...
└── by-domain/
    ├── code/
    │   ├── patterns-archive.md
    │   └── corrections-archive.md
    └── ...
```

## Archive Format

```markdown
## [ARC-YYYYMMDD-XXX] archived_entry

**Original Logged**: ISO-8601 timestamp
**Archived**: ISO-8601 timestamp
**Original Tier**: hot | corrections | projects | domains
**Retention**: until | date-based | size-based

### Original Content
[Archived content with original metadata]

### Decay Analysis
Why this pattern was archived (redundant, outdated, superseded)

### Historical Value
What insights can still be gained from this pattern

---
```

## Archive Management

### Automatic Decay
- Patterns older than 90 days automatically considered for archiving
- Low-frequency access patterns (>30 days without access)
- Superseded patterns (newer versions exist)

### Manual Archiving
- Explicit archiving via management commands
- Pattern consolidation when redundancy detected
- End-of-project pattern archival

### Archive Recovery
- Patterns can be restored from archive if needed
- Archive searchable for historical reference
- Decay patterns can be reactivated

---
*Archive is automatically managed based on decay rules and retention policies.*