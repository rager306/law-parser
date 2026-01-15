# LDUP v1.0 Architecture (Project v3)

Цель v3 — вернуть **самоулучшение** как основной контур архитектуры, но согласовать его с фактическими возможностями DSPy 3.0.4 (и отметить, что требует кастомной реализации).

## 1) Базовая структура (с самоулучшением)

- **Perception**: Ingestion → Source Detector → GEPA‑optimized structural module.
- **Understanding**: SIMBA‑optimized semantic module → MiPROv2‑optimized temporal resolver → HCO cache.
- **Reasoning**: TCGR (custom) → Cross‑Ref Resolver → Graph storage (FalkorDB/Graphiti).
- **Self‑Improvement (Core)**: SRC/TRC/STC → Unified Feedback Queue → Policy Optimizer → YAML Store (pending/active/archived) → Graph recompile.

## 2) Что из v1 необходимо вернуть (архитектура самообучения)

### Из `docs/project_v1/SRC correction cycle.md`
- **Feedback JSONL** с `error_type`, `text_fragment`, `expected/predicted`, `confidence`.
- **Pending→Active** правило с автоматической валидацией.
- **Протокол улучшения**: правило фиксируется, метрики улучшения сохраняются.

### Из `docs/project_v1/SRC-cycles (temporal + semantic).md`
- **Unified Feedback Queue**: объединение semantic/temporal/structural сигналов.
- **Policy Optimizer** решает приоритеты, учитывая ΔAccuracy/ΔLLM/ΔConflict.
- **Metrics Collector** замыкает контур и обновляет policy weights.

### Из `docs/project_v1/Arch v.0.3 YAML = Behavioral Specification Layer.md`
- **YAML как поведенческий слой**: general + private правила.
- **Rule compilation** → DSPy Graph (через компилятор LDUP).
- **Formal + empirical validation** перед активацией.

## 3) Сопоставление с DSPy 3.0.4 (что реально существует)

| Компонент | Идея в v1 | DSPy 3.0.4 | Статус в v3 |
|---|---|---|---|
| GEPA | Reflective prompt evolution | `dspy/teleprompt/gepa/gepa.py` | ✅ Native (compile‑time) |
| SIMBA | Introspective optimization | `dspy/teleprompt/simba.py` | ✅ Native (compile‑time) |
| MiPROv2 | Multi‑stage optimizer | `dspy/teleprompt/mipro_optimizer_v2.py` | ✅ Native (compile‑time) |
| Typed Signatures | Structured I/O | `dspy/signatures/signature.py` | ✅ Native |
| Policy Optimizer | Reinforcement over rules | нет в DSPy 3.0.4 | ❗ Custom LDUP module |
| SRC/TRC/STC | Self‑refinement controllers | нет в DSPy 3.0.4 | ❗ Custom LDUP module |
| YAML Compiler | YAML → Graph | нет в DSPy 3.0.4 | ❗ Custom LDUP module |
| HCO Cache | Semantic block cache | DSPy cache only | ⚠ Partial (build on `dspy/clients/cache.py`) |
| TCGR | Causal temporal graph | нет в DSPy 3.0.4 | ❗ Custom LDUP module |

## 4) Принципиальные решения v3

1. **Self‑Improvement является обязательным слоем**, а не опциональной надстройкой.
2. **GEPA/SIMBA/MiPROv2 используются только как compile‑time оптимизаторы**, а не runtime‑узлы.
3. **Policy Optimizer и SRC‑контуры — кастомные LDUP‑модули**, но подключаются к DSPy через стандартные tracing/metrics интерфейсы.
4. **YAML версионируется семантически**: `major` — смена структуры; `minor` — новые правила; `patch` — устранение конфликтов.
5. **Каждый патч документируется**: `rationale`, `example_fragment`, `error_type`, `confidence`.

## 5) Ссылки на DSPy 3.0.4

- GEPA: https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/teleprompt/gepa/gepa.py#L148
- SIMBA: https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/teleprompt/simba.py#L16
- MIPROv2: https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/teleprompt/mipro_optimizer_v2.py#L47
- Signature: https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/signatures/signature.py#L240
- Cache: https://github.com/stanfordnlp/dspy/blob/3.0.4/dspy/clients/cache.py#L18
