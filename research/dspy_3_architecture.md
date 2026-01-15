# DSPy 3.0+ Technical Documentation & Research Analysis

## 🧭 Overview
DSPy has evolved into a sophisticated framework for programming, not just prompting, Language Models. The latest versions (3.0.x) introduce several advanced architectural components that align perfectly with the LDUP (Legal Document Universal Parser) requirements.

## 🧱 Key Architectural Components (3.0+)

### 1. GEPA (Graph-Enhanced Prompt Architecture)
*   **Path**: `dspy/teleprompt/gepa/gepa.py`
*   **Role**: An evolutionary optimizer that uses reflection to evolve text components of complex systems.
*   **Mechanism**:
    *   Captures full execution traces.
    *   Reflects on predictor behavior to propose new instructions.
    *   Supports textual feedback at both individual predictor and program levels.
    *   **LDUP Alignment**: Directly matches the `GEPA 3.5` requirement for structural bootstrap and hierarchical parsing.

### 2. SIMBA (Stochastic Introspective Mini-Batch Ascent)
*   **Path**: `dspy/teleprompt/simba.py`
*   **Role**: Introspective optimizer that uses the LLM to analyze its own performance.
*   **Mechanism**:
    *   Identifies challenging examples with high output variability.
    *   Creates self-reflective rules or adds successful demonstrations.
    *   **LDUP Alignment**: Matches the `SIMBA 2.2` requirement for morpho-semantic analysis and learning from double negations/complex syntax.

### 3. MIPROv2 (Multi-level Instruction Program Optimizer)
*   **Path**: `dspy/teleprompt/mipro_optimizer_v2.py`
*   **Role**: A sophisticated optimizer that jointly optimizes instructions and few-shot examples.
*   **Mechanism**:
    *   Uses a "Grounded Proposer" to generate instruction candidates.
    *   Optimizes across multi-stage pipelines.
    *   Supports `auto` budget settings (light, medium, heavy).
    *   **LDUP Alignment**: Corresponds to the `MiPROv3` (or v2) temporal resolver requirement for bi-temporal interval reasoning.

### 4. MCP (Model Context Protocol) Integration
*   **Path**: `dspy/utils/mcp.py`
*   **Role**: Integration with the Model Context Protocol.
*   **Mechanism**:
    *   Converts MCP tools into DSPy-native Tool objects.
    *   Enables asynchronous tool calling via MCP sessions.
    *   **LDUP Alignment**: Facilitates the "Action Layer" and integration with external databases/agents like FalkorDB.

### 5. Advanced Evaluation & Feedback (SRC v2)
*   **Path**: `dspy/teleprompt/gepa/gepa_utils.py` (referenced)
*   **Concept**: The `GEPAFeedbackMetric` protocol allows for complex, trace-aware feedback.
*   **LDUP Alignment**: Supports the `SRC v2` (Self-Refinement Controller) logic for generating JSONL patches based on execution errors.

## 🚀 Optimization Logic

### Rule-First vs LLM-Assist
The new optimizers (GEPA, SIMBA) are designed to "compile" logic into stable instructions and rules. This supports the LDUP target of `llm_usage_rate < 0.2` by moving from pure LLM inference to compiled, rule-based execution paths.

### Hybrid Context Optimization (HCO)
While specific "HCO" files are part of the LDUP-specific logic, DSPy's internal caching (`dspy/utils/caching.py`) and trace-based reflection provide the functional foundation for implementing the HCO Cache.

## 📂 Implementation Blueprint for LDUP

| LDUP Layer | DSPy 3.0+ Component | Implementation Strategy |
|------------|---------------------|--------------------------|
| **Perception** | `GEPA` / `SIMBA` | Use GEPA for structural bootstrap; SIMBA for initial semantic sensory. |
| **Understanding** | `MIPROv2` / `LM` | MiPRO for temporal resolver; Structure-aware signatures for S-LLM. |
| **Reasoning** | `dspy.Predict` / `Tool` | Custom signatures for TCGR logic and GraphBuilder tools. |
| **Learning** | `GEPA Feedback` | Implement `GEPAFeedbackMetric` for SRC v2 reflexive loops. |
| **Adaptation** | `Optimizer` | Use DSPy's built-in reinforcement-like optimization for Policy Tuning. |

## 🧪 Research Findings
*   **Trace-Awareness**: The move towards full execution traces (`DSPyTrace`) allows the system to understand "why" a failure occurred, which is essential for the `SRC v2` controller.
*   **Async Performance**: Modern DSPy uses `ParallelExecutor` (in `dspy/utils/parallelizer.py`) with straggler limits and thread isolation, critical for processing large regulatory corpuses.
*   **Dynamic Signatures**: The framework now supports more robust dynamic signature generation, enabling the "Neural Policy Tuning" (NPT) requirement for reconfiguring pipelines based on act complexity.
