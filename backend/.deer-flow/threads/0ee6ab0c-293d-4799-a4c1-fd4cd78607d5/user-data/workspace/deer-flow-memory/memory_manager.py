#!/usr/bin/env python3
"""
DeerFlow Unified Memory System
Combines v1 structured entries with v1.2.9 tiered storage and intelligent automation.
"""

import os
import json
import yaml
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import zipfile
import csv


# ==================== Constants & Configuration ====================

BASE_DIR = Path(os.getenv("DEER_FLOW_MEMORY", "~/deer-flow-memory")).expanduser()
HOT_FILE = BASE_DIR / "memory.md"
INDEX_FILE = BASE_DIR / "index.md"
CORRECTIONS_FILE = BASE_DIR / "corrections.md"
HEALTH_FILE = BASE_DIR / "health" / "status.json"

PROJECTS_DIR = BASE_DIR / "projects"
DOMAINS_DIR = BASE_DIR / "domains"
ARCHIVE_DIR = BASE_DIR / "archive"
TEMPLATES_DIR = BASE_DIR / "templates"
HEALTH_DIR = BASE_DIR / "health"
EXPORTS_DIR = BASE_DIR / "exports"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"

TIER_LIMITS = {
    "hot": 100,      # lines in memory.md
    "warm": 200,     # lines per file in projects/domains
    "cold": None     # unlimited
}

PROMOTION_RULES = {
    "repeat_count": 3,     # uses in 7 days
    "repeat_window_days": 7,
    "demotion_days": 30,   # unused for demotion to warm
    "archive_days": 90     # unused for archive
}

# ==================== Enums ====================

class EntryType(str, Enum):
    CORRECTION = "correction"
    KNOWLEDGE_GAP = "knowledge_gap"
    BEST_PRACTICE = "best_practice"
    ERROR = "error"
    FEATURE_REQUEST = "feature_request"

class NamespaceType(str, Enum):
    GLOBAL = "global"
    PROJECT = "projects"
    DOMAIN = "domains"
    TEMPORARY = "temporary"

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Status(str, Enum):
    TENTATIVE = "tentative"
    EMERGING = "emerging"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"
    PROMOTED = "promoted"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"

class ContextTrigger(str, Enum):
    GIT_REPO = "git_repo"
    FILE_EXTENSIONS = "file_extensions"
    WORKING_DIRECTORY = "working_directory"
    TIME_PATTERNS = "time_patterns"

# ==================== Data Models ====================

@dataclass
class MemoryEntry:
    """Unified memory entry with v1 metadata + v1.2.9 tiering"""
    entry_id: str  # ENTRY-YYYYMMDD-XXX
    type: EntryType
    namespace: str  # global, projects/foo, domains/bar
    logged: str
    priority: Priority
    status: Status
    area: str
    summary: str
    details: str
    suggested_action: str
    metadata: Dict[str, Any]
    repetitions: int = 0
    last_used: Optional[str] = None
    context_triggers: List[ContextTrigger] = None

    def __post_init__(self):
        if self.context_triggers is None:
            self.context_triggers = []
        if isinstance(self.priority, str):
            self.priority = Priority(self.priority)
        if isinstance(self.status, str):
            self.status = Status(self.status)
        if isinstance(self.type, str):
            self.type = EntryType(self.type)

    def to_markdown(self) -> str:
        """Render entry to markdown format"""
        lines = [
            f"# [{self.entry_id}] {self.type.value}",
            f"**Type**: {self.type.value}",
            f"**Namespace**: {self.namespace}",
            f"**Logged**: {self.logged}",
            f"**Priority**: {self.priority.value}",
            f"**Status**: {self.status.value}",
            f"**Area**: {self.area}",
            f"**Repetitions**: {self.repetitions}",
            f"**Context Triggers**: {', '.join([t.value for t in self.context_triggers]) if self.context_triggers else 'None'}",
            "",
            "### Summary",
            self.summary,
            "",
            "### Details",
            self.details,
            "",
            "### Suggested Action",
            self.suggested_action,
            "",
            "### Metadata"
        ]

        for key, value in self.metadata.items():
            lines.append(f"- {key}: {value}")

        lines.append("---")
        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, content: str) -> 'MemoryEntry':
        """Parse markdown back to entry"""
        lines = content.strip().split('\n')
        header = lines[0]
        entry_id = re.search(r'\[(.*?)\]', header).group(1)
        type_match = re.search(r'\*\*Type\*\*: (\w+)', lines[1])
        namespace_match = re.search(r'\*\*Namespace\*\*: (.+)', lines[2])
        logged_match = re.search(r'\*\*Logged\*\*: (.+)', lines[3])
        priority_match = re.search(r'\*\*Priority\*\*: (\w+)', lines[4])
        status_match = re.search(r'\*\*Status\*\*: (\w+)', lines[5])
        area_match = re.search(r'\*\*Area\*\*: (.+)', lines[6])
        reps_match = re.search(r'\*\*Repetitions\*\*: (\d+)', lines[7])
        triggers_match = re.search(r'\*\*Context Triggers\*\*: (.+)', lines[8])

        # Find sections
        summary_start = lines.index("### Summary") + 1
        summary_end = lines.index("### Details")
        details_start = summary_end + 1
        details_end = lines.index("### Suggested Action")
        action_start = details_end + 1
        action_end = lines.index("### Metadata")

        metadata = {}
        for line in lines[lines.index("### Metadata") + 1:]:
            if line.startswith("- "):
                key, value = line[2:].split(": ", 1)
                metadata[key.lower().replace(' ', '_')] = value

        return cls(
            entry_id=entry_id,
            type=EntryType(type_match.group(1)),
            namespace=namespace_match.group(1),
            logged=logged_match.group(1),
            priority=Priority(priority_match.group(1)),
            status=Status(status_match.group(1)),
            area=area_match.group(1),
            summary="\n".join(lines[summary_start:summary_end]).strip(),
            details="\n".join(lines[details_start:details_end]).strip(),
            suggested_action="\n".join(lines[action_start:action_end]).strip(),
            metadata=metadata,
            repetitions=int(reps_match.group(1)) if reps_match else 0,
            context_triggers=[ContextTrigger(t.strip()) for t in triggers_match.group(1).split(',')] if triggers_match.group(1) != 'None' else []
        )


@dataclass
class HealthMetrics:
    """Memory system health tracking"""
    total_entries: int = 0
    hot_entries: int = 0
    warm_entries: int = 0
    cold_entries: int = 0
    last_update: Optional[str] = None
    avg_priority: float = 0.0
    conflict_count: int = 0
    auto_promotions: int = 0
    auto_demotions: int = 0
    compression_ratio: float = 0.0
    usage_since_last_cleanup: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> Dict:
        return asdict(self)


# ==================== Core Memory Manager ====================

class UnifiedMemory:
    """Unified DeerFlow Memory System"""

    def __init__(self, base_dir: Path = BASE_DIR):
        self.base_dir = Path(base_dir).expanduser()
        self.ensure_directories()
        self.index = self.load_index()
        self.corrections_log = self.load_corrections()
        self.health = self.load_health()

    def ensure_directories(self):
        """Create all required directories"""
        for dir_path in [self.base_dir, PROJECTS_DIR, DOMAINS_DIR, ARCHIVE_DIR,
                         TEMPLATES_DIR, HEALTH_DIR, EXPORTS_DIR, SNAPSHOTS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def load_index(self) -> Dict[str, str]:
        """Load index.md mapping topics to file locations"""
        if not INDEX_FILE.exists():
            return {}
        index = {}
        for line in INDEX_FILE.read_text().splitlines():
            if line.strip() and ':' in line:
                topic, location = line.split(':', 1)
                index[topic.strip()] = location.strip()
        return index

    def save_index(self):
        """Save index.md"""
        lines = [f"{topic}: {location}" for topic, location in sorted(self.index.items())]
        INDEX_FILE.write_text("\n".join(lines) + "\n")

    def load_corrections(self) -> List[Dict]:
        """Load recent corrections from corrections.md"""
        if not CORRECTIONS_FILE.exists():
            return []
        entries = []
        content = CORRECTIONS_FILE.read_text()
        # Parse entries separated by ---
        raw_entries = content.split('---\n')
        for raw in raw_entries:
            if raw.strip():
                # Basic parse
                entry = {'raw': raw}
                if '**Type**:' in raw:
                    entry['type'] = re.search(r'\*\*Type\*\*: (\w+)', raw).group(1)
                if '**Logged**:' in raw:
                    entry['logged'] = re.search(r'\*\*Logged\*\*: (.+)', raw).group(1)
                if '**Entry**:' in raw:
                    entry['entry_id'] = re.search(r'\*\*Entry\*\*: (LRN-.+)', raw).group(1)
                entries.append(entry)
        return entries

    def load_health(self) -> HealthMetrics:
        """Load health metrics from JSON"""
        if HEALTH_FILE.exists():
            try:
                data = json.loads(HEALTH_FILE.read_text())
                return HealthMetrics(**data)
            except:
                pass
        return HealthMetrics()

    def save_health(self):
        """Save health metrics"""
        HEALTH_DIR.mkdir(parents=True, exist_ok=True)
        self.health.last_update = datetime.utcnow().isoformat()
        HEALTH_FILE.write_text(json.dumps(self.health.to_dict(), indent=2))

    # ==================== Entry Creation ====================

    def generate_entry_id(self, entry_type: EntryType) -> str:
        """Generate unique ID: TYPE-YYYYMMDD-XXX"""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = entry_type.value.upper()[:4]
        # Find next sequence number
        existing = list(BASE_DIR.glob(f"{prefix}-{today}-*.md"))
        num = len(existing) + 1
        return f"{prefix}-{today}-{num:03d}"

    def create_entry(self, **kwargs) -> MemoryEntry:
        """Create a new memory entry with defaults"""
        entry_id = kwargs.get('entry_id') or self.generate_entry_id(kwargs.get('type', EntryType.CORRECTION))
        entry = MemoryEntry(
            entry_id=entry_id,
            type=kwargs.get('type', EntryType.CORRECTION),
            namespace=kwargs.get('namespace', 'global'),
            logged=kwargs.get('logged', datetime.utcnow().isoformat()),
            priority=kwargs.get('priority', Priority.MEDIUM),
            status=kwargs.get('status', Status.PENDING),
            area=kwargs.get('area', 'general'),
            summary=kwargs.get('summary', ''),
            details=kwargs.get('details', ''),
            suggested_action=kwargs.get('suggested_action', ''),
            metadata=kwargs.get('metadata', {}),
            repetitions=kwargs.get('repetitions', 0),
            last_used=kwargs.get('last_used'),
            context_triggers=kwargs.get('context_triggers', [])
        )
        return entry

    def save_entry(self, entry: MemoryEntry) -> Path:
        """Save entry to appropriate tier based on namespace and status"""
        if entry.namespace == NamespaceType.GLOBAL or entry.namespace.startswith('projects/') or entry.namespace.startswith('domains/'):
            # WARM tier - save to namespace file
            ns_file = self.base_dir / f"{entry.namespace}.md"
            self._append_to_file(ns_file, entry.to_markdown())
        else:
            # HOT tier or corrections
            if entry.type == EntryType.CORRECTION:
                self._append_to_file(CORRECTIONS_FILE, entry.to_markdown())
            else:
                self._append_to_file(HOT_FILE, entry.to_markdown())

        # Update index
        self.index[entry.entry_id] = entry.namespace
        self.save_index()
        return self.get_entry_path(entry)

    def get_entry_path(self, entry: MemoryEntry) -> Path:
        """Get filesystem path for entry"""
        if entry.namespace == NamespaceType.GLOBAL:
            return HOT_FILE
        elif entry.namespace.startswith('projects/') or entry.namespace.startswith('domains/'):
            return self.base_dir / f"{entry.namespace}.md"
        else:
            return BASE_DIR / f"corrections.md"

    def _append_to_file(self, filepath: Path, content: str):
        """Append content to file, creating if needed"""
        if filepath.exists():
            filepath.write_text(filepath.read_text() + "\n" + content)
        else:
            filepath.write_text(content + "\n")

    # ==================== Tier Movement ====================

    def check_promotion_candidates(self) -> List[MemoryEntry]:
        """Find entries that should be promoted to HOT based on repetition"""
        candidates = []

        # Scan all warm files for entries with repetitions >= threshold
        for ns_dir in [PROJECTS_DIR, DOMAINS_DIR]:
            for filepath in ns_dir.glob("*.md"):
                entries = self.parse_file_entries(filepath)
                for entry in entries:
                    if entry.repetitions >= PROMOTION_RULES["repeat_count"]:
                        candidates.append(entry)

        return candidates

    def promote_to_hot(self, entry: MemoryEntry) -> bool:
        """Move entry to hot memory.md"""
        # Remove from current location
        current_path = self.get_entry_path(entry)
        if current_path.exists():
            content = current_path.read_text()
            # Remove specific entry block
            entry_marker = f"# [{entry.entry_id}]"
            if entry_marker in content:
                parts = content.split(entry_marker)
                # Reconstruct without this entry
                before = parts[0].rstrip()
                after = entry_marker + parts[1].split('---\n', 1)[1] if '---\n' in parts[1] else ""
                new_content = (before + after).strip()
                if new_content:
                    current_path.write_text(new_content)
                else:
                    current_path.unlink(missing_ok=True)

        # Add to HOT
        entry.namespace = NamespaceType.GLOBAL
        entry.status = Status.CONFIRMED
        self.save_entry(entry)

        # Log promotion in corrections
        self.log_correction(
            type=EntryType.BEST_PRACTICE,
            summary=f"Auto-promoted {entry.entry_id} to HOT tier",
            details=f"Entry reached {entry.repetitions} repetitions in 7 days. Moved to global memory.",
            priority=Priority.LOW,
            area="memory"
        )

        self.health.auto_promotions += 1
        self.save_health()
        return True

    def demote_to_warm(self, entry: MemoryEntry) -> bool:
        """Demote entry from HOT to appropriate warm namespace"""
        if entry.namespace != NamespaceType.GLOBAL:
            return False

        # Determine namespace based on context triggers or metadata
        target_namespace = entry.metadata.get('suggested_namespace', 'global')

        # Remove from HOT
        current_path = HOT_FILE
        content = current_path.read_text()
        entry_marker = f"# [{entry.entry_id}]"
        if entry_marker not in content:
            return False

        parts = content.split(entry_marker)
        before = parts[0].rstrip()
        after = entry_marker + parts[1].split('---\n', 1)[1] if '---\n' in parts[1] else ""
        new_content = (before + after).strip()
        if new_content:
            current_path.write_text(new_content)
        else:
            current_path.unlink(missing_ok=True)

        # Add to warm
        entry.namespace = target_namespace
        entry.status = Status.ARCHIVED
        self.save_entry(entry)

        self.health.auto_demotions += 1
        self.save_health()
        return True

    def check_demotion_candidates(self) -> List[MemoryEntry]:
        """Find HOT entries unused for 30 days"""
        if not HOT_FILE.exists():
            return []

        candidates = []
        entries = self.parse_file_entries(HOT_FILE)
        cutoff = datetime.utcnow() - timedelta(days=PROMOTION_RULES["demotion_days"])

        for entry in entries:
            if entry.last_used:
                last_used = datetime.fromisoformat(entry.last_used.rstrip('Z'))
                if last_used < cutoff:
                    candidates.append(entry)

        return candidates

    # ==================== Compression ====================

    def compress_memory(self) -> Dict[str, int]:
        """Merge similar entries and archive old patterns"""
        stats = {"merged": 0, "archived": 0, "summarized": 0}

        # Find similar corrections
        all_entries = []
        for filepath in [CORRECTIONS_FILE] + list(PROJECTS_DIR.glob("*.md")) + list(DOMAINS_DIR.glob("*.md")):
            all_entries.extend(self.parse_file_entries(filepath))

        # Group by similarity (type + area + keywords from summary)
        groups = {}
        for entry in all_entries:
            key = f"{entry.type}:{entry.area}:{self._extract_keywords(entry.summary)}"
            groups.setdefault(key, []).append(entry)

        for key, group in groups.items():
            if len(group) > 1 and entry.status in [Status.PENDING, Status.CONFIRMED]:
                # Merge into one representative entry
                merged = self.merge_entries(group)
                self._replace_entries_in_files(group, [merged])
                stats["merged"] += len(group) - 1

        # Archive patterns unused >90 days
        cutoff = datetime.utcnow() - timedelta(days=PROMOTION_RULES["archive_days"])
        for filepath in [PROJECTS_DIR.glob("*.md"), DOMAINS_DIR.glob("*.md")]:
            for f in filepath:
                entries = self.parse_file_entries(f)
                to_archive = []
                for entry in entries:
                    if entry.last_used:
                        last = datetime.fromisoformat(entry.last_used.rstrip('Z'))
                        if last < cutoff and entry.status not in [Status.PROMOTED, Status.RESOLVED]:
                            to_archive.append(entry)

                if to_archive:
                    self.archive_entries(to_archive, ARCHIVE_DIR / f.name)
                    stats["archived"] += len(to_archive)

        self.health.compression_ratio = stats["merged"] / len(all_entries) if all_entries else 0
        self.save_health()
        return stats

    def _extract_keywords(self, text: str) -> str:
        """Simple keyword extraction for grouping"""
        words = re.findall(r'\b\w{4,}\b', text.lower())
        common = {'should', 'must', 'need', 'have', 'error', 'failed', 'issue', 'problem'}
        filtered = [w for w in words if w not in common]
        return ','.join(sorted(set(filtered))[:5])

    def merge_entries(self, entries: List[MemoryEntry]) -> MemoryEntry:
        """Merge multiple similar entries into one comprehensive entry"""
        base = entries[0]
        base.details += "\n\n**Additional cases:**\n"
        base.details += "\n".join([f"- {e.summary}" for e in entries[1:]])

        base.metadata['merged_from'] = [e.entry_id for e in entries]
        base.entry_id = f"{base.entry_id.split('-')[0]}-MERGE-{len(entries)}"
        base.repetitions = max(e.repetitions for e in entries)
        return base

    def archive_entries(self, entries: List[MemoryEntry], archive_file: Path):
        """Move entries to archive"""
        content = "\n".join([e.to_markdown() for e in entries])
        if archive_file.exists():
            archive_file.write_text(archive_file.read_text() + "\n" + content)
        else:
            archive_file.write_text(content)

        # Remove from source files
        for entry in entries:
            path = self.get_entry_path(entry)
            if path.exists():
                # Remove specific entry from file (simplified)
                content = path.read_text()
                entry_marker = f"# [{entry.entry_id}]"
                if entry_marker in content:
                    path.write_text(content.replace(entry_marker + content.split(entry_marker)[1].split('---\n')[0] + '---\n', ''))

    # ==================== Parsing ====================

    def parse_file_entries(self, filepath: Path) -> List[MemoryEntry]:
        """Parse all entries from a markdown file"""
        if not filepath.exists():
            return []

        content = filepath.read_text()
        raw_entries = content.split('---\n')
        entries = []
        for raw in raw_entries:
            if raw.strip() and raw.startswith('# ['):
                try:
                    entry = MemoryEntry.from_markdown(raw)
                    entries.append(entry)
                except Exception as e:
                    self.health.errors.append(f"Parse error in {filepath}: {str(e)}")
        return entries

    # ==================== Context Detection ====================

    def detect_context(self, cwd: Optional[Path] = None, file_path: Optional[Path] = None) -> List[str]:
        """Detect relevant namespaces based on context"""
        namespaces = ['global']
        cwd = Path(cwd or os.getcwd())
        file_path = Path(file_path) if file_path else None

        # Git repo detection
        if (cwd / '.git').exists():
            repo_name = cwd.name
            namespaces.append(f"projects/{repo_name}")

        # File extension domain detection
        if file_path:
            ext = file_path.suffix.lower()
            domain_map = {
                '.ts': 'domains/typescript',
                '.tsx': 'domains/react',
                '.js': 'domains/javascript',
                '.py': 'domains/python',
                '.md': 'domains/documentation',
                '.dockerfile': 'domains/devops',
                '.yml': 'domains/config'
            }
            if ext in domain_map:
                namespaces.append(domain_map[ext])

        # Working directory patterns
        if 'test' in cwd.name.lower():
            namespaces.append('domains/tests')
        if 'docs' in cwd.name.lower():
            namespaces.append('domains/documentation')

        # Time patterns (for recurring context)
        hour = datetime.now().hour
        if 6 <= hour < 12:
            namespaces.append('domains/morning_patterns')
        elif 22 <= hour or hour < 6:
            namespaces.append('domains/night_patterns')

        return list(set(namespaces))

    def load_contextual_memory(self, namespaces: List[str]) -> List[MemoryEntry]:
        """Load entries from specified namespaces"""
        entries = []
        for ns in namespaces:
            if ns == 'global':
                entries.extend(self.parse_file_entries(HOT_FILE) if HOT_FILE.exists() else [])
            else:
                ns_file = self.base_dir / f"{ns}.md"
                if ns_file.exists():
                    entries.extend(self.parse_file_entries(ns_file))
        return entries

    # ==================== Health & Reporting ====================

    def get_health_report(self) -> str:
        """Generate health metrics report"""
        hot_count = len(self.parse_file_entries(HOT_FILE)) if HOT_FILE.exists() else 0
        warm_count = sum(len(self.parse_file_entries(f)) for f in PROJECTS_DIR.glob("*.md"))
        warm_count += sum(len(self.parse_file_entries(f)) for f in DOMAINS_DIR.glob("*.md"))
        cold_count = sum(len(self.parse_file_entries(f)) for f in ARCHIVE_DIR.glob("*.md"))

        report = f"""
📊 DeerFlow Memory Health

HOT (memory.md): {hot_count} entries
WARM (projects/ + domains/): {warm_count} entries
COLD (archive/): {cold_count} entries

Last update: {self.health.last_update or 'Never'}

Auto-promotions: {self.health.auto_promotions}
Auto-demotions: {self.health.auto_demotions}
Compression ratio: {self.health.compression_ratio:.2%}
Conflicts detected: {self.health.conflict_count}

Recent errors: {len(self.health.errors)}
"""
        if self.health.errors:
            report += "\nLatest errors:\n"
            for err in self.health.errors[-5:]:
                report += f"  - {err}\n"

        return report.strip()

    # ==================== Export System ====================

    def export_memory(self, format: str = 'zip', namespaces: List[str] = None) -> Path:
        """Export memory in various formats"""
        namespaces = namespaces or ['global', 'projects', 'domains', 'archive']
        export_path = EXPORTS_DIR / f"memory-export-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        if format == 'json':
            export_path = export_path.with_suffix('.json')
            all_entries = []
            for ns in namespaces:
                if ns == 'global':
                    all_entries.extend(self.parse_file_entries(HOT_FILE))
                elif ns == 'projects':
                    all_entries.extend([e for f in PROJECTS_DIR.glob("*.md") for e in self.parse_file_entries(f)])
                elif ns == 'domains':
                    all_entries.extend([e for f in DOMAINS_DIR.glob("*.md") for e in self.parse_file_entries(f)])
                elif ns == 'archive':
                    all_entries.extend([e for f in ARCHIVE_DIR.glob("*.md") for e in self.parse_file_entries(f)])

            export_path.write_text(json.dumps([asdict(e) for e in all_entries], indent=2))

        elif format == 'markdown':
            export_path = export_path.with_suffix('.md')
            content = "# DeerFlow Memory Export\n\n"
            for ns in namespaces:
                content += f"## {ns.title()}\n\n"
                if ns == 'global':
                    entries = self.parse_file_entries(HOT_FILE)
                elif ns == 'projects':
                    entries = [e for f in PROJECTS_DIR.glob("*.md") for e in self.parse_file_entries(f)]
                elif ns == 'domains':
                    entries = [e for f in DOMAINS_DIR.glob("*.md") for e in self.parse_file_entries(f)]
                elif ns == 'archive':
                    entries = [e for f in ARCHIVE_DIR.glob("*.md") for e in self.parse_file_entries(f)]
                content += "\n".join([e.to_markdown() for e in entries]) + "\n\n"
            export_path.write_text(content)

        elif format == 'csv':
            export_path = export_path.with_suffix('.csv')
            all_entries = []
            for ns in namespaces:
                if ns == 'global':
                    all_entries.extend(self.parse_file_entries(HOT_FILE))
                elif ns == 'projects':
                    all_entries.extend([e for f in PROJECTS_DIR.glob("*.md") for e in self.parse_file_entries(f)])
                elif ns == 'domains':
                    all_entries.extend([e for f in DOMAINS_DIR.glob("*.md") for e in self.parse_file_entries(f)])
                elif ns == 'archive':
                    all_entries.extend([e for f in ARCHIVE_DIR.glob("*.md") for e in self.parse_file_entries(f)])

            with export_path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['entry_id', 'type', 'namespace', 'logged', 'priority', 'status', 'area', 'summary', 'details', 'suggested_action'])
                writer.writeheader()
                for e in all_entries:
                    row = asdict(e)
                    row['details'] = row['details'][:100]  # truncate for CSV
                    row['suggested_action'] = row['suggested_action'][:100]
                    writer.writerow(row)

        elif format == 'zip':
            export_path = export_path.with_suffix('.zip')
            # First export each format into temp dir
            temp_dir = export_path.parent / f"temp-{export_path.stem}"
            temp_dir.mkdir(exist_ok=True)
            self.export_memory('json', namespaces)
            self.export_memory('markdown', namespaces)
            self.export_memory('csv', namespaces)
            with zipfile.ZipFile(export_path, 'w') as zf:
                for file in temp_dir.glob("*"):
                    zf.write(file, file.name)
            # Cleanup temp

        return export_path

    # ==================== Utilities ====================

    def log_correction(self, **kwargs) -> MemoryEntry:
        """Quick method to log a correction"""
        entry = self.create_entry(
            type=EntryType.CORRECTION,
            namespace='corrections',
            **kwargs
        )
        self.save_entry(entry)
        return entry

    def record_usage(self, entry_id: str):
        """Record that an entry was used (for demotion tracking)"""
        # Find entry
        for filepath in [HOT_FILE] + list(PROJECTS_DIR.glob("*.md")) + list(DOMAINS_DIR.glob("*.md")):
            entries = self.parse_file_entries(filepath)
            for entry in entries:
                if entry.entry_id == entry_id:
                    entry.last_used = datetime.utcnow().isoformat()
                    entry.repetitions += 1
                    # Save modified entry back
                    self._replace_entry_in_file(filepath, entry)
                    return

    def _replace_entry_in_file(self, filepath: Path, updated_entry: MemoryEntry):
        """Replace an entry in a file with updated version"""
        content = filepath.read_text()
        old_marker = f"# [{updated_entry.entry_id}]"
        if old_marker in content:
            parts = content.split(old_marker)
            after = parts[1].split('---\n', 1)[1] if '---\n' in parts[1] else ""
            new_block = updated_entry.to_markdown() + "\n---\n"
            new_content = parts[0] + new_block + after
            filepath.write_text(new_content)


# ==================== CLI Interface ====================

def main():
    """CLI interface for memory operations"""
    import sys

    mem = UnifiedMemory()

    if len(sys.argv) < 2:
        print("Usage: memory_manager.py <command> [args]")
        print("\nCommands:")
        print("  health           - Show health report")
        print("  promote          - Check and promote candidates")
        print("  demote           - Check and demote unused entries")
        print("  compress         - Run compression")
        print("  export <format>  - Export memory (json|markdown|csv|zip)")
        print("  log <type> <summary> <details> <area> - Quick log entry")
        print("  context          - Detect current context")
        print("  snapshot         - Create a snapshot")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'health':
        print(mem.get_health_report())

    elif cmd == 'promote':
        candidates = mem.check_promotion_candidates()
        for entry in candidates:
            mem.promote_to_hot(entry)
            print(f"Promoted {entry.entry_id} to HOT")
        print(f"\nTotal promotions: {len(candidates)}")

    elif cmd == 'demote':
        candidates = mem.check_demotion_candidates()
        for entry in candidates:
            mem.demote_to_warm(entry)
            print(f"Demoted {entry.entry_id}")
        print(f"\nTotal demotions: {len(candidates)}")

    elif cmd == 'compress':
        stats = mem.compress_memory()
        print(f"Compression complete: {stats}")

    elif cmd == 'export':
        if len(sys.argv) < 3:
            print("Specify format: json|markdown|csv|zip")
            sys.exit(1)
        fmt = sys.argv[2]
        path = mem.export_memory(fmt)
        print(f"Exported to {path}")

    elif cmd == 'log':
        if len(sys.argv) < 6:
            print("Usage: log <type> <summary> <details> <area>")
            sys.exit(1)
        entry = mem.log_correction(
            type=EntryType(sys.argv[2]),
            summary=sys.argv[3],
            details=sys.argv[4],
            area=sys.argv[5]
        )
        print(f"Logged {entry.entry_id}")

    elif cmd == 'context':
        namespaces = mem.detect_context()
        entries = mem.load_contextual_memory(namespaces)
        print(f"Detected namespaces: {namespaces}")
        print(f"Loaded {len(entries)} contextual entries")

    elif cmd == 'snapshot':
        snapshot_file = SNAPSHOTS_DIR / f"snapshot-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
        snapshots = {
            'timestamp': datetime.utcnow().isoformat(),
            'hot': [asdict(e) for e in mem.parse_file_entries(HOT_FILE)] if HOT_FILE.exists() else [],
            'warm': {
                'projects': {f.name: [asdict(e) for e in mem.parse_file_entries(f)] for f in PROJECTS_DIR.glob("*.md")},
                'domains': {f.name: [asdict(e) for e in mem.parse_file_entries(f)] for f in DOMAINS_DIR.glob("*.md")}
            },
            'cold': {f.name: [asdict(e) for e in mem.parse_file_entries(f)] for f in ARCHIVE_DIR.glob("*.md")},
            'health': mem.health.to_dict(),
            'index': mem.index
        }
        snapshot_file.write_text(json.dumps(snapshots, indent=2))
        print(f"Snapshot saved to {snapshot_file}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
