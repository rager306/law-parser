# LDUP v3 — Mermaid Diagrams

## 1) Architecture Overview

```mermaid
graph TB
    subgraph Perception [Perception]
        Ingest[Document Ingester] --> Source[Source Detector]
        Source --> Struct[GEPA-optimized Structural Module]
    end

    subgraph Understanding [Understanding]
        Struct --> Semantic[SIMBA-optimized Semantic Module]
        Semantic --> Temporal[MiPROv2-optimized Temporal Module]
        Temporal --> HCO[HCO Cache]
    end

    subgraph Reasoning [Reasoning]
        HCO --> TCGR[TCGR (custom)]
        TCGR --> CrossRef[Cross-Reference Resolver]
        CrossRef --> Graph[Graph Storage (FalkorDB/Graphiti)]
    end

    subgraph Validation [Validation]
        Graph --> StructuralV[Structural Validator]
        StructuralV --> SemanticV[Semantic Validator]
        SemanticV --> TemporalV[Temporal Validator]
    end

    subgraph SelfImprovement [Self-Improvement Core]
        TemporalV --> SRC[SRC/TRC/STC Controllers]
        SRC --> Queue[Unified Feedback Queue]
        Queue --> Policy[Policy Optimizer (custom)]
        Policy --> YAML[YAML RuleStore (pending/active/archived)]
        YAML --> Compiler[LDUP YAML Compiler]
        Compiler --> Struct
    end
```

## 2) Runtime Workflow

```mermaid
sequenceDiagram
    participant XML as WordML XML
    participant P as Perception
    participant U as Understanding
    participant R as Reasoning
    participant V as Validation
    participant O as Output

    XML->>P: Ingestion + Source Detection
    P->>P: GEPA-optimized Structure
    P->>U: Pass structure + text
    U->>U: SIMBA semantics
    U->>U: MiPROv2 temporal intervals
    U->>U: HCO cache lookup
    U->>R: Enriched document
    R->>R: TCGR causal links
    R->>R: CrossRef extraction
    R->>V: Validations
    V->>O: Typed Document + Export
```

## 3) Self-Improvement Loop

```mermaid
graph LR
    Run[Runtime Execution] --> Trace[DSPy Trace + Validators]
    Trace --> Detect[SRC/TRC/STC Detect Issues]
    Detect --> Patch[YAML Patch Proposal + Rationale]
    Patch --> Validate[YAML Validator + Simulation]
    Validate --> Policy[Policy Optimizer]
    Policy --> Store[YAML RuleStore: pending/active/archived]
    Store --> Rebuild[Recompile Graph]
    Rebuild --> Run
```

## 4) YAML Compilation Pipeline

```mermaid
flowchart LR
    YAML[General + Private YAML] --> Loader[YAML Loader]
    Loader --> Schema[Schema Validator]
    Schema --> Compile[Rule Compiler]
    Compile --> Graph[DSPy Graph Assembly]
    Graph --> Exec[Executable Parsing Pipeline]
```

## 5) Policy Optimizer Decision Flow

```mermaid
sequenceDiagram
    participant SRC as SRC/TRC/STC Controllers
    participant Q as Unified Feedback Queue
    participant P as Policy Optimizer
    participant V as YAML Validator
    participant S as YAML Store
    participant G as DSPy Graph

    SRC->>Q: Feedback JSONL
    Q->>P: Candidate rules
    P->>V: Validate + simulate
    V-->>P: OK/WARN/REJECT
    P->>S: pending/active/archived
    S->>G: Reload RuleSpec
```
