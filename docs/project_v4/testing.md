# LDUP v4 Testing Strategy

**Goal:** Ensure correctness through **property-based testing** (hypothesis), unit tests, and integration tests.

---

## Test Pyramid

```
                    ┌─────────────────┐
                    │  Integration    │  ← Full pipeline on real docs
                    │    Tests        │
                    ├─────────────────┤
                    │   Property      │  ← hypothesis: edge cases
                    │     Tests       │
                    ├─────────────────┤
                    │   Unit Tests    │  ← Individual modules
                    └─────────────────┘
```

---

## 1. Property-Based Testing (hypothesis)

### What is Property-Based Testing?

Traditional unit tests check **specific examples**:
```python
def test_parse_article_number():
    text = "Статья 123."
    result = parse_article_number(text)
    assert result == "123"
```

Property-based tests check **invariants across ALL inputs**:
```python
from hypothesis import given, strategies as st

@given(st.from_regex(r"Статья \d+\.", fullmatch=True))
def test_parse_article_number_always_works(text):
    """Should handle ANY valid article number pattern."""
    result = parse_article_number(text)
    assert result.isdigit()  # Property: result is always digits
    assert 1 <= len(result) <= 10  # Property: reasonable length
```

### Why hypothesis?

| Aspect | Unit Tests | hypothesis |
|--------|------------|------------|
| Coverage | Examples you think of | 100-1000 auto-generated cases |
| Edge cases | Manual (empty, None, huge) | Automatic |
| Shrinking | Manual (find minimal case) | Automatic (finds minimal failing case) |
| Confidence | Low (5-10 examples) | High (exhaustive) |
| Debugging | "Which case failed?" | "Here's the minimal failing case" |

### hypothesis Strategy Definitions

#### Text Strategies
```python
import string
from hypothesis import strategies as st

# Cyrillic text
cyrillic_text = st.text(
    alphabet="абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ" + string.whitespace + string.punctuation,
    min_size=1,
    max_size=1000
)

# Legal document structure patterns
article_pattern = st.from_regex(r"Статья \d+\.", fullmatch=True)
chapter_pattern = st.from_regex(r"Глава [IVXLCDM]+\.", fullmatch=True)
clause_pattern = st.from_regex(r"\d+\.\d+", fullmatch=True)

# Modality expressions
modality_text = st.sampled_from([
    "запрещается",
    "разрешается",
    "обязан",
    "должен",
    "не запрещается",  # Double negative
    "запрещается не",  # Double negative
])
```

#### Domain Object Strategies
```python
from pydantic import BaseModel
from hypothesis import strategies as st

class LegalDocument(BaseModel):
    text: str
    source_type: str

# Build legal documents from strategies
legal_document_strategy = st.builds(
    LegalDocument,
    text=cyrillic_text,
    source_type=st.sampled_from(["consultantplus", "garant", "raw"])
)
```

### Critical Property Tests

#### Parser Properties
```python
from hypothesis import given, settings

@given(cyrillic_text)
@settings(max_examples=1000)  # Test 1000 cases
def test_parser_never_crashes(text):
    """Parser should NEVER crash on ANY input text."""
    result = parser.parse(text)
    assert result is not None  # Property: always returns something
    assert isinstance(result, ParsedDocument)  # Property: correct type

@given(cyrillic_text)
def test_parser_preserves_text(text):
    """Parser should preserve original text."""
    result = parser.parse(text)
    assert result.original_text == text  # Property: text is preserved

@given(st.lists(article_pattern, min_size=0, max_size=100))
def test_article_extraction(articles):
    """Should extract all articles from text."""
    text = "\n".join(articles)
    result = parser.extract_articles(text)
    assert len(result.articles) == len(articles)  # Property: count matches
```

#### Structural Properties
```python
@given(legal_document_strategy)
def test_structure_hierarchy(doc):
    """Structure should always be valid hierarchy."""
    result = parser.parse_structure(doc.text)
    assert result is not None

    # Property: Root has no parent
    assert result.parent is None

    # Property: All children have valid parent pointers
    for chapter in result.chapters:
        assert chapter.parent == result
        for article in chapter.articles:
            assert article.parent == chapter
            for clause in article.clauses:
                assert clause.parent == article

@given(legal_document_strategy)
def test_article_numbering(doc):
    """Article numbers should be extractable."""
    result = parser.parse_structure(doc.text)
    for article in result.articles:
        assert article.number.isdigit()  # Property: number is digits
        assert 1 <= int(article.number) <= 9999  # Property: reasonable range
```

#### Semantic Properties
```python
@given(modality_text, cyillic_text)
def test_modality_classification(modality, context):
    """Modality classifier should handle ANY modality expression."""
    text = f"{context} {modality}"
    result = semantic_classifier.classify(text)
    assert result.modality in ["permission", "prohibition", "obligation"]
    assert 0 <= result.confidence <= 1  # Property: valid confidence

@given(st.data())
def test_double_negation(data):
    """Double negatives should strengthen prohibition."""
    text = data.draw(st.sampled_from([
        "запрещается не курить",
        "не разрешается не выполнять",
    ]))
    result = semantic_classifier.classify(text)
    # Property: double negative → stronger modality
    assert result.modality in ["prohibition_strong", "obligation_strong"]
```

#### Temporal Properties
```python
from datetime import datetime, timedelta
from hypothesis import strategies as st

date_strategy = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 12, 31)
)

@given(date_strategy, date_strategy)
def test_valid_intervals(valid_from, valid_to):
    """Valid intervals should have valid_from < valid_to."""
    # Swap if needed
    if valid_from >= valid_to:
        valid_from, valid_to = valid_to, valid_from

    interval = TemporalInterval(valid_from=valid_from, valid_to=valid_to)
    result = temporal_validator.validate(interval)

    # Property: valid interval passes validation
    assert result.is_valid
    assert result.valid_from < result.valid_to

@given(date_strategy)
def test_effective_date(date):
    """Effective date should be extractable."""
    text = f"Вступает в силу с {date.strftime('%d.%m.%Y')}"
    result = temporal_extractor.extract(text)
    assert result.effective_date == date  # Property: exact match
```

#### Serialization Properties
```python
from adaptix import Retort

@given(st.builds(StructuralRule))
def test_serialization_roundtrip(rule):
    """Serialization should be lossless."""
    retort = Retort()

    # Serialize
    serialized = retort.dump(rule)

    # Deserialize
    deserialized = retort.load(serialized, StructuralRule)

    # Property: roundtrip preserves all fields
    assert deserialized == rule
    assert deserialized.pattern == rule.pattern
    assert deserialized.priority == rule.priority
```

### hypothesis Settings

```python
# Standard settings
@settings(max_examples=100)  # Default: 100 cases

# Fast tests (CI/CD)
@settings(max_examples=20, deadline=timedelta(milliseconds=100))

# Thorough tests (nightly)
@settings(max_examples=1000, deadline=timedelta(seconds=1))

# Disable deadline for slow LLM calls
@settings(max_examples=50, deadline=None)

# Custom profiles
hypothesis.profile("ci", max_examples=20, deadline=timedelta(milliseconds=100))
hypothesis.profile("dev", max_examples=100, deadline=None)
hypothesis.profile("stress", max_examples=5000, deadline=None)
```

### Running hypothesis Tests

```bash
# Run all property tests
pytest tests/property/

# Run specific test
pytest tests/property/test_parser.py::test_parser_never_crashes

# With profile
hypothesis profile ci run pytest tests/property/

# Generate failing examples to file
pytest --hypothesis-seed=1234 tests/property/

# Verbose output
pytest -vv tests/property/
```

---

## 2. Unit Tests

### What to Unit Test

| Module | Test Focus | Mock |
|--------|------------|------|
| **Document Ingester** | Parse WordML → text + metadata | Mock file system |
| **Source Detector** | Detect consultantplus/garant/raw | Mock patterns |
| **Structural Bootstrap** | Chapter/Article/Part/Clause parsing | Mock LLM |
| **Semantic Classifier** | Modality classification | Mock LLM |
| **Temporal Resolver** | Date/interval extraction | Mock LLM |
| **HCO Cache** | Cache hit/miss logic | Mock cache backend |
| **TCGR** | Causal graph construction | Mock graph DB |
| **CrossRef** | Reference resolution | Mock graph DB |
| **Validators** | Pydantic validation | No mock needed |
| **Rule Compiler** | Pydantic → DSPy compilation | Mock DSPy |

### Example: Unit Test with Mocks

```python
import pytest
from unittest.mock import Mock, patch

def test_structural_bootstrap():
    # Arrange
    mock_llm = Mock()
    mock_llm.return_value = ParsedStructure(
        chapters=[Chapter(id=1, title="Test")]
    )

    # Act
    with patch('dspy.settings.context', llm=mock_llm):
        result = structural_module.parse(text="Test document")

    # Assert
    assert len(result.chapters) == 1
    assert result.chapters[0].title == "Test"
    mock_llm.assert_called_once()  # Verify LLM was called

def test_hco_cache_miss():
    # Arrange
    cache_key = "abc123"
    hco_cache.set(cache_key, None)  # Empty cache

    # Act
    result = hco_cache.get_or_compute(
        key=cache_key,
        compute_fn=lambda: semantic_result
    )

    # Assert
    assert result == semantic_result
    # Verify compute_fn was called (cache miss)
```

### Coverage Goals

```bash
# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Target: 90%+ for custom LDUP modules
# Note: DSPy modules are external, no coverage needed
```

---

## 3. Integration Tests

### What to Integration Test

| Test | Purpose | Real Data? |
|------|---------|------------|
| **Full pipeline** | End-to-end parsing | Yes (sample docs) |
| **Source-specific** | ConsultantPlus, Garant, raw | Yes (sample docs) |
| **Self-improvement** | Feedback → Rule → Activation | Yes (simulated) |
| **Export formats** | AKN, LegalDocML-RU | Yes (validate schemas) |
| **Graph storage** | FalkorDB/Graphiti | Yes (test DB) |

### Example: Integration Test

```python
import pytest
from pathlib import Path

@pytest.mark.integration
def test_full_pipeline_on_sample_document():
    # Arrange
    sample_doc = Path("tests/fixtures/44-fz-sample.docx")

    # Act
    result = full_pipeline.parse(sample_doc)

    # Assert
    assert result.structure.chapters  # Has structure
    assert result.semantics  # Has semantics
    assert result.temporals  # Has temporals
    assert len(result.validation_errors) == 0  # No errors

@pytest.mark.integration
def test_export_to_akn_validates():
    # Arrange
    sample_doc = Path("tests/fixtures/44-fz-sample.docx")
    result = full_pipeline.parse(sample_doc)

    # Act
    akn_xml = export_to_akn(result)

    # Assert
    from lxml import etree
    tree = etree.fromstring(akn_xml)
    # Validate against AKN schema
    schema.validate(tree)
```

### Running Integration Tests

```bash
# Run integration tests only
pytest -m integration

# Run with real LLM (set API key first)
export OPENAI_API_KEY="sk-..."
pytest -m integration --llm-real

# Run without LLM (use mocks)
pytest -m integration --llm-mock
```

---

## 4. Regression Tests

### Golden Corpus Approach

```python
# tests/regression/test_golden_corpus.py

GOLDEN_CORPUS = Path("tests/fixtures/golden/")

@pytest.mark.regression
def test_regression_on_golden_corpus():
    """Ensure output matches expected golden corpus."""
    for sample_file in GOLDEN_CORPUS.glob("*.json"):
        # Load golden output
        golden = json.loads(sample_file.read_text())
        input_doc = golden["input"]
        expected_output = golden["expected_output"]

        # Parse
        actual_output = full_pipeline.parse(input_doc)

        # Assert
        assert actual_output == expected_output, f"Regression in {sample_file}"
```

### Regression Test Workflow

1. **Initial**: Run on corpus, save outputs as "golden"
2. **After change**: Run again, compare to golden
3. **If diff**: Investigate if it's a bug or improvement
4. **If improvement**: Update golden corpus
5. **If bug**: Fix code

---

## 5. Test Organization

```
tests/
├── unit/
│   ├── test_ingester.py
│   ├── test_source_detector.py
│   ├── test_structural.py
│   ├── test_semantic.py
│   ├── test_temporal.py
│   ├── test_hco_cache.py
│   ├── test_tcgr.py
│   ├── test_crossref.py
│   ├── test_validators.py
│   └── test_rule_compiler.py
├── property/
│   ├── test_parser.py
│   ├── test_structure.py
│   ├── test_semantic.py
│   ├── test_temporal.py
│   └── test_serialization.py
├── integration/
│   ├── test_full_pipeline.py
│   ├── test_sources.py
│   ├── test_self_improvement.py
│   ├── test_exports.py
│   └── test_graph_storage.py
├── regression/
│   └── test_golden_corpus.py
└── fixtures/
    ├── unit/
    ├── integration/
    └── golden/
```

---

## 6. Running Tests

### Command Summary

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Property tests only
pytest tests/property/

# Integration tests only
pytest -m integration

# Regression tests only
pytest -m regression

# With coverage
pytest --cov=src --cov-report=html

# Parallel (pytest-xdist)
pytest -n auto

# Verbose
pytest -vv

# Stop on first failure
pytest -x

# Run failed tests only
pytest --lf

# With hypothesis profile
hypothesis profile ci run pytest
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run unit tests
        run: uv run pytest tests/unit/ --cov=src
      - name: Run property tests (CI profile)
        run: uv run hypothesis profile ci run pytest tests/property/
      - name: Run integration tests (mock LLM)
        run: uv run pytest -m integration --llm-mock
```

---

## 7. Testing Best Practices

### DO ✅
- Use hypothesis for critical functions (parsers, validators)
- Mock LLM calls in unit tests (avoid cost, latency)
- Use real data in integration tests (catch real-world issues)
- Maintain golden corpus for regression
- Aim for 90%+ coverage on custom code

### DON'T ❌
- Don't test external libraries (DSPy, Pydantic, adaptix)
- Don't use real LLM calls in unit tests (slow, expensive)
- Don't ignore flaky tests (fix or disable)
- Don't commit without running tests locally

---

## References

- hypothesis docs: https://hypothesis.readthedocs.io
- pytest docs: https://docs.pytest.org
- pydantic testing: https://docs.pydantic.dev/concepts/testing
