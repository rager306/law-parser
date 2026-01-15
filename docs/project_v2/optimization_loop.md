# Optimization Loop: The Self-Learning Cycle — v2.1

Процесс эволюции системы от «LLM-heavy» к «Rule-based».

```mermaid
graph LR
    subgraph Optimization_Phase [Optimization Phase (Compile Time)]
        Program[Vanilla DSPy Program] --> Tele[Teleprompter: MIPROv2 / GEPA / SIMBA]
        Tele --> Trainset[Training Set: 44-FZ Samples]
        Trainset --> Compiled[Compiled DSPy Program]
    end

    subgraph Inference_Phase [Inference Phase (Run Time)]
        Input[New Document] --> Compiled
        Compiled --> Output[Typed Structured Data]
        Output --> Trace[DSPy Execution Trace]
    end

    subgraph Feedback_Phase [Feedback Phase (Refinement)]
        Trace --> SRC[SRC v2: Error Detection]
        SRC --> JSONL[Feedback JSONL + Rationale]
        JSONL --> Policy[Policy Optimizer: Multi-armed Bandit]
        Policy --> YAML[Updated YAML DNA (pending)]
        YAML --> Validator[YAML Validator + Simulation]
        Validator --> Active[Promote to active + version bump]
    end

    Active -.-> |Trigger Recompile| Optimization_Phase
```

## 🧠 Ключевые механизмы оптимизации

*   **Compile-time Optimizers**: GEPA/SIMBA/MIPROv2 применяются при компиляции DSPy-программы (см. https://dspy.ai/api/optimizers/).
*   **SRC v2 (Self-Refinement Controller)**: Генерирует feedback на основе трасс выполнения и валидаторов структуры/семантики/времени.
*   **Policy Optimizer**: Реализует логику `docs/project_v1/Policy Optimizer in YAML (policy_config.yaml).md` и управляет весами правил.
*   **YAML Validator + Simulation**: Проверяет синтаксис, конфликты и качество на мини-корпусе документов.
*   **Documentation + Versioning**: каждый патч фиксируется с `rationale`, `error_type`, `example_fragment` и получает semver‑bump при активации.

## 📏 Метрики качества (минимальный набор)

*   **Structural Accuracy**: доля корректно выделенных узлов (Chapter/Article/Clause).
*   **Semantic Accuracy**: точность модальностей (обязанность/запрет/разрешение).
*   **Temporal Accuracy**: точность `valid_from/valid_to` и отсутствие коллизий.
*   **LLM Usage Rate**: доля документов, требующих LLM-поддержки (целевое значение ≤ 0.2).
