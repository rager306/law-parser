# LDUP v4 — Mermaid Diagrams

**All diagrams updated for v4 architecture with compile/runtime separation, safety rails, and new components.**

---

## 1. Architecture Overview (Compile + Runtime)

```mermaid
graph TB
    subgraph CompileTime["COMPILE TIME (Once)"]
        Train["Training Corpus (N=100-1000)"]
        Train --> GEPA["GEPA Optimizer (DSPy 3.1)"]
        Train --> SIMBA["SIMBA Optimizer (DSPy 3.1)"]
        Train --> MIPROv2["MiPROv2 Optimizer (DSPy 3.1)"]

        Pydantic["Pydantic Rule Definition"]
        adaptix["adaptix Serialization"]

        GEPA --> Graph["Compiled DSPy Graph (.pkl)"]
        SIMBA --> Graph
        MIPROv2 --> Graph
        Graph --> Cache["Rule Cache (adaptix)"]
        Pydantic --> Cache
    end

    subgraph Runtime["RUNTIME (Per Document)"]
        Input["Input Document (WordML/PDF)"]
        Input --> Ingest["Ingestion"]
        Ingest --> Source["Source Detector"]
        Source --> Load["Load Compiled Graph"]

        Load --> Structural["Structural Bootstrap (GEPA-optimized)"]
        Structural --> Semantic["Semantic Analysis (SIMBA-optimized)"]
        Semantic --> Temporal["Temporal Resolution (MiPROv2-optimized)"]

        Temporal --> HCO["HCO Cache"]
        HCO --> TCGR["TCGR (Custom)"]
        TCGR --> CrossRef["CrossRef Resolver"]
        CrossRef --> GraphDB["Graph Storage (FalkorDB/Graphiti)"]

        GraphDB --> Validators["Validators (Pydantic + loguru)"]
        Validators --> Export["Export (AKN, LegalDocML-RU)"]
    end

    subgraph SelfImprovement["SELF-IMPROVEMENT (Background)"]
        Validators --> Controllers["SRC/TRC/STC Controllers"]
        Controllers --> Feedback["Feedback Queue (JSONL)"]
        Feedback --> Policy["Policy Optimizer"]
        Policy --> GenRules["Generate Rules (Pydantic)"]
        GenRules --> Validate["Validate + Simulate"]
        Validate --> Safety["Safety Rails Check"]
        Safety -->|"Pass"| Store["Rule Store (pending→active)"]
        Safety -->|"Circuit Breaker"| Rollback["Rollback"]
        Store -->|"Batch of 10"| Trigger["Trigger Recompile"]
        Trigger --> CompileTime
    end

    subgraph Observability["OBSERVABILITY (loguru)"]
        Log["Structured Logging"]
        Metrics["Metrics Collection"]
        Alerts["Alerting"]
    end

    Runtime -.->|Errors| Controllers
    Runtime -.->|Logs| Log
    CompileTime -.->|Metrics| Metrics
    SelfImprovement -.->|Metrics| Metrics
    Metrics -.->|Threshold| Alerts
```

---

## 2. Compile-Time Workflow (Optimization)

```mermaid
flowchart TB
    Start([Start: Compile-Time Optimization]) --> LoadCorpus["Load Training Corpus (N=100-1000)"]
    LoadCorpus --> Split["Split: 80% Train / 20% Val"]

    Split --> GEPA["GEPA: Optimize Structural Prompts"]
    Split --> SIMBA["SIMBA: Optimize Semantic Prompts"]
    Split --> MIPROv2["MiPROv2: Optimize Temporal Prompts"]

    GEPA --> GEPACost["~1,000-5,000 LLM calls<br/>1.7-8.3 minutes"]
    SIMBA --> SIMBACost["~250-1,000 LLM calls<br/>0.4-1.7 minutes"]
    MIPROv2 --> MIPROv2Cost["~250-1,000 LLM calls<br/>0.4-1.7 minutes"]

    GEPACost --> LoadRules["Load Pydantic Rules"]
    SIMBACost --> LoadRules
    MIPROv2Cost --> LoadRules

    LoadRules --> CompileRules["Compile Rules → DSPy Instructions"]
    CompileRules --> adaptix["Serialize with adaptix"]

    adaptix --> Assemble["Assemble DSPy Graph"]
    Assemble --> Serialize["Serialize Graph (.pkl)"]
    Serialize --> Cache["Cache: graph.pkl, rules.pkl"]

    Cache --> LogLog["loguru: Compile Complete"]
    LogLog --> End([End: Ready for Runtime])

    style Start fill:#e1f5fe
    style End fill:#c8e6c9
    style GEPACost fill:#fff3e0
    style SIMBACost fill:#fff3e0
    style MIPROv2Cost fill:#fff3e0
```

---

## 3. Runtime Workflow (Per Document)

```mermaid
sequenceDiagram
    participant Doc as Input Document
    participant Ingest as Ingestion
    participant Source as Source Detector
    participant Graph as Compiled Graph
    participant Struct as Structural
    participant Sem as Semantic
    participant Temp as Temporal
    participant HCO as HCO Cache
    participant TCGR as TCGR
    participant CrossRef as CrossRef
    participant Valid as Validators
    participant Log as loguru

    Doc->>Ingest: WordML/PDF
    Ingest->>Log: INFO: Ingestion started

    Ingest->>Source: Normalized text
    Source->>Source: Detect consultantplus/garant/raw
    Source->>Log: INFO: Source detected

    Source->>Graph: Load compiled graph
    Graph->>Graph: Load rules from cache

    Graph->>Struct: Parse structure
    Struct->>Log: DEBUG: Structural parsing
    Struct->>Graph: Chapter/Article/Part/Clause

    Graph->>Sem: Classify semantics
    Sem->>Log: DEBUG: Semantic classification
    Sem->>HCO: Check cache
    HCO-->>Sem: Cache hit/miss
    Sem->>Graph: Modality + definitions

    Graph->>Temp: Extract temporals
    Temp->>Log: DEBUG: Temporal extraction
    Temp->>Graph: Validity intervals

    Graph->>TCGR: Build causal links
    TCGR->>Log: INFO: Causal graph built
    TCGR->>Graph: Amendment graph

    Graph->>CrossRef: Resolve references
    CrossRef->>Log: INFO: References resolved
    CrossRef->>Graph: Internal/external refs

    Graph->>Valid: Validate with Pydantic
    Valid->>Log: INFO: Validation passed

    alt Validation Errors
        Valid->>Log: ERROR: Validation failed
        Valid->>Feedback: Queue for self-improvement
    end

    Valid->>Log: INFO: Export complete
```

---

## 4. Self-Improvement Loop with Safety Rails

```mermaid
stateDiagram-v2
    [*] --> Detecting: Runtime Execution

    Detecting --> SRC: SRC/TRC/STC<br/>Detect Errors
    SRC --> Feedback: Feedback JSONL

    Feedback --> Prioritize: Policy Optimizer<br/>Prioritize by Frequency × Impact
    Prioritize --> Generate: Generate Pydantic Rules

    Generate --> Validate: Schema Validation
    Validate -->|"Pass"| Simulate: Mini-Corpus Simulation
    Validate -->|"Fail"| Reject: Reject Rule

    Simulate --> Safety: Safety Rails Check

    Safety --> Check1: Max Iterations?
    Safety --> Check2: Convergence?
    Safety --> Check3: Circuit Breaker?

    Check1 -->|">=10"| Stop: Stop Self-Improvement
    Check2 -->|"<1%"| Stop: Converged
    Check3 -->|">5% Drop"| Rollback: Rollback to Backup

    Rollback --> Stop

    Check1 -->|"<10"| Activate: Activate Rule
    Check2 -->|">=1%"| Activate
    Check3 -->|"<=5%"| Activate

    Activate --> Update: Update Rule Store<br/>(pending → active)
    Update --> Count: Count Active Rules

    Count --> CheckBatch: Mod 10 == 0?
    CheckBatch -->|"Yes"| Recompile: Trigger Compile-Time
    CheckBatch -->|"No"| Detecting: Continue Runtime

    Recompile --> [*]: New Optimization Run
    Stop --> [*]: Halted
    Reject --> [*]: Rejected
```

---

## 5. Safety Rails Decision Flow

```mermaid
flowchart TB
    Start([Candidate Rule Generated]) --> Backup["Backup Current Rule Store"]

    Backup --> Validate["Validate with Pydantic"]
    Validate -->|"Fail"| Reject["Reject Rule"]
    Validate -->|"Pass"| Simulate["Simulate on Mini-Corpus (N=20)"]

    Simulate --> CalcAcc["Calculate Accuracy"]
    CalcAcc --> CalcImprovement["Improvement = New - Baseline"]

    CalcImprovement --> Check1{"Improvement >= 1%?"}
    Check1 -->|"No"| Converge["Converged: Stop Loop"]
    Check1 -->|"Yes"| Check2{"New >= Baseline × 0.95?"}

    Check2 -->|"No"| CircuitBreaker["Circuit Breaker:<br/>Accuracy Dropped >5%"]
    Check2 -->|"Yes"| Check3{"Iteration < 10?"}

    Check3 -->|"No"| MaxIter["Max Iterations Reached"]
    Check3 -->|"Yes"| Activate["Activate Rule"]

    Activate --> UpdateStore["Update Rule Store:<br/>pending → active"]
    UpdateStore --> LogSuccess["loguru: Rule Activated"]
    LogSuccess --> Continue([Continue to Next Rule])

    CircuitBreaker --> Rollback["Rollback to Backup"]
    Rollback --> LogCB["loguru: Circuit Breaker Tripped"]
    LogCB --> Stop([Stop Self-Improvement])

    MaxIter --> LogMax["loguru: Max Iterations"]
    LogMax --> Stop

    Converge --> LogConv["loguru: Converged"]
    LogConv --> Stop

    Reject --> LogReject["loguru: Rule Rejected"]
    LogReject --> Continue

    style Start fill:#e1f5fe
    style Continue fill:#c8e6c9
    style Stop fill:#ffcdd2
    style Reject fill:#ffcdd2
    style Rollback fill:#ffcdd2
    style Activate fill:#c8e6c9
```

---

## 6. Data Flow: Pydantic + adaptix

```mermaid
flowchart LR
    subgraph Definition["Rule Definition (Pydantic)"]
        BaseModel["Pydantic BaseModel"]
        Field["Field(ge=0, le=10)"]
        Validator["@validator"]

        BaseModel --> Field
        BaseModel --> Validator
    end

    subgraph Validation["Validation"]
        Input["User Input / YAML"]
        Validate["model_validate()"]
        Error["ValidationError"]

        Input --> Validate
        Validate -->|"Pass"| ValidRule["Valid Rule"]
        Validate -->|"Fail"| Error
    end

    subgraph Serialization["Serialization (adaptix)"]
        Retort["Retort()"]
        Dump["dump(rule)"]
        Load["load(bytes, Rule)"]

        ValidRule --> Retort
        Retort --> Dump
        Dump --> Bytes["JSON / MsgPack / Binary"]
        Bytes --> Load
        Load --> LoadedRule["Loaded Rule"]
    end

    subgraph Storage["Storage / Transport"]
        Cache["Cache (rules.pkl)"]
        LLM["LLM Context (JSON)"]
        GraphDB["Graph DB Nodes"]

        Bytes --> Cache
        Bytes --> LLM
        Bytes --> GraphDB
    end

    subgraph Runtime["Runtime Usage"]
        HotPath["Hot Path (LLM I/O)"]
        Cached["Cached Rules"]

        Cache --> HotPath
        LoadedRule --> HotPath
        Cached --> HotPath
    end

    style BaseModel fill:#e3f2fd
    style ValidRule fill:#c8e6c9
    style Bytes fill:#fff3e0
    style HotPath fill:#f3e5f5
```

---

## 7. Testing Strategy

```mermaid
graph TB
    subgraph PropertyTests["Property-Based Tests (hypothesis)"]
        Parser["Parser Properties"]
        Structure["Structure Properties"]
        Semantic["Semantic Properties"]
        Temporal["Temporal Properties"]
        Serial["Serialization Properties"]

        Hypothesis["@given(st.text())"]
        Hypothesis --> Parser
        Hypothesis --> Structure
        Hypothesis --> Semantic
        Hypothesis --> Temporal
        Hypothesis --> Serial
    end

    subgraph UnitTests["Unit Tests"]
        MockLLN["Mock LLM Calls"]
        MockCache["Mock Cache"]
        MockDB["Mock Graph DB"]

        MockLLN --> TestIngest["Test Ingester"]
        MockCache --> TestHCO["Test HCO Cache"]
        MockDB --> TestTCGR["Test TCGR"]
    end

    subgraph IntegrationTests["Integration Tests"]
        RealDocs["Real Documents"]
        RealLLM["Real LLM Calls"]
        Pipeline["Full Pipeline"]

        RealDocs --> RealLLM
        RealLLM --> Pipeline
    end

    subgraph RegressionTests["Regression Tests"]
        Golden["Golden Corpus"]
        Compare["Compare Output"]
        Alert["Alert on Regression"]

        Golden --> Compare
        Compare --> Alert
    end

    PropertyTests -->|"100-1000 cases"| Coverage[90%+ Coverage]
    UnitTests --> Coverage
    IntegrationTests -->|"Real data"| Coverage
    RegressionTests -->|"Prevent regressions"| Coverage

    style Hypothesis fill:#e1f5fe
    style Coverage fill:#c8e6c9
```

---

## 8. Observability Pipeline

```mermaid
flowchart TB
    subgraph Logging["loguru Configuration"]
        Console["Console (Dev)<br/>Colorized, Human-Readable"]
        FileJSON["File (Prod)<br/>JSON Lines"]
        FileError["Error File<br/>Errors Only"]
        FileLLM["LLM Trace<br/>Prompts/Responses"]

        Config["logger.add()"]
        Config --> Console
        Config --> FileJSON
        Config --> FileError
        Config --> FileLLM
    end

    subgraph Levels["Logging Levels"]
        DEBUG["DEBUG: LLM Calls"]
        INFO["INFO: Operations"]
        WARNING["WARNING: Fallbacks"]
        ERROR["ERROR: Failures"]
        CRITICAL["CRITICAL: System Failure"]

        Console --> DEBUG
        Console --> INFO
        Console --> WARNING
        FileJSON --> INFO
        FileJSON --> WARNING
        FileError --> ERROR
        FileError --> CRITICAL
        FileLLM --> DEBUG
    end

    subgraph Structured["Structured Logging"]
        Bind["logger.bind()"]
        Extra["extra={...}"]

        Bind --> Context["document_id, source_type"]
        Extra --> Metrics["parse_time, llm_calls"]
    end

    subgraph Outputs["Outputs"]
        LogFiles["Rotated Files<br/>1 day, 7 days retention"]
        Alerts["Alerts<br/>Slack, Prometheus"]
        Dashboards["Dashboards<br/>Grafana, MLflow"]

        FileJSON --> LogFiles
        FileError --> Alerts
        Metrics --> Dashboards
    end

    style Config fill:#e3f2fd
    style Context fill:#c8e6c9
    style Alerts fill:#ffcdd2
```

---

## 9. Technology Stack

```mermaid
graph TB
    subgraph Framework["Core Framework"]
        DSPy["DSPy 3.1<br/>LLM Orchestration"]
        Pydantic["Pydantic 2.x<br/>Type Safety"]
        adaptix["adaptix 1.x<br/>Fast Serialization"]

        DSPy --> Compile["Compile-Time<br/>Optimization"]
        Pydantic --> Rules["Rule Definition"]
        adaptix --> Cache["Rule Cache"]
    end

    subgraph Observability["Observability"]
        loguru["loguru 0.7+<br/>Structured Logging"]
        hypothesis["hypothesis 6.x+<br/>Property-Based Testing"]
        MLflow["MLflow<br/>Experiment Tracking"]
        Prometheus["Prometheus<br/>Metrics"]
    end

    subgraph Storage["Storage & Export"]
        FalkorDB["FalkorDB<br/>Graph Storage"]
        Graphiti["Graphiti<br/>Alternative Graph"]
        lxml["lxml 5.x<br/>XML Processing"]
    end

    subgraph Testing["Testing"]
        pytest["pytest 8.x<br/>Test Runner"]
        pytest_asyncio["pytest-asyncio<br/>Async Tests"]
        pytest_cov["pytest-cov<br/>Coverage"]
    end

    Framework --> System["LDUP v4 System"]
    Observability --> System
    Storage --> System
    Testing --> System

    style DSPy fill:#e3f2fd
    style Pydantic fill:#c8e6c9
    style adaptix fill:#fff3e0
    style loguru fill:#f3e5f5
    style hypothesis fill:#e1f5fe
```

---

## 10. Version Comparison: v3 vs v4

```mermaid
graph TB
    subgraph V3["v3 Architecture"]
        V3Compile["Compile-Time"]
        V3Runtime["Runtime"]
        V3SI["Self-Improvement"]

        V3Runtime -->|"Incorrect"| V3Compile
        V3SI -->|"No Safety"| V3Runtime
        V3Compile -->|"YAML"| V3Runtime
    end

    subgraph V4["v4 Architecture"]
        V4Compile["Compile-Time<br/>(Clear Separation)"]
        V4Runtime["Runtime<br/>(Fixed)"]
        V4SI["Self-Improvement<br/>(Safety Rails)"]

        V4Compile -->|"Graph.pkl"| V4Runtime
        V4Runtime -->|"Errors"| V4SI
        V4SI -->|"Safe"| V4Compile
        V4SI -->|"Rollback"| V4SI
    end

    subgraph Changes["Key Changes"]
        C1["DSPy 3.0.4 → 3.1"]
        C2["YAML → Pydantic + adaptix"]
        C3["Add loguru"]
        C4["Add hypothesis"]
        C5["Add Safety Rails"]
    end

    V3 -.->|"Fixed"| V4
    Changes --> V4

    style V3 fill:#ffcdd2
    style V4 fill:#c8e6c9
    style Changes fill:#fff3e0
```

---

## Diagram Legend

| Color | Meaning |
|-------|---------|
| 🟦 Blue | Compile-time / DSPy |
| 🟩 Green | Runtime / Success |
| 🟨 Orange | Optimization / Processing |
| 🟪 Purple | Observability / Testing |
| 🟥 Red | Error / Failure / Circuit Breaker |

---

## References

- Mermaid docs: https://mermaid.js.org
- DSPy 3.1: https://github.com/stanfordnlp/dspy
- Pydantic: https://docs.pydantic.dev
- adaptix: https://adaptix.readthedocs.io
- loguru: https://loguru.readthedocs.io
- hypothesis: https://hypothesis.readthedocs.io
