# LDUP v4 Architecture

**Goal:** Build a **self-improving legal document parser** with compile-time optimization, runtime safety, and full observability.

## Core Principles

1. **Compile-Time Optimization, Runtime Execution** — Optimizers run once, not per document
2. **Type Safety First** — Pydantic for rules, adaptix for fast serialization
3. **Observability by Design** — loguru for structured logging from day one
4. **Test Everything** — hypothesis for property-based testing
5. **Safe Self-Improvement** — Rollback, circuit-breaker, convergence criteria

---

## System Architecture

### High-Level View

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          COMPILE TIME                                   │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Input: Training Documents (N=100-1000)                           │ │
│  │                                                                  │ │
│  │  1. GEPA   → Optimize structural parsing prompts                 │ │
│  │  2. SIMBA  → Optimize semantic classification prompts            │ │
│  │  3. MIPROv2 → Optimize temporal resolution prompts               │ │
│  │                                                                  │ │
│  │  Output: Compiled DSPy Graph (optimized prompts baked in)       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                     ↓                                  │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Rule Definition (Pydantic)                                       │ │
│  │  - StructuralRule: pattern, priority, source_type                │ │
│  │  - SemanticRule: modality, exceptions, confidence                │ │
│  │  - TemporalRule: interval_patterns, effective_date_rules         │ │
│  │                                                                  │ │
│  │  Serialization (adaptix)                                         │ │
│  │  - Fast dump/load for cache                                     │ │
│  │  - 2-10x faster than Pydantic for hot paths                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           RUNTIME (Per Document)                       │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Input: Single Legal Document (WordML, PDF, etc.)                 │ │
│  │                                                                  │ │
│  │  Perception Layer                                                │ │
│  │  - Ingest → Source Detection → Structural Bootstrap             │ │
│  │  [Uses: GEPA-optimized structural module]                        │ │
│  │                                                                  │ │
│  │  Understanding Layer                                             │ │
│  │  - Semantic Classification → Temporal Resolution → HCO Cache     │ │
│  │  [Uses: SIMBA-optimized semantic, MiPROv2-optimized temporal]   │ │
│  │                                                                  │ │
│  │  Reasoning Layer                                                 │ │
│  │  - TCGR (causal links) → CrossRef → Graph Storage                │ │
│  │  [Uses: Custom LDUP modules]                                     │ │
│  │                                                                  │ │
│  │  Validation Layer                                                │ │
│  │  - Structural / Semantic / Temporal checks                       │ │
│  │  [Uses: Pydantic-validated rules + loguru logging]              │ │
│  │                                                                  │ │
│  │  Output: AKN / LegalDocML-RU + Semantic Graph                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    SELF-IMPROVEMENT LOOP (Background)                  │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  1. SRC/TRC/STC Controllers → Detect errors                       │ │
│  │  2. Feedback JSONL → Collect failures                             │ │
│  │  3. Policy Optimizer → Generate candidate rules (Pydantic)       │ │
│  │  4. Validate → Schema check + simulation on mini-corpus          │ │
│  │  5. Safety Rails → Rollback if accuracy drops >5%                │ │
│  │  6. Store → Versioned rule store (pending → active → archived)   │ │
│  │  7. Recompile → Trigger new compile-time optimization            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Map

### Compile-Time Components (Run Once)

| Component | Technology | DSPy Native? | Purpose |
|-----------|------------|--------------|---------|
| **GEPA** | DSPy 3.1 | ✅ Yes | Optimize structural parsing prompts via reflective evolution |
| **SIMBA** | DSPy 3.1 | ✅ Yes | Optimize semantic classification via introspection |
| **MiPROv2** | DSPy 3.1 | ✅ Yes | Multi-stage prompt optimization for temporal resolution |
| **Rule Compiler** | Custom LDUP | ❌ No | Compile Pydantic rules → DSPy teleprompt instructions |
| **adaptix Retort** | adaptix 1.x | ❌ No | Fast serialization for compiled graph |

### Runtime Components (Run Per Document)

| Component | Technology | DSPy Native? | Purpose |
|-----------|------------|--------------|---------|
| **Document Ingester** | Custom LDUP | ❌ No | Parse WordML → normalized text + metadata |
| **Source Detector** | Custom LDUP | ❌ No | Detect: ConsultantPlus, Garant, etc. |
| **Structural Bootstrap** | GEPA-optimized module | ✅ Yes | Build Chapter/Article/Part/Clause hierarchy |
| **Semantic Classifier** | SIMBA-optimized module | ✅ Yes | Classify modality: permission/prohibition/obligation |
| **Temporal Resolver** | MiPROv2-optimized module | ✅ Yes | Extract validity intervals, effective dates |
| **HCO Cache** | Custom LDUP (extends DSPy cache) | ⚠ Partial | Semantic block cache for repeated patterns |
| **TCGR** | Custom LDUP | ❌ No | Temporal Causal Graph Reasoner |
| **CrossRef Resolver** | Custom LDUP | ❌ No | Internal/external reference resolution |
| **Graph Storage** | FalkorDB/Graphiti | ❌ No | Persist semantic graph |
| **Validators** | Pydantic + Custom LDUP | ❌ No | Structural/semantic/temporal checks |

### Self-Improvement Components (Background)

| Component | Technology | DSPy Native? | Purpose |
|-----------|------------|--------------|---------|
| **SRC/TRC/STC Controllers** | Custom LDUP | ❌ No | Detect structural/semantic/temporal errors |
| **Unified Feedback Queue** | Custom LDUP | ❌ No | Collect feedback JSONL from all sources |
| **Policy Optimizer** | Custom LDUP | ❌ No | Prioritize rules by ΔAccuracy/ΔLLM/ΔConflict |
| **Rule Store** | Custom LDUP + adaptix | ❌ No | Versioned rules: pending/active/archived |
| **Safety Rails** | Custom LDUP | ❌ No | Rollback, circuit-breaker, convergence |

---

## DSPy 3.1 Alignment

### What DSPy 3.1 Provides

| Feature | DSPy 3.1 | LDUP v4 Usage |
|---------|----------|---------------|
| **GEPA Optimizer** | `dspy.teleprompt.GePA` | Compile-time: optimize structural parsing |
| **SIMBA Optimizer** | `dspy.teleprompt.SIMBA` | Compile-time: optimize semantic classification |
| **MiPROv2 Optimizer** | `dspy.teleprompt.MIPROv2` | Compile-time: optimize temporal resolution |
| **Typed Signatures** | `dspy.Signature` | Define all module I/O contracts |
| **Cache** | `dspy.clients.cache` | Extended with HCO (semantic block cache) |
| **Tracing** | `dspy.settings.context` | Collect LLM calls for self-improvement |

### What LDUP Must Implement

| Component | Why Not in DSPy? | LDUP v4 Implementation |
|-----------|------------------|------------------------|
| **Policy Optimizer** | Domain-specific for legal rules | Custom: Pydantic rules + priority scoring |
| **SRC/TRC/STC Controllers** | Legal document specific | Custom: Detect Russian law patterns |
| **YAML/Pydantic Compiler** | Behavioral layer specific | Custom: Compile rules → DSPy instructions |
| **TCGR** | Causal temporal reasoning | Custom: Graph-based amendment tracker |
| **Safety Rails** | Production requirement | Custom: Rollback, circuit-breaker |
| **Observability** | Production requirement | Custom: loguru integration |

---

## Technology Stack

### Core Framework
```toml
[dependencies]
dspy = "3.1"              # LLM orchestration
pydantic = "2.x"          # Type-safe rules
adaptix = "1.x"           # Fast serialization
loguru = "0.7+"           # Structured logging
hypothesis = "6.x+"       # Property-based testing
```

### Storage & Export
```toml
[dependencies]
falkordb = "1.x"          # Graph storage (or neo4j)
graphiti = "0.x"          # Alternative graph storage
lxml = "5.x"              # XML processing (AKN, LegalDocML)
```

### Testing
```toml
[dev-dependencies]
pytest = "8.x"
pytest-asyncio = "0.23+"  # Async test support
hypothesis = "6.x+"       # Property-based testing
pytest-cov = "5.x"        # Coverage
```

---

## Data Flow

### Compile-Time Flow
```
Training Corpus (N=100-1000 docs)
    ↓
[dspy.teleprompt.GePA] ──→ Optimized structural prompts
[dspy.teleprompt.SIMBA] ──→ Optimized semantic prompts
[dspy.teleprompt.MIPROv2] ──→ Optimized temporal prompts
    ↓
Compiled DSPy Graph (.pkl)
    ↓
[adaptix dump] ──→ Serialized rules cache
```

### Runtime Flow
```
Input Document (WordML/PDF)
    ↓
[Ingest] → Normalized text + metadata
    ↓
[Source Detector] → consultantplus/garant/raw
    ↓
[GEPA-optimized Structural Module] → Chapter/Article/Part/Clause
    ↓
[SIMBA-optimized Semantic Module] → Modality + definitions
    ↓
[MiPROv2-optimized Temporal Module] → Validity intervals
    ↓
[HCO Cache] → Semantic block lookup
    ↓
[TCGR] → Causal amendment links
    ↓
[CrossRef] → Reference resolution
    ↓
[Graph Storage] → Persist semantic graph
    ↓
[Validators] → Pydantic checks + loguru logging
    ↓
[Export] → AKN + LegalDocML-RU
    ↓
[Feedback Queue] → Errors → Self-improvement
```

### Self-Improvement Flow
```
[Validators] → Errors detected
    ↓
[SRC/TRC/STC] → Categorize: structural/semantic/temporal
    ↓
[Feedback JSONL] → error_type, text_fragment, expected, predicted
    ↓
[Policy Optimizer] → Generate Pydantic rule candidates
    ↓
[Validate] → Schema check + mini-corpus simulation
    ↓
[Safety Rails] → Check improvement threshold, rollback if needed
    ↓
[Rule Store] → pending → active → archived
    ↓
[Recompile Trigger] → New compile-time optimization run
```

---

## Safety & Reliability

### Safety Rails
```python
# Self-improvement safety limits
MAX_ITERATIONS = 10
MIN_IMPROVEMENT_THRESHOLD = 0.01  # 1%
MAX_ACCURACY_DROP = 0.05  # 5% (circuit breaker)
MIN_CORPUS_SIZE = 10  # Validation set size
```

### Observability
```python
# loguru configuration
logger.add("logs/{time}.log", rotation="1 day", retention="7 days")
logger.bind(document_id=123, stage="perception").info("Processing")
```

### Testing
```python
# Property-based test
@given(st.text(min_size=1))
def test_parser_handles_any_text(text):
    result = parser.parse(text)
    assert result is not None
```

---

## References

- DSPy 3.1: https://github.com/stanfordnlp/dspy
- Pydantic v2: https://docs.pydantic.dev
- adaptix: https://adaptix.readthedocs.io
- loguru: https://loguru.readthedocs.io
- hypothesis: https://hypothesis.readthedocs.io
