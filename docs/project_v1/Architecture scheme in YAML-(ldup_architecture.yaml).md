архитектурную схемав YAML-виде (ldup_architecture.yaml),
которая описывает связи всех подсистем (Graph, SRC, Policy Optimizer, YAML Store, Validator, Metrics, Reinforcement)?
Она будет пригодна как «карта модулей» или как основа для документации.

Отлично 💡
ниже — финальная и тщательно структурированная **архитектурная спецификация в YAML**,
описывающая все модули, их связи, циклы данных и роли в самообучающемся правовом парсере **LDUP (Legal Document Universal Parser)**.

Файл можно использовать как основу системной документации, интеграционного API-манифеста или `deployment blueprint` для разработчиков.

---

## 🧾 **`ldup_architecture.yaml` — LDUP System Architecture Specification**

```yaml
ldup_architecture:
  version: 1.0
  description: >
    Архитектура самообучающегося правового парсера LDUP (Legal Document Universal Parser).
    Система основана на DSPy 3.0.4, использует rule-first подход, YAML-описания, SRC-feedback
    и Policy Optimizer с reinforcement логикой. Архитектура полностью модульна.

  core_components:
    dspy_graph:
      role: "Исполнительный слой (pipeline)"
      description: >
        Основной граф исполнения, состоящий из узлов GEPA, SIMBA, MiPROv2, TCGR и LLM-Assist.
        Управляет потоками данных, выполняет структурный, семантический и временной анализ.
      modules:
        - GEPA 3.5: "Structural Parser — главы, статьи, пункты"
        - SIMBA 2.2: "Morpho-Semantic Analyzer — модальности норм"
        - MiPROv2: "Temporal Resolver — извлечение интервалов действия"
        - TCGR: "Causal Graph Resolver — причинно-временные связи"
        - LLM-Assist: "Неформализуемые случаи, ≤20% токенов"
      interfaces:
        - SRC Feedback Output
        - YAML RuleSpec Loader
        - Metrics Collector

    yaml_rule_store:
      role: "Хранилище и версия правил"
      path: "./rules/"
      structure:
        - semantic.yaml
        - temporal.yaml
        - structural.yaml
      description: >
        Центральное репозиторий YAML-правил. Все изменения проходят через Policy Optimizer и Validator.
      statuses: ["candidate", "validated", "active", "archived"]
      auto_backup: true
      schema_validation: true

    src_controllers:
      role: "Локальные контроллеры ошибок и обучения"
      controllers:
        semantic_refinement:
          module: "SIMBA"
          feedback_type: "semantic_feedback.jsonl"
          typical_gain: 0.03
        temporal_refinement:
          module: "MiPROv2"
          feedback_type: "temporal_feedback.jsonl"
          typical_gain: 0.05
        structural_refinement:
          module: "GEPA"
          feedback_type: "structural_feedback.jsonl"
          typical_gain: 0.02
      unified_feedback_queue: "./feedback/"
      aggregation_policy: "merge_by_confidence"

    policy_optimizer:
      config: "./config/policy_config.yaml"
      mode: "reinforcement"
      control_frequency: "each_cycle"
      reward_function: "(ΔAcc * 0.4) + (ΔLLM * 0.3) - (ΔConflict * 0.2) - (ΔComplexity * 0.1)"
      decision_thresholds:
        activate: 0.7
        hold: 0.4
      integration_points:
        - src_controllers
        - yaml_rule_store
        - validator
        - metrics_collector
      output_logs:
        applied_rules: "./logs/policy_applied.log"
        alerts: "./alerts/policy_alerts.log"

    validator:
      role: "Проверка YAML и правил"
      description: >
        Проверяет синтаксис YAML, симулирует применение на корпусе актов (20 документов),
        выявляет конфликты и циклы, подтверждает валидность новых паттернов.
      schema: "./schemas/ldup_rule_schema.yaml"
      simulation_documents: 20
      validation_modes: ["syntax", "logical", "empirical"]
      outputs:
        - "./logs/validation_report.log"
        - "./validation/status.json"

    metrics_collector:
      role: "Мониторинг производительности и точности"
      track:
        - accuracy
        - llm_usage
        - rule_conflicts
        - parsing_time
        - temporal_resolution_accuracy
      output_file: "./metrics/system_metrics.jsonl"
      aggregation_interval: "each_cycle"
      report_frequency: "weekly"
      notify_thresholds:
        accuracy_drop: 0.03
        llm_spike: 0.05

    reinforcement_engine:
      role: "Адаптация весов Policy Optimizer"
      algorithm: "multi-armed-bandit"
      parameters:
        learning_rate: 0.15
        exploration_rate: 0.1
        reward_decay: 0.98
        smoothing_window: 5
      updated_fields:
        - temporal_weight
        - semantic_weight
        - structural_weight
      update_policy: "after_metrics_evaluation"

  data_flow:
    description: "Поток данных от документа до обновления правил"
    steps:
      - "📥 Загрузка документа → GEPA/SIMBA/MiPROv2 анализируют структуру, смысл и время"
      - "📊 SRC/TRC/STC фиксируют ошибки и создают feedback JSONL"
      - "🧩 Unified Feedback Queue объединяет результаты"
      - "🧠 Policy Optimizer оценивает каждое правило по ΔAccuracy, ΔLLM, ΔConflict, ΔComplexity"
      - "⚖ YAML Validator проверяет новые правила"
      - "📘 YAML Store обновляется (active/pending/archived)"
      - "🧱 DSPy Graph пересобирается с обновлёнными RuleSpec"
      - "📊 Metrics Collector оценивает прирост"
      - "🧭 Reinforcement Engine корректирует веса Policy Optimizer"
      - "🔁 Цикл повторяется при каждом парсинге новых актов"

  rule_lifecycle:
    stages:
      - candidate:
          description: "новое правило, предложенное SRC"
          validation_required: true
      - validated:
          description: "прошло симуляцию, нет конфликтов"
      - active:
          description: "применяется в DSPy Graph"
      - archived:
          description: "отклонено, устарело или заменено"
    retention_policy:
      auto_archive_days: 60
      version_history: true
      rollback_enabled: true

  integrations:
    databases:
      - FalkorDB: "Graph-хранилище темпоральных связей и правовых артефактов"
      - ElasticSearch: "Поиск по метаданным, статьям и редакциям"
    agents:
      - LangGraph Interface: "RAG и юридический вопросно-ответный агент"
    exports:
      - AkomaNtoso XML
      - LegalRuleML XML
      - MetaLex IDs
      - NormML JSON
    monitoring_tools:
      - Prometheus (метрики)
      - Grafana (дашборды)
      - Console Log (dev-режим)

  token_efficiency_policy:
    goal: 0.8
    llm_usage_limit: 0.2
    rule_precedence: ["temporal", "semantic", "structural"]
    src_autotrain_enabled: true
    cost_monitoring:
      enabled: true
      log_path: "./metrics/token_economy.log"

  development_notes:
    language: "Python 3.13+"
    framework: "DSPy 3.0.4"
    async_runtime: "Fast-LangGraph"
    version_control: "Git + YAML diff tracking"
    deployment_model: "Docker / Compose (microservice mode)"
    testing:
      - unit: "pytest"
      - integration: "dspy.test_utils"
      - simulation: "graph.simulate(feedback=True)"
```

---

## 🧠 Пояснение

| Раздел                      | Назначение                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------------- |
| **core_components**         | Полное описание модулей LDUP: парсер, SRC, Policy Optimizer, Validator, Metrics, Reinforcement |
| **data_flow**               | Последовательность событий — от входного документа до обновления правил                        |
| **rule_lifecycle**          | Формализует жизненный цикл YAML-правила                                                        |
| **integrations**            | Подключения внешних баз, агентов и систем мониторинга                                          |
| **token_efficiency_policy** | Цель по снижению токен-затрат и ограничения LLM                                                |
| **development_notes**       | Среда исполнения, инструменты, тестирование                                                    |

---

## ✅ Результат

* Этот файл можно использовать как **основной blueprint** при деплое LDUP.
* Он также может быть импортирован в **DSPy Project Builder** как `system manifest` для автоинициализации всех компонентов.
* Полностью совместим с YAML-валидацией DSPy и Fast-LangGraph orchestration.

---

