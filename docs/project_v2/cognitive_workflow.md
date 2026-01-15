# Cognitive Workflow: From Raw XML to Temporal Knowledge Graph — v2.1

Схема жизненного цикла документа в системе LDUP.

```mermaid
sequenceDiagram
    participant XML as Raw XML (WordML)
    participant P as Perception Layer
    participant U as Understanding Layer
    participant R as Reasoning Layer
    participant V as Validation + Export
    participant L as Learning Layer (SRC)
    participant DB as FalkorDB (Graphiti)

    XML->>P: 1. Ingestion & Preprocessing
    Note over P: SourceDetector identifies "Consultant+"
    P->>P: 2. Structural Bootstrap (GEPA-optimized module)
    Note over P: Compile-time optimized with GEPA

    P->>U: 3. Semantic & Temporal Analysis
    U->>U: SIMBA-optimized semantic rules
    U->>U: MiPROv2-optimized temporal resolver
    Note right of U: HCO Cache for semantic blocks

    U->>R: 4. Causal & Relationship Mapping
    R->>R: TCGR: Link Amendment to target Article
    R->>R: CrossRef: Resolve internal/external links

    R->>V: 5. Structural + Semantic + Temporal Validation
    V->>V: Typed Output (Document/Article/Clause)
    V->>DB: 6. Knowledge Persistence
    Note over DB: Store as Bi-temporal RDF* triples

    DB-->>L: 7. Execution Trace (DSPyTrace)
    L->>L: 8. Auto-Diagnostics (SRC v2)
    L->>L: 9. YAML Patch Proposal + Rationale
    L-->>P: 10. Policy Optimizer (pending → active)
```

## 📜 Описание внутренних процессов

1.  **Ingestion**: Очистка XML от шума Word (`w:proofErr`, `w:rsid`) на основе `docs/project_v1/ldup_system.yaml`.
2.  **Compile-time vs Run-time**: GEPA/SIMBA/MIPROv2 работают как оптимизаторы на compile-time. На run-time используется скомпилированный `dspy.Module`.
3.  **HCO Cache Interaction**:
    *   **Ключ**: `source_id + article_id + hash(text_block) + rules_version`.
    *   **Инвалидация**: при обновлении YAML или при смене источника документа.
    *   **Основа**: `dspy.cache` как нижний уровень, поверх него — LDUP-слой семантических блоков. GitHub v3.0.4: https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/clients/cache.py#L18
4.  **Validation Layer**:
    *   **Structural**: проверка вложенности (Article ∈ Chapter).
    *   **Semantic**: контроль модальностей (must/forbid/allow).
    *   **Temporal**: проверка интервалов `valid_from < valid_to` и конфликтов редакций.
5.  **Self‑Improvement**:
    *   **Auto‑Diagnostics** фиксирует отклонения и формирует YAML‑патчи.
    *   **Patch Metadata**: `error_type`, `source_id`, `example_fragment`, `rationale`.
    *   **Versioning**: патчи пишутся как `pending` и проходят симуляцию/валидацию перед активацией.
6.  **Typed Output**: результаты фиксируются как `Document → Chapter → Article → Clause` и экспортируются в AKN/LegalDocML-RU.
