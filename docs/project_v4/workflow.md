# LDUP v4 Workflow

**Goal:** Define clear **2-phase execution** (compile-time vs runtime) with self-improvement loop.

---

## Phase 1: Compile-Time (Run Once)

### Purpose
Optimize DSPy prompts using training corpus, compile Pydantic rules into executable graph.

### When to Run
- **Initial setup**: First time with new corpus
- **Rule activation**: After self-improvement promotes rules to `active`
- **Model change**: When switching LLM providers or models
- **Scheduled**: Weekly/Monthly to incorporate new patterns

### Inputs
- **Training corpus**: N=100-1000 annotated legal documents
- **Base rules**: Pydantic rule definitions (StructuralRule, SemanticRule, TemporalRule)
- **DSPy configuration**: LLM provider, model settings, cache paths

### Steps

#### 1.1 Data Preparation
```python
# Load training corpus
from pathlib import Path

corpus_files = Path("data/training/").glob("*.jsonl")
documents = [load_document(f) for f in corpus_files]

# Split: 80% train, 20% validation
train_docs, val_docs = train_test_split(documents, test_size=0.2)
```

#### 1.2 GEPA Optimization (Structural)
```python
import dspy
from dspy.teleprompt.gepa import GePA

# Define structural module signature
class StructuralSignature(dspy.Signature):
    """Parse legal document structure."""
    text = dspy.InputField(desc="Document text")
    structure = dspy.OutputField(desc="Chapter/Article/Part/Clause hierarchy")

# Run GEPA optimizer
structural_module = dspy.Predict(StructuralSignature)
gepa_optimizer = GePA(metric=structural_accuracy)
optimized_structural = gepa_optimizer.compile(
    structural_module,
    trainset=train_docs,
    valset=val_docs,
    max_bootsteps=10  # Reflective evolution rounds
)
```

**Cost:** ~100-500 LLM calls per bootstep × 10 bootsteps = **1,000-5,000 LLM calls**

#### 1.3 SIMBA Optimization (Semantic)
```python
from dspy.teleprompt.simba import SIMBA

class SemanticSignature(dspy.Signature):
    """Classify semantic modality."""
    text = dspy.InputField(desc="Legal provision text")
    modality = dspy.OutputField(desc="permission/prohibition/obligation")
    confidence = dspy.OutputField(desc="Confidence score")

semantic_module = dspy.Predict(SemanticSignature)
simba_optimizer = SIMBA(metric=semantic_f1)
optimized_semantic = simba_optimizer.compile(
    semantic_module,
    trainset=train_docs,
    valset=val_docs,
    max_labeled_demos=20,  # Few-shot examples
    max_rounds=5  # Introspection rounds
)
```

**Cost:** ~50-200 LLM calls per round × 5 rounds = **250-1,000 LLM calls**

#### 1.4 MiPROv2 Optimization (Temporal)
```python
from dspy.teleprompt.mipro_optimizer_v2 import MIPROv2

class TemporalSignature(dspy.Signature):
    """Extract temporal information."""
    text = dspy.InputField(desc="Legal provision text")
    effective_date = dspy.OutputField(desc="Date when provision takes effect")
    valid_from = dspy.OutputField(desc="Validity interval start")
    valid_to = dspy.OutputField(desc="Validity interval end")

temporal_module = dspy.Predict(TemporalSignature)
mipro_optimizer = MIPROv2(metric=temporal_accuracy)
optimized_temporal = mipro_optimizer.compile(
    temporal_module,
    trainset=train_docs,
    valset=val_docs,
    num_trials=5,  # Prompt optimization trials
    max_labeled_demos=10
)
```

**Cost:** ~50-200 LLM calls per trial × 5 trials = **250-1,000 LLM calls**

#### 1.5 Rule Compilation (Pydantic → DSPy)
```python
from pydantic import BaseModel
from adaptix import Retort

# Define rule schema
class StructuralRule(BaseModel):
    pattern: str
    priority: int = Field(ge=0, le=10)
    source_type: str  # consultantplus, garant, raw

class SemanticRule(BaseModel):
    modality: str  # permission, prohibition, obligation
    exception_patterns: list[str]
    confidence_threshold: float = Field(ge=0.0, le=1.0)

# Load rules from JSON/YAML
rules = load_rules("rules/structural.json")

# Compile into DSPy instructions
compiled_rules = compile_rules_for_dspy(rules)

# Serialize with adaptix
retort = Retort()
rules_cache = retort.dump(compiled_rules)
Path("cache/rules.pkl").write_bytes(rules_cache)
```

#### 1.6 Graph Assembly & Serialization
```python
# Assemble optimized modules into graph
from dspy import Module

class LDUPGraph(Module):
    def __init__(self):
        self.structural = optimized_structural
        self.semantic = optimized_semantic
        self.temporal = optimized_temporal

    def forward(self, text):
        structure = self.structural(text=text)
        semantics = self.semantic(text=text)
        temporals = self.temporal(text=text)
        return LegalDocument(structure, semantics, temporals)

# Serialize compiled graph
graph = LDUPGraph()
Path("cache/graph.pkl").write_bytes(pickle.dumps(graph))
```

### Outputs
- `cache/graph.pkl` — Compiled DSPy graph with optimized prompts
- `cache/rules.pkl` — Serialized Pydantic rules (adaptix format)
- `logs/compile_{timestamp}.log` — Compilation trace (loguru)

### Total Compile-Time Cost
| Component | LLM Calls | Duration (at 10 req/s) |
|-----------|-----------|------------------------|
| GEPA | 1,000-5,000 | 1.7-8.3 minutes |
| SIMBA | 250-1,000 | 0.4-1.7 minutes |
| MiPROv2 | 250-1,000 | 0.4-1.7 minutes |
| **Total** | **1,500-7,000** | **2.5-11.7 minutes** |

---

## Phase 2: Runtime (Per Document)

### Purpose
Parse individual legal documents using compiled graph and rules.

### When to Run
- **On-demand**: User uploads document
- **Batch processing**: Queue of documents from scrape
- **API request**: REST endpoint receives document

### Inputs
- **Document file**: WordML (.docx), PDF, or plain text
- **Compiled graph**: `cache/graph.pkl`
- **Rules cache**: `cache/rules.pkl`

### Steps

#### 2.1 Ingestion
```python
from loguru import logger
from docx import Document

logger.bind(document_id=doc_id, stage="ingestion").info("Starting ingestion")

# Parse WordML
doc = Document(file_path)
text = "\n".join([p.text for p in doc.paragraphs])
metadata = extract_metadata(doc)  # Author, created_date, etc.

logger.bind(
    document_id=doc_id,
    text_length=len(text),
    metadata_keys=list(metadata.keys())
).debug("Ingestion complete")
```

**Logging Level:** DEBUG (full text not logged, only metadata)

#### 2.2 Source Detection
```python
SOURCE_PATTERNS = {
    "consultantplus": r"КонсультантПлюс",
    "garant": r"Гарант",
    "raw": r""  # Default
}

def detect_source(text: str, metadata: dict) -> str:
    for source, pattern in SOURCE_PATTERNS.items():
        if re.search(pattern, text) or source in metadata.get("source", ""):
            logger.bind(document_id=doc_id, source=source).info("Source detected")
            return source
    logger.bind(document_id=doc_id).warning("Unknown source, using 'raw'")
    return "raw"
```

**Logging Level:** INFO (source type), WARNING (fallback to 'raw')

#### 2.3 Structural Bootstrap (GEPA-optimized)
```python
# Load compiled graph
graph = pickle.loads(Path("cache/graph.pkl").read_bytes())

# Load rules
retort = Retort()
rules = retort.load(Path("cache/rules.pkl").read_bytes(), list[StructuralRule])

# Apply source-specific rules
source_rules = [r for r in rules if r.source_type == detected_source]

logger.bind(
    document_id=doc_id,
    num_rules=len(source_rules)
).info("Applying structural rules")

# Parse structure
structure = graph.structural(text=text)

logger.bind(
    document_id=doc_id,
    num_chapters=len(structure.chapters),
    parse_time=structure.parse_time
).info("Structure parsed")
```

**Logging Level:** INFO (progress), DEBUG (full structure)

#### 2.4 Semantic Analysis (SIMBA-optimized)
```python
# Classify modality per article
semantics = []
for article in structure.articles:
    semantic = graph.semantic(text=article.text)
    semantics.append(semantic)

    logger.bind(
        document_id=doc_id,
        article_id=article.id,
        modality=semantic.modality,
        confidence=semantic.confidence
    ).debug("Semantic classification")
```

**Logging Level:** DEBUG (per-article), INFO (summary)

#### 2.5 Temporal Resolution (MiPROv2-optimized)
```python
# Extract temporal info
temporals = []
for article in structure.articles:
    temporal = graph.temporal(text=article.text)

    # Validate intervals
    if temporal.valid_from and temporal.valid_to:
        if temporal.valid_from >= temporal.valid_to:
            logger.bind(
                document_id=doc_id,
                article_id=article.id,
                valid_from=temporal.valid_from,
                valid_to=temporal.valid_to
            ).warning("Invalid temporal interval")
            # Apply correction rule
            temporal = apply_temporal_correction_rule(temporal)

    temporals.append(temporal)
```

**Logging Level:** WARNING (invalid intervals), DEBUG (all temporals)

#### 2.6 HCO Cache Lookup
```python
# Semantic block cache
cache_key = hashlib.md5(article.text.encode()).hexdigest()
cached = hco_cache.get(cache_key)

if cached:
    logger.bind(
        document_id=doc_id,
        cache_key=cache_key,
        hit=True
    ).debug("HCO cache hit")
    semantics.append(cached.semantic)
else:
    # Compute and cache
    semantic = graph.semantic(text=article.text)
    hco_cache.set(cache_key, semantic)
    logger.bind(cache_key=cache_key, hit=False).debug("HCO cache miss")
```

**Logging Level:** DEBUG (cache hits/misses)

#### 2.7 Reasoning (TCGR + CrossRef)
```python
# TCGR: Build causal amendment links
causal_graph = tcgr.build_graph(structure, temporals)

logger.bind(
    document_id=doc_id,
    num_nodes=causal_graph.num_nodes,
    num_edges=causal_graph.num_edges
).info("Causal graph built")

# CrossRef: Resolve references
references = crossref.resolve(structure)

logger.bind(
    document_id=doc_id,
    num_references=len(references)
).info("References resolved")
```

**Logging Level:** INFO (summary), DEBUG (details)

#### 2.8 Validation (Pydantic)
```python
from pydantic import ValidationError

try:
    # Validate complete document
    validated_doc = LegalDocument(
        structure=structure,
        semantics=semantics,
        temporals=temporals,
        causal_graph=causal_graph,
        references=references
    )
    logger.bind(document_id=doc_id).info("Validation passed")

except ValidationError as e:
    logger.bind(
        document_id=doc_id,
        errors=e.error_count()
    ).error("Validation failed")
    # Queue for self-improvement
    feedback_queue.put(FeedbackEntry(
        document_id=doc_id,
        error_type="validation",
        details=str(e)
    ))
```

**Logging Level:** ERROR (validation failures), INFO (success)

#### 2.9 Export
```python
# Export to AKN
akn_xml = export_to_akn(validated_doc)
Path("output/akn/{doc_id}.xml").write_text(akn_xml)

# Export to LegalDocML-RU
ldml_xml = export_to_ldml(validated_doc)
Path("output/ldml/{doc_id}.xml").write_text(ldml_xml)

# Store in graph DB
graph_storage.store(validated_doc)

logger.bind(
    document_id=doc_id,
    akn_size=len(akn_xml),
    ldml_size=len(ldml_xml)
).info("Export complete")
```

**Logging Level:** INFO (export success), ERROR (failures)

### Total Runtime Cost
| Step | LLM Calls | Duration (at 10 req/s) |
|------|-----------|------------------------|
| Ingestion | 0 | <1s |
| Source Detection | 0 | <1s |
| Structural | 5-15 | 0.5-1.5s |
| Semantic | 5-15 | 0.5-1.5s |
| Temporal | 5-10 | 0.5-1.0s |
| Reasoning | 0 | <1s |
| Validation | 0 | <1s |
| Export | 0 | <1s |
| **Total** | **15-40** | **3-8 seconds** |

---

## Self-Improvement Loop (Background)

### Purpose
Automatically detect errors, generate candidate rules, validate, and activate.

### When to Run
- **Continuous**: Background daemon monitors feedback queue
- **Triggered**: When error threshold exceeded
- **Scheduled**: Daily/weekly batch processing

### Steps

#### 3.1 Error Detection (SRC/TRC/STC)
```python
from loguru import logger

# Structural: STC
for article in validated_doc.structure.articles:
    if not article.parent_chapter:
        logger.bind(
            document_id=doc_id,
            article_id=article.id
        ).warning("STC: Article without parent chapter")
        stc_controller.report_issue(
            error_type="orphan_article",
            text_fragment=article.text,
            expected="parent_chapter != None"
        )

# Semantic: SRC
for semantic in validated_doc.semantics:
    if "запрещается не" in semantic.text and semantic.modality == "permission":
        logger.bind(
            document_id=doc_id,
            article_id=semantic.article_id
        ).warning("SRC: Double negation misclassified")
        src_controller.report_issue(
            error_type="double_negation_misclassification",
            text_fragment=semantic.text,
            predicted="permission",
            expected="prohibition"
        )

# Temporal: TRC
for temporal in validated_doc.temporals:
    if temporal.valid_from and temporal.valid_to and temporal.valid_from >= temporal.valid_to:
        logger.bind(
            document_id=doc_id,
            article_id=temporal.article_id
        ).error("TRC: Invalid interval")
        trc_controller.report_issue(
            error_type="invalid_interval",
            text_fragment=temporal.text,
            expected="valid_from < valid_to"
        )
```

#### 3.2 Feedback Collection
```python
feedback_entry = FeedbackEntry(
    timestamp=datetime.now(timezone.utc),
    error_type="semantic_misclassification",
    module="simba",
    text_fragment="запрещается не",
    expected="prohibition",
    predicted="permission",
    confidence=0.88,
    source_id="consultantplus_xml",
    example_fragment="Статья 33, часть 1, пункт 1"
)

feedback_queue.put(feedback_entry)
```

#### 3.3 Policy Optimizer
```python
# Collect feedback batch
feedback_batch = feedback_queue.get_batch(min_size=10)

# Group by error_type
by_error_type = groupby(feedback_batch, key=lambda f: f.error_type)

# Prioritize by ΔAccuracy/ΔLLM/ΔConflict
prioritized = policy_optimizer.prioritize(by_error_type)

logger.bind(
    batch_size=len(feedback_batch),
    prioritized_count=len(prioritized)
).info("Policy optimization complete")
```

#### 3.4 Rule Generation (Pydantic)
```python
# Generate candidate rule
candidate_rule = SemanticRule(
    pattern="запрещается не",
    modality="prohibition_strong",
    exception_patterns=[],
    confidence_threshold=0.7,
    source_type="consultantplus_xml",
    rationale="double negation strengthens prohibition",
    status="pending"
)

# Validate with Pydantic
try:
    validated_rule = SemanticRule.model_validate(candidate_rule)
    logger.bind(rule_pattern=validated_rule.pattern).info("Rule validated")
except ValidationError as e:
    logger.bind(errors=e.errors()).error("Rule validation failed")
```

#### 3.5 Simulation & Testing
```python
# Test on mini-corpus
mini_corpus = load_validation_set(n=20)
accuracy_before = evaluate_on_corpus(graph, mini_corpus)
accuracy_after = evaluate_with_rule(graph, validated_rule, mini_corpus)

improvement = accuracy_after - accuracy_before

logger.bind(
    rule_pattern=validated_rule.pattern,
    accuracy_before=accuracy_before,
    accuracy_after=accuracy_after,
    improvement=improvement
).info("Simulation complete")
```

#### 3.6 Safety Rails
```python
MAX_ITERATIONS = 10
MIN_IMPROVEMENT_THRESHOLD = 0.01  # 1%
MAX_ACCURACY_DROP = 0.05  # 5%

for iteration in range(MAX_ITERATIONS):
    # ... generate and test rule ...

    if improvement < MIN_IMPROVEMENT_THRESHOLD:
        logger.info("Converged: improvement below threshold")
        break

    if accuracy_after < accuracy_before * (1 - MAX_ACCURACY_DROP):
        logger.warning("Accuracy dropped >5%, rolling back")
        rollback_to_last_good_state()
        break  # Circuit breaker

    if accuracy_after > accuracy_before:
        activate_rule(validated_rule)
        logger.bind(rule_pattern=validated_rule.pattern).info("Rule activated")
```

#### 3.7 Rule Activation & Recompile Trigger
```python
# Update rule status
validated_rule.status = "active"
rule_store.update(validated_rule)

# Trigger recompile if threshold reached
if rule_store.count_active() % 10 == 0:
    logger.info("Rule batch threshold reached, triggering recompile")
    trigger_compile_time_optimization()
```

---

## Error Handling

### Retry Strategy
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def parse_with_retry(text: str):
    try:
        return graph.structural(text=text)
    except Exception as e:
        logger.bind(error=str(e)).warning("Parse failed, retrying")
        raise
```

### Fallback Strategy
```python
# If optimized module fails, fall back to base module
try:
    structure = optimized_structural(text=text)
except Exception as e:
    logger.bind(error=str(e)).error("Optimized module failed, using fallback")
    structure = base_structural_module(text=text)
```

---

## Logging Strategy (loguru)

### Configuration
```python
from loguru import logger

# Remove default handler
logger.remove()

# Console (development)
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# File (production - JSON lines)
logger.add(
    "logs/app.log",
    level="INFO",
    format="{message}",  # JSON will be serialized
    rotation="1 day",
    retention="7 days",
    compression="zip",
    serialize=True  # JSON lines
)
```

### Structured Logging
```python
logger.bind(
    document_id=doc.id,
    source=doc.source_type,
    stage="perception"
).info("Processing document", extra={
    "size_bytes": len(doc.text),
    "estimated_llm_calls": 25
})
```

---

## Performance Optimization

### Caching Strategy
- **HCO Cache**: Semantic block cache (DSPy cache extension)
- **Graph Cache**: Compiled DSPy graph (reused for all documents)
- **Rules Cache**: Serialized Pydantic rules (adaptix format)
- **LLM Cache**: DSPy's built-in cache for repeated prompts

### Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    # Process articles in parallel
    semantics = list(executor.map(
        lambda article: graph.semantic(text=article.text),
        structure.articles
    ))
```

---

## References

- DSPy compilation: https://github.com/stanfordnlp/dspy
- loguru logging: https://loguru.readthedocs.io
- Pydantic validation: https://docs.pydantic.dev
