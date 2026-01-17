# CLI Reference

The readwise-plus CLI provides quick access to common operations from the command line.

## Installation

Install with CLI support:

```bash
pip install readwise-plus[cli]
```

## Authentication

Set the `READWISE_API_KEY` environment variable:

```bash
export READWISE_API_KEY="your_api_key"
```

## Commands

### Highlights

```bash
# List highlights
readwise highlights list
readwise highlights list --limit 50
readwise highlights list --book-id 123
readwise highlights list --days 7
readwise highlights list --json

# Show a highlight
readwise highlights show 123456

# Export highlights
readwise highlights export
readwise highlights export --format markdown -o highlights.md
readwise highlights export --format json -o highlights.json
readwise highlights export --days 30
```

### Books

```bash
# List books
readwise books list
readwise books list --limit 50
readwise books list --category articles
readwise books list --json

# Show a book
readwise books show 12345
```

### Reader

```bash
# View inbox
readwise reader inbox
readwise reader inbox --limit 50
readwise reader inbox --json

# Save a URL
readwise reader save "https://example.com/article"

# Archive a document
readwise reader archive doc_id_here

# Get reading stats
readwise reader stats
```

### Tags

```bash
# List all tags
readwise tags list
readwise tags list --json

# Search highlights by tag
readwise tags search "python"
readwise tags search "python" --limit 50

# Find untagged highlights
readwise tags untagged
readwise tags untagged --limit 100

# Auto-tag highlights (dry run by default)
readwise tags auto-tag --pattern "TODO:" --tag "actionable"
readwise tags auto-tag --pattern "python" --tag "python" --no-dry-run

# Rename a tag
readwise tags rename "ml" "machine-learning"
readwise tags rename "ml" "machine-learning" --no-dry-run

# Merge tags
readwise tags merge "ml,ML,machine-learning" --into "machine-learning"
readwise tags merge "ml,ML" --into "machine-learning" --no-dry-run

# Delete a tag
readwise tags delete "deprecated"
readwise tags delete "deprecated" --no-dry-run

# Generate tag report
readwise tags report
readwise tags report --json
```

### Sync

```bash
# Full sync
readwise sync full

# Incremental sync
readwise sync incremental
readwise sync incremental --state-file sync.json
```

### Digests

```bash
# Daily digest
readwise digest daily
readwise digest daily --format markdown
readwise digest daily -o daily.md

# Weekly digest
readwise digest weekly
readwise digest weekly -o weekly.md

# Book digest
readwise digest book 12345
readwise digest book 12345 -o book-notes.md
```

### Version

```bash
readwise version
```

## Global Options

### JSON Output

Most commands support `--json` for machine-readable output:

```bash
readwise highlights list --json
readwise books list --json
readwise tags list --json
```

### Dry Run

Destructive tag operations default to dry run mode:

```bash
# Preview changes
readwise tags rename "old" "new"

# Apply changes
readwise tags rename "old" "new" --no-dry-run
```

## Examples

### Export Recent Highlights

```bash
# Export last week's highlights to markdown
readwise highlights export --days 7 -f markdown -o weekly-highlights.md
```

### Clean Up Old Inbox Items

```bash
# Check stale items
readwise reader stats

# See tags report to find unused tags
readwise tags report
```

### Automated Tagging

```bash
# Tag all Python-related highlights
readwise tags auto-tag -p "\bpython\b" -t "python" --no-case-sensitive

# Preview first
readwise tags auto-tag -p "\bpython\b" -t "python"
```

### Generate Weekly Review

```bash
# Create weekly digest
readwise digest weekly -o ~/Documents/weekly-review.md
```
