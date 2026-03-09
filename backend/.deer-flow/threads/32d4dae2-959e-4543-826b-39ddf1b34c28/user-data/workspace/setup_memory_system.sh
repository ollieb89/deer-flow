#!/bin/bash

# Deer Flow Memory System Setup Script
# Creates the tiered memory architecture

set -e

echo "Setting up Deer Flow Memory System..."

# Create main memory directory
MEMORY_DIR="$HOME/deer-flow-memory"
echo "Creating main memory directory: $MEMORY_DIR"
mkdir -p "$MEMORY_DIR"

# Create core files
echo "Creating core memory files..."

# Hot memory (always loaded, ≤100 lines)
cat > "$MEMORY_DIR/hot.md" << 'EOF'
# Hot Memory - Always Loaded

This file contains the most frequently accessed patterns and corrections (≤100 lines).

## Instructions
- Keep this file under 100 lines total
- Only include patterns that are actively used
- Review and rotate patterns regularly
- Add date stamps for pattern effectiveness

## Current Hot Patterns

EOF

# Corrections memory (last 50 corrections)
cat > "$MEMORY_DIR/corrections.md" << 'EOF'
# Corrections Memory - Last 50 Corrections

This file tracks the most recent corrections for pattern learning.

## Instructions
- Keep only the last 50 corrections
- Include context about the correction
- Note the original issue and solution
- Add effectiveness metrics

## Recent Corrections

EOF

# Index and stats
cat > "$MEMORY_DIR/index.md" << 'EOF'
# Memory Index and Statistics

This file provides an overview of the memory system status and statistics.

## System Overview
- **Memory Directory**: $MEMORY_DIR
- **Last Updated**: $(date)
- **Total Files**: $(find "$MEMORY_DIR" -type f | wc -l)
- **Total Size**: $(du -sh "$MEMORY_DIR" | cut -f1)

## Memory Utilization

### Hot Tier
- **Current Lines**: $(wc -l < "$MEMORY_DIR/hot.md" 2>/dev/null || echo "0")
- **Limit**: 100 lines
- **Utilization**: $(echo "scale=1; $(wc -l < "$MEMORY_DIR/hot.md" 2>/dev/null || echo "0") * 100 / 100" | bc)% of limit

### Corrections Tier
- **Current Entries**: $(grep -c "^## " "$MEMORY_DIR/corrections.md" 2>/dev/null || echo "0")
- **Limit**: 50 entries
- **Utilization**: $(echo "scale=1; $(grep -c "^## " "$MEMORY_DIR/corrections.md" 2>/dev/null || echo "0") * 100 / 50" | bc)% of limit

### Directories
- **Projects**: $(find "$MEMORY_DIR/projects" -type d 2>/dev/null | wc -l) active
- **Domains**: $(find "$MEMORY_DIR/domains" -type d 2>/dev/null | wc -l) active
- **Templates**: $(find "$MEMORY_DIR/templates" -type d 2>/dev/null | wc -l) active
- **Archive**: $(find "$MEMORY_DIR/archive" -type d 2>/dev/null | wc -l) archived

## Health Metrics
- **Last Health Check**: $(date)
- **Status**: Active
- **Conflicts**: 0
- **Warnings**: 0

## Memory Configuration
- **Hot Tier Limit**: 100 lines
- **Corrections Limit**: 50 entries
- **Auto-Compression**: Enabled
- **Conflict Resolution**: Enabled
- **Context Loading**: Enabled
EOF

# Create directory structure
echo "Creating directory structure..."

# Projects directory
mkdir -p "$MEMORY_DIR/projects"
for project in current active; do
    mkdir -p "$MEMORY_DIR/projects/$project"
    cat > "$MEMORY_DIR/projects/$project/patterns.md" << 'EOF'
# Project Patterns

This file contains patterns specific to this project.

## Project-Specific Patterns

EOF
    cat > "$MEMORY_DIR/projects/$project/stats.md" << 'EOF'
# Project Statistics

## Project Stats
- **Created**: $(date)
- **Patterns**: 0
- **Last Updated**: $(date)
- **Effectiveness**: N/A

## Pattern Usage
EOF
done

# Domains directory
mkdir -p "$MEMORY_DIR/domains"
for domain in code writing comms research; do
    mkdir -p "$MEMORY_DIR/domains/$domain"
    cat > "$MEMORY_DIR/domains/$domain/patterns.md" << 'EOF'
# Domain Patterns

This file contains patterns specific to the $domain domain.

## Domain-Specific Patterns

EOF
    cat > "$MEMORY_DIR/domains/$domain/stats.md" << 'EOF'
# Domain Statistics

## Domain Stats
- **Created**: $(date)
- **Domain**: $domain
- **Patterns**: 0
- **Last Updated**: $(date)
- **Effectiveness**: N/A

## Pattern Usage
EOF
done

# Archive directory
mkdir -p "$MEMORY_DIR/archive/$(date +%Y-%m-%d)"

# Templates directory
mkdir -p "$MEMORY_DIR/templates"
for template in basic project analysis research; do
    mkdir -p "$MEMORY_DIR/templates/$template"
    cat > "$MEMORY_DIR/templates/$template/structure.md" << 'EOF'
# Template Structure

This file defines the structure for the $template template.

## Template Structure
- **Purpose**: [Define purpose]
- **Components**: [List components]
- **Patterns**: [List included patterns]

EOF
    cat > "$MEMORY_DIR/templates/$template/patterns.md" << 'EOF'
# Template Patterns

This file contains patterns included in the $template template.

## Template Patterns

EOF
done

# Create validation script
cat > "$MEMORY_DIR/validate_memory.sh" << 'EOF'
#!/bin/bash

# Memory System Validation Script

echo "Validating Deer Flow Memory System..."

# Check main directory
if [ ! -d "$HOME/deer-flow-memory" ]; then
    echo "ERROR: Memory directory not found"
    exit 1
fi

# Check core files
CORE_FILES=("hot.md" "corrections.md" "index.md")
for file in "${CORE_FILES[@]}"; do
    if [ ! -f "$HOME/deer-flow-memory/$file" ]; then
        echo "ERROR: Core file $file not found"
        exit 1
    fi
done

# Check line count for hot.md
HOT_LINES=$(wc -l < "$HOME/deer-flow-memory/hot.md" 2>/dev/null || echo "0")
if [ "$HOT_LINES" -gt 100 ]; then
    echo "WARNING: hot.md exceeds 100 lines ($HOT_LINES lines)"
fi

# Check entries in corrections.md
CORRECTIONS_COUNT=$(grep -c "^## " "$HOME/deer-flow-memory/corrections.md" 2>/dev/null || echo "0")
if [ "$CORRECTIONS_COUNT" -gt 50 ]; then
    echo "WARNING: corrections.md exceeds 50 entries ($CORRECTIONS_COUNT entries)"
fi

# Check directory structure
DIRS=("projects" "domains" "archive" "templates")
for dir in "${DIRS[@]}"; do
    if [ ! -d "$HOME/deer-flow-memory/$dir" ]; then
        echo "ERROR: Directory $dir not found"
        exit 1
    fi
done

echo "Memory system validation passed!"
echo "Hot tier: $HOT_LINES/100 lines"
echo "Corrections: $CORRECTIONS_COUNT/50 entries"
echo "Directories: $(find "$HOME/deer-flow-memory" -type d | wc -l) total"
EOF

# Make validation script executable
chmod +x "$MEMORY_DIR/validate_memory.sh"

# Run validation
echo "Running validation..."
bash "$MEMORY_DIR/validate_memory.sh"

echo "Deer Flow Memory System setup complete!"
echo "Memory directory: $MEMORY_DIR"
echo "To validate: $MEMORY_DIR/validate_memory.sh"