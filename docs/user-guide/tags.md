# Tag Management

Tags help organize your highlights. The SDK provides powerful tools for tag management and automation.

## Basic Tag Operations

### List Tags on a Highlight

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

tags = client.v2.list_highlight_tags(highlight_id=123)
for tag in tags:
    print(f"- {tag.name}")
```

### Add a Tag

```python
client.v2.create_highlight_tag(highlight_id=123, name="important")
```

### Remove a Tag

```python
client.v2.delete_highlight_tag(highlight_id=123, tag_id=456)
```

## TagWorkflow

The `TagWorkflow` class provides advanced tag management:

```python
from readwise_sdk.workflows.tags import TagWorkflow

workflow = TagWorkflow(client)
```

### Get Tag Report

```python
report = workflow.get_tag_report()

print(f"Total tags: {report.total_tags}")
print(f"Total usages: {report.total_usages}")

print("\nTop tags:")
for name, count in report.tags_by_usage[:10]:
    print(f"  {name}: {count}")

if report.duplicate_candidates:
    print("\nPotential duplicates:")
    for group in report.duplicate_candidates:
        print(f"  {', '.join(group)}")
```

### Search by Tag

```python
highlights = workflow.get_highlights_by_tag("python")
print(f"Found {len(highlights)} highlights with tag 'python'")
```

### Find Untagged Highlights

```python
untagged = workflow.get_untagged_highlights()
print(f"Found {len(untagged)} untagged highlights")
```

## Auto-Tagging

Automatically tag highlights based on patterns:

```python
from readwise_sdk.workflows.tags import TagWorkflow, TagPattern

workflow = TagWorkflow(client)

patterns = [
    TagPattern(r"\bpython\b", "python", case_sensitive=False),
    TagPattern(r"\bmachine learning\b", "ml", case_sensitive=False),
    TagPattern(r"TODO:", "actionable", match_in_notes=True),
]

# Preview changes (dry run)
results = workflow.auto_tag_highlights(patterns, dry_run=True)
print(f"Would tag {len(results)} highlights")

# Apply changes
results = workflow.auto_tag_highlights(patterns, dry_run=False)
print(f"Tagged {len(results)} highlights")
```

### TagPattern Options

```python
TagPattern(
    pattern=r"\bkeyword\b",      # Regex pattern
    tag="tag-name",              # Tag to apply
    case_sensitive=False,        # Case insensitive matching
    match_in_text=True,          # Search in highlight text
    match_in_notes=True,         # Search in notes
)
```

## Rename Tags

Rename a tag across all highlights:

```python
# Preview
affected = workflow.rename_tag("ml", "machine-learning", dry_run=True)
print(f"Would affect {len(affected)} highlights")

# Apply
workflow.rename_tag("ml", "machine-learning", dry_run=False)
```

## Merge Tags

Combine multiple tags into one:

```python
# Preview
affected = workflow.merge_tags(
    source_tags=["ml", "ML", "machine-learning"],
    target_tag="machine-learning",
    dry_run=True,
)
print(f"Would affect {len(affected)} highlights")

# Apply
workflow.merge_tags(
    source_tags=["ml", "ML"],
    target_tag="machine-learning",
    dry_run=False,
)
```

## Delete Tags

Remove a tag from all highlights:

```python
# Preview
affected = workflow.delete_tag("deprecated", dry_run=True)
print(f"Would affect {len(affected)} highlights")

# Apply
workflow.delete_tag("deprecated", dry_run=False)
```

## CLI Commands

All tag operations are available via CLI:

```bash
# List tags with counts
readwise tags list

# Search by tag
readwise tags search "python"

# Find untagged highlights
readwise tags untagged

# Auto-tag (dry run by default)
readwise tags auto-tag --pattern "TODO:" --tag "actionable"
readwise tags auto-tag --pattern "TODO:" --tag "actionable" --no-dry-run

# Rename tag
readwise tags rename "ml" "machine-learning"
readwise tags rename "ml" "machine-learning" --no-dry-run

# Merge tags
readwise tags merge "ml,ML" --into "machine-learning"

# Delete tag
readwise tags delete "deprecated"

# Full report
readwise tags report
```

## Next Steps

- [Workflows](workflows.md)
- [CLI Reference](../cli.md)
