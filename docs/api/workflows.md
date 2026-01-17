# Workflows

Workflows provide automation utilities for common tasks.

## TagWorkflow

Utilities for tag management and automation.

```python
from readwise_sdk import ReadwiseClient
from readwise_sdk.workflows.tags import TagWorkflow, TagPattern

client = ReadwiseClient()
workflow = TagWorkflow(client)
```

### Methods

#### auto_tag_highlights

Apply automatic tagging based on patterns:

```python
from readwise_sdk.workflows.tags import TagPattern

patterns = [
    TagPattern(pattern=r"\bpython\b", tag="python"),
    TagPattern(pattern=r"TODO:", tag="actionable", match_in_notes=True),
]

# Dry run - see what would be tagged
results = workflow.auto_tag_highlights(patterns, dry_run=True)
for highlight_id, tags in results.items():
    print(f"Highlight {highlight_id}: would add {tags}")

# Apply tags
results = workflow.auto_tag_highlights(patterns, dry_run=False)
```

#### get_tag_report

Generate a report of tag usage statistics:

```python
report = workflow.get_tag_report()

print(f"Total tags: {report.total_tags}")
print(f"Total usages: {report.total_usages}")
print(f"Unused tags: {report.unused_tags}")

# Tags sorted by usage
for tag, count in report.tags_by_usage[:10]:
    print(f"  {tag}: {count}")

# Potential duplicates
for group in report.duplicate_candidates:
    print(f"Similar tags: {group}")
```

#### merge_tags

Merge multiple tags into one:

```python
# Dry run first
affected = workflow.merge_tags(
    source_tags=["ml", "ML", "machine-learning"],
    target_tag="machine-learning",
    dry_run=True,
)
print(f"Would affect {len(affected)} highlights")

# Apply merge
affected = workflow.merge_tags(
    source_tags=["ml", "ML"],
    target_tag="machine-learning",
    dry_run=False,
)
```

#### rename_tag

Rename a tag across all highlights:

```python
# Dry run
affected = workflow.rename_tag("old-name", "new-name", dry_run=True)
print(f"Would rename in {len(affected)} highlights")

# Apply rename
affected = workflow.rename_tag("old-name", "new-name", dry_run=False)
```

#### delete_tag

Delete a tag from all highlights:

```python
# Dry run
affected = workflow.delete_tag("deprecated-tag", dry_run=True)
print(f"Would delete from {len(affected)} highlights")

# Apply deletion
affected = workflow.delete_tag("deprecated-tag", dry_run=False)
```

#### get_highlights_by_tag

Get all highlights with a specific tag:

```python
highlights = workflow.get_highlights_by_tag("python")
for h in highlights:
    print(f"- {h.text[:80]}...")
```

#### get_untagged_highlights

Get all highlights without any tags:

```python
untagged = workflow.get_untagged_highlights()
print(f"Found {len(untagged)} untagged highlights")
```

## Models

### TagPattern

```python
@dataclass
class TagPattern:
    pattern: str              # Regex pattern to match
    tag: str                  # Tag to apply
    case_sensitive: bool = False
    match_in_notes: bool = True
    match_in_text: bool = True
```

### TagReport

```python
@dataclass
class TagReport:
    total_tags: int
    total_usages: int
    tags_by_usage: list[tuple[str, int]]
    unused_tags: list[str]
    duplicate_candidates: list[list[str]]
```
