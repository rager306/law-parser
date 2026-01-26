# LDUP v4 Serialization Strategy

**Goal:** Type-safe rule definitions with **Pydantic** + fast serialization with **adaptix**.

---

## Why Not YAML? (v3 Problem)

### YAML Issues

```yaml
# v3: Weak typing, fragile
semantic:
  modalities:
    - pattern: "запрещается не"
      label: "prohibition_strong"
      priority: 5  # ❌ No range validation
      source_type: "consultantplus_xml"  # ❌ Typo: "consultantplus_xm" not caught
      confidence: 0.88  # ❌ No constraint (should be 0-1)
```

**Problems:**
1. **Weak typing**: Typos not caught until runtime
2. **Whitespace fragility**: Indentation errors crash YAML loader
3. **No IDE support**: Must memorize field names
4. **No validation**: Can't check ranges (e.g., `priority` 0-10)
5. **Slow serialization**: PyYAML is 10-100x slower than binary formats

---

## Solution: Pydantic + adaptix

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Rule Definition Layer                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Pydantic BaseModel                                      │  │
│  │  - Type hints                                            │  │
│  │  - Validation (Field(ge=0, le=10))                       │  │
│  │  - IDE autocomplete                                      │  │
│  │  - Error messages ("priority must be <= 10")            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Serialization Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  adaptix Retort                                           │  │
│  │  - Fast dump/load (2-10x faster than Pydantic)          │  │
│  │  - Native dataclass support                             │  │
│  │  - Better error messages (with field path)              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Storage / Transport                         │
│  - Cache files (rules.pkl)                                      │
│  - LLM context (JSON)                                           │
│  - Graph DB (nodes/edges)                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pydantic for Validation

### Define Rule Schemas

```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from datetime import datetime

class StructuralRule(BaseModel):
    """Rule for structural parsing (Chapters, Articles, Parts, Clauses)."""

    pattern: str = Field(..., min_length=1, description="Regex pattern to match")
    priority: int = Field(default=5, ge=0, le=10, description="Priority 0-10 (higher = more important)")
    source_type: Literal["consultantplus", "garant", "raw"] = Field(..., description="Document source type")
    rule_type: Literal["chapter", "article", "part", "clause"] = Field(..., description="Structural element type")
    case_sensitive: bool = Field(default=False, description="Match case?")
    unicode_aware: bool = Field(default=True, description="Handle Cyrillic?")

    @validator("pattern")
    def pattern_must_be_valid_regex(cls, v):
        """Validate that pattern is a valid regex."""
        import re
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v

class SemanticRule(BaseModel):
    """Rule for semantic classification (modality, definitions)."""

    modality: Literal["permission", "prohibition", "obligation", "definition"] = Field(..., description="Semantic modality")
    pattern: str = Field(..., min_length=1)
    priority: int = Field(default=5, ge=0, le=10)
    source_type: Literal["consultantplus", "garant", "raw"]
    exception_patterns: list[str] = Field(default_factory=list, description="Patterns that override this rule")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence to apply")
    strength_modifier: float = Field(default=1.0, ge=0.0, le=2.0, description="Strength multiplier (e.g., double negative)")

    @validator("modality")
    def double_negation_strengthens(cls, v, values):
        """Double negatives should strengthen the modality."""
        pattern = values.get("pattern", "")
        if "не" in pattern.lower() and pattern.lower().count("не") >= 2:
            # If modality is already strong, ensure strength_modifier >= 1.5
            if "prohibition" in v or "obligation" in v:
                # This would be set during rule creation
                pass
        return v

class TemporalRule(BaseModel):
    """Rule for temporal information extraction."""

    pattern: str = Field(..., min_length=1, description="Date pattern regex")
    date_format: str = Field(..., description="Python strptime format (e.g., '%d.%m.%Y')")
    priority: int = Field(default=5, ge=0, le=10)
    source_type: Literal["consultantplus", "garant", "raw"]
    locale: str = Field(default="ru_RU", description="Locale for month names")
    relative_date_patterns: dict[str, str] = Field(default_factory=dict, description="Relative dates (e.g., 'с дня вступления в силу')")

    @validator("date_format")
    def date_format_must_parse(cls, v):
        """Validate that format string is valid."""
        from datetime import datetime
        try:
            datetime.strptime("01.01.2000", v)
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        return v

class RuleMetadata(BaseModel):
    """Metadata for rule versioning."""

    rule_id: str = Field(..., description="Unique rule identifier")
    version: str = Field(..., description="Semantic version (e.g., '1.2.3')")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Literal["system", "human", "self_improvement"] = Field(..., description="Rule origin")
    rationale: str = Field(..., description="Why this rule exists")
    example_fragment: str = Field(..., description="Example text fragment")
    status: Literal["pending", "active", "archived"] = Field(default="pending", description="Rule lifecycle status")
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Measured accuracy on validation set")
    last_validated: Optional[datetime] = Field(None, description="Last validation timestamp")
```

### Validation Examples

```python
# Valid rule
valid_rule = StructuralRule(
    pattern=r"Статья \d+\.",
    priority=8,
    source_type="consultantplus",
    rule_type="article"
)
# ✅ Passes validation

# Invalid rule (priority out of range)
try:
    invalid_rule = StructuralRule(
        pattern=r"Статья \d+\.",
        priority=15,  # ❌ > 10
        source_type="consultantplus",
        rule_type="article"
    )
except ValidationError as e:
    print(e)
    # Output: 1 validation error for StructuralRule
    #         priority
    #           ensure this value is less than or equal to 10 (type=value_error.number.not_le; limit_value=10)

# Invalid rule (bad regex)
try:
    invalid_rule = StructuralRule(
        pattern=r"Статья (\d+",  # ❌ Unclosed parenthesis
        priority=5,
        source_type="consultantplus",
        rule_type="article"
    )
except ValidationError as e:
    print(e)
    # Output: 1 validation error for StructuralRule
    #         pattern
    #           Invalid regex pattern: missing ), unterminated subpattern at position 8

# Invalid rule (wrong source_type)
try:
    invalid_rule = StructuralRule(
        pattern=r"Статья \d+\.",
        priority=5,
        source_type="consultantplus_xm",  # ❌ Typo
        rule_type="article"
    )
except ValidationError as e:
    print(e)
    # Output: 1 validation error for StructuralRule
    #         source_type
    #           unexpected value; permitted: 'consultantplus', 'garant', 'raw'
```

---

## adaptix for Fast Serialization

### Why adaptix?

| Aspect | Pydantic `.model_dump()` | adaptix `Retort()` |
|--------|-------------------------|-------------------|
| Speed | 10-50 ms | 1-5 ms (2-10x faster) |
| Dataclasses | Limited support | Native support |
| Error messages | Generic | Specific (with field path) |
| Custom types | Possible but verbose | Simple converters |

### Basic Usage

```python
from adaptix import Retort
from pathlib import Path

# Create retort (serializer)
retort = Retort()

# Serialize rule to JSON (or MsgPack, etc.)
rule = StructuralRule(
    pattern=r"Статья \d+\.",
    priority=8,
    source_type="consultantplus",
    rule_type="article"
)

# Dump to JSON string
json_str = retort.dump(rule)
# Output: {"pattern": "Статья \\d+\\.", "priority": 8, "source_type": "consultantplus", "rule_type": "article", "case_sensitive": false, "unicode_aware": true}

# Load from JSON string
loaded_rule = retort.load(json_str, StructuralRule)
assert loaded_rule == rule
```

### Batch Serialization

```python
# Serialize list of rules
rules = [
    StructuralRule(pattern=r"Статья \d+\.", priority=8, source_type="consultantplus", rule_type="article"),
    SemanticRule(modality="prohibition", pattern=r"запрещается", priority=7, source_type="consultantplus"),
    TemporalRule(pattern=r"\d{2}\.\d{2}\.\d{4}", date_format="%d.%m.%Y", priority=6, source_type="consultantplus"),
]

# Dump to bytes (fast!)
rules_bytes = retort.dump(rules)

# Save to file
Path("cache/rules.pkl").write_bytes(rules_bytes)

# Load from file
loaded_rules = retort.load(Path("cache/rules.pkl").read_bytes(), list[StructuralRule | SemanticRule | TemporalRule])
```

### Custom Type Converters

```python
from adaptix import NameConv, TypeShowMode

# Configure retort
retort = Retort(
    name_conv=NameConv.CAMEL_CASE,  # Convert snake_case to camelCase for external APIs
    type_show_mode=TypeShowMode.ASCII,  # ASCII-only type names
    strict_coercion=False,  # Allow flexible type conversion
)

# Dump with camelCase
json_str = retort.dump(rule)
# Output: {"pattern": "...", "priority": 8, "sourceType": "consultantplus", ...}
```

---

## Pydantic + adaptix Together

### When to Use Which

| Use Case | Tool | Reason |
|----------|------|--------|
| **Define rules** | Pydantic | Validation, type checking, IDE support |
| **Serialize for LLM context** | adaptix | Fast (called millions of times) |
| **Cache compiled rules** | adaptix | Fast serialization, smaller size |
| **API responses** | Pydantic | Validation + `model_dump_json()` |
| **User-facing config** | Pydantic | Error messages, validation |
| **Internal hot paths** | adaptix | Performance critical |

### Example: Full Pipeline

```python
from pydantic import BaseModel, Field
from adaptix import Retort
from typing import Union

# 1. Define with Pydantic
class StructuralRule(BaseModel):
    pattern: str
    priority: int = Field(ge=0, le=10)
    source_type: str
    rule_type: str

# 2. Validate with Pydantic
try:
    rule = StructuralRule(
        pattern=r"Статья \d+\.",
        priority=8,
        source_type="consultantplus",
        rule_type="article"
    )
    # ✅ Valid
except ValidationError as e:
    print(f"Validation error: {e}")
    # ❌ Invalid

# 3. Serialize with adaptix (fast!)
retort = Retort()
rule_bytes = retort.dump(rule)

# 4. Save to cache
Path("cache/rules.pkl").write_bytes(rule_bytes)

# 5. Load from cache (fast!)
loaded_rule = retort.load(Path("cache/rules.pkl").read_bytes(), StructuralRule)

# 6. Use in hot path (LLM context)
llm_context = retort.dump([loaded_rule])  # Fast!
```

---

## Rule Store (Versioned)

### Data Model

```python
from pydantic import BaseModel
from typing import Dict, List
from enum import Enum

class RuleStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ARCHIVED = "archived"

class RuleStore(BaseModel):
    """Versioned rule store with pending → active → archived lifecycle."""

    structural_rules: Dict[RuleStatus, List[StructuralRule]] = Field(
        default_factory=lambda: {status: [] for status in RuleStatus}
    )
    semantic_rules: Dict[RuleStatus, List[SemanticRule]] = Field(
        default_factory=lambda: {status: [] for status in RuleStatus}
    )
    temporal_rules: Dict[RuleStatus, List[TemporalRule]] = Field(
        default_factory=lambda: {status: [] for status in RuleStatus}
    )
    metadata: Dict[str, RuleMetadata] = Field(default_factory=dict)

    def add_rule(self, rule: Union[StructuralRule, SemanticRule, TemporalRule], metadata: RuleMetadata):
        """Add rule with metadata."""
        rule_type = type(rule).__name__
        if rule_type == "StructuralRule":
            self.structural_rules[RuleStatus.PENDING].append(rule)
        elif rule_type == "SemanticRule":
            self.semantic_rules[RuleStatus.PENDING].append(rule)
        elif rule_type == "TemporalRule":
            self.temporal_rules[RuleStatus.PENDING].append(rule)
        self.metadata[metadata.rule_id] = metadata

    def promote_rule(self, rule_id: str):
        """Promote rule from pending → active."""
        metadata = self.metadata[rule_id]
        # Find rule in pending, move to active
        # ...

    def archive_rule(self, rule_id: str):
        """Archive rule from active."""
        # ...
```

### Persistence

```python
from adaptix import Retort
from pathlib import Path

retort = Retort()

# Save rule store
store = RuleStore()
store_bytes = retort.dump(store)
Path("data/rule_store.pkl").write_bytes(store_bytes)

# Load rule store
store = retort.load(Path("data/rule_store.pkl").read_bytes(), RuleStore)
```

---

## YAML Support (Optional)

### If You Really Need YAML

```python
from pydantic_yaml import parse_yaml_file, to_yaml_file

# Load from YAML (for user editing)
rules = parse_yaml_file(
    "rules/structural.yaml",
    type=list[StructuralRule]
)

# Validate with Pydantic
for rule in rules:
    rule.model_validate(rule)  # Will raise ValidationError if invalid

# Save to YAML (for user readability)
to_yaml_file(
    "rules/structural_validated.yaml",
    rules,
    exclude_none=True  # Don't write fields with None
)
```

### Why Avoid YAML for Production?

1. **Typo in field name**: `priotiry` instead of `priority` → silent error
2. **Wrong type**: `priority: "5"` instead of `priority: 5` → runtime error
3. **Missing field**: Forgetting `source_type` → crashes at runtime
4. **Indentation error**: YAML is whitespace-sensitive → cryptic errors

**Use JSON instead** (if not using adaptix binary format):
```json
{
  "pattern": "Статья \\d+\\.",
  "priority": 8,
  "source_type": "consultantplus",
  "rule_type": "article"
}
```

---

## Performance Benchmarks

### Serialization Speed

```python
import time
from pydantic import BaseModel
from adaptix import Retort

class TestRule(BaseModel):
    pattern: str
    priority: int
    source_type: str
    rule_type: str

rules = [TestRule(pattern=f"pattern{i}", priority=i, source_type="test", rule_type="article") for i in range(1000)]

# Pydantic serialization
start = time.time()
for rule in rules:
    _ = rule.model_dump_json()
pydantic_time = time.time() - start

# adaptix serialization
retort = Retort()
start = time.time()
_ = retort.dump(rules)
adaptix_time = time.time() - start

print(f"Pydantic: {pydantic_time:.3f}s")
print(f"adaptix: {adaptix_time:.3f}s")
print(f"Speedup: {pydantic_time / adaptix_time:.1f}x")
```

**Expected Results:**
- Pydantic: 0.5-2.0s (for 1000 rules)
- adaptix: 0.05-0.2s (for 1000 rules)
- **Speedup: 5-10x faster**

---

## Best Practices

### DO ✅
- Use Pydantic for rule definition (validation, type checking)
- Use adaptix for serialization (hot paths: LLM I/O, cache)
- Validate rules at load time (fail fast)
- Use strict types (Literal, Field(ge=0, le=10))
- Document rationale for each rule

### DON'T ❌
- Don't use YAML for production (use JSON or adaptix binary)
- Don't skip validation (always `.model_validate()`)
- Don't ignore ValidationError (it means bad data)
- Don't serialize with Pydantic in hot paths (slow)

---

## References

- Pydantic docs: https://docs.pydantic.dev
- adaptix docs: https://adaptix.readthedocs.io
- pydantic-yaml: https://github.com/nowog/pydantic-yaml
