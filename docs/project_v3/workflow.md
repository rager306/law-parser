# LDUP v3 Workflow (Self‑Improving)

## 1) Execution Flow (Runtime)

1. **Ingestion**: WordML → normalized text + metadata.
2. **Structural Bootstrap**: GEPA‑optimized module builds `Chapter/Article/Part/Clause` hierarchy.
3. **Semantic/Temporal Analysis**: SIMBA/MiPROv2‑optimized modules annotate modality + validity intervals.
4. **Reasoning**: TCGR (custom) links amendments, CrossRef resolves internal/external links.
5. **Validation**: structural/semantic/temporal checks; invalid segments are marked.
6. **Export**: AKN / LegalDocML‑RU / Graph persistence.

## 2) Self‑Improvement Flow (Always‑On)

1. **Auto‑Diagnostics** (SRC/TRC/STC) detect anomalies:
   - structural: mis‑detected boundaries, missing hierarchy
   - semantic: modality misclassification
   - temporal: invalid date intervals or missing effective periods
2. **Feedback JSONL** is created with fields:
   - `error_type`, `module`, `text_fragment`, `expected`, `predicted`, `confidence`
3. **YAML Patch Proposal** is created (pending) with:
   - `pattern`, `action`, `rationale`, `source_id`, `example_fragment`
4. **Validation & Simulation**:
   - schema check, conflict detection, mini‑corpus simulation
5. **Versioning & Promotion**:
   - semver bump on activation
   - status transitions: `pending → active → archived`
6. **Graph Recompile** with updated RuleSpec.

## 3) DSPy 3.0.4 Alignment

- **Compile‑time**: GEPA / SIMBA / MIPROv2 optimizers (native DSPy).
- **Run‑time**: compiled `dspy.Module` + LDUP YAML rules.
- **Self‑Improvement**: SRC/TRC/STC + Policy Optimizer are **LDUP‑custom** and not native DSPy.

## 4) Output Contract

- `Document → Chapter → Article → Part → Clause → Subclause`
- `TemporalInfo` + `EditorialNote` + `Reference`
- Export targets: Akoma Ntoso, LegalDocML‑RU, graph storage
