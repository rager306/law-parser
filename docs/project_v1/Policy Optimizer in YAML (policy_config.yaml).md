Прекрасно ⚙️
ниже — полностью оформленный и документированный YAML-манифест конфигурации **Policy Optimizer** для твоего LDUP-парсера.
Файл описывает стратегию обучения, веса, пороги, приоритеты, параметры подкрепления и метрики мониторинга.

Он реализует подход *reinforcement governance over rules*:
каждый тип SRC-feedback оценивается по приросту точности, снижению LLM-зависимости, рискам конфликта и сложности алгоритма.

---

## 🧾 **`policy_config.yaml` — LDUP Policy Optimizer Configuration**

```yaml
policy_optimizer:
  version: 1.0
  description: >
    Политика самообучения DSPy-парсера LDUP.
    Управляет приоритетами обновления YAML-правил по категориям:
    structural, temporal, semantic.
    Использует reinforcement-модель для оптимального выбора применяемых изменений.

  general_settings:
    mode: "reinforcement"
    reward_strategy: "multi-armed-bandit"
    evaluation_window: 5          # итераций цикла SRC
    min_confidence_to_apply: 0.7  # минимальный PolicyScore для активации
    pending_threshold: 0.4        # порог отложенного правила
    decay_factor: 0.95            # постепенное затухание старых reward'ов

  weights:
    delta_accuracy: 0.4            # вес точности
    delta_llm_dependency: 0.3      # вес экономии токенов
    delta_conflict: 0.2            # штраф за потенциальный конфликт
    delta_complexity: 0.1          # штраф за увеличение сложности графа

  priorities:
    temporal:
      weight_multiplier: 1.3       # временные правила приоритетнее
      expected_gain: 0.05
      typical_conflict_risk: 0.02
    semantic:
      weight_multiplier: 1.0
      expected_gain: 0.03
      typical_conflict_risk: 0.05
    structural:
      weight_multiplier: 0.8
      expected_gain: 0.02
      typical_conflict_risk: 0.01

  confidence_adjustment:
    high_confidence: 0.85
    medium_confidence: 0.65
    low_confidence: 0.45

  decision_thresholds:
    activate_rule: 0.7             # активировать
    hold_rule: 0.4                 # отложить
    reject_rule: 0.4               # отклонить при score < 0.4

  conflict_detection:
    simulate_on_documents: 20      # документов для симуляции
    max_allowed_overlap: 0.1
    overlap_penalty: 0.15          # штраф за пересечение шаблонов
    time_limit_seconds: 15

  complexity_control:
    max_rule_size: 2000            # макс. строк кода/паттернов на модуль
    max_new_rules_per_cycle: 10
    performance_target_seconds: 3.0

  reward_update_policy:
    update_frequency: 1             # после каждого SRC цикла
    smoothing_window: 5
    learning_rate: 0.15
    exploration_rate: 0.1           # вероятность тестировать неопробованные паттерны
    reward_decay: 0.98
    negative_reward_penalty: 0.5

  metrics_monitoring:
    track:
      - accuracy
      - llm_usage
      - rule_conflicts
      - parsing_time
    improvement_goal:
      accuracy_gain: 0.03
      llm_usage_drop: 0.05
    evaluation_schedule: "each_iteration"
    metric_log: "./metrics/policy_metrics.jsonl"

  rule_promotion_pipeline:
    stages:
      - name: "candidate"
        description: "новое правило, добавленное SRC, ожидает оценку"
      - name: "validated"
        description: "прошло проверку схемы и симуляцию"
      - name: "active"
        description: "одобрено Policy Optimizer, применяется в Graph"
      - name: "archived"
        description: "отклонено или устарело"
    auto_archive_after_days: 60

  feedback_integration:
    src_inputs:
      - semantic_refinement
      - temporal_refinement
      - structural_refinement
    yaml_output_path: "./rules/"
    validation_module: "dspy.policy.validator"
    approval_logging: "./logs/policy_approval.log"

  alerting:
    enable_notifications: true
    notify_on_conflict: true
    notify_on_performance_drop: true
    channels:
      - console
      - file
    file_path: "./alerts/policy_alerts.log"
```

---

## 🧠 **Как работает Policy Optimizer на базе этого YAML**

1️⃣ **Загрузка**
DSPy Policy Engine читает YAML и создаёт объект `PolicyModel`,
инициализируя веса и приоритеты.

2️⃣ **Оценка**
Каждый SRC-feedback превращается в объект `RuleCandidate` с полями
`Δaccuracy`, `Δllm`, `Δconflict`, `Δcomplexity`, `confidence`.

3️⃣ **Вычисление PolicyScore**

```python
PolicyScore = (ΔAcc * 0.4) + (ΔLLM * 0.3) - (ΔConflict * 0.2) - (ΔComplexity * 0.1)
```

4️⃣ **Коррекция по типу правила**

```python
PolicyScore *= weight_multiplier[module_type]
```

5️⃣ **Сравнение с порогами**

* `≥ 0.7` → правило активируется;
* `0.4–0.7` → отправляется в pending для симуляции;
* `< 0.4` → отклоняется и архивируется.

6️⃣ **Обновление весов Reinforcement-модели**
Реальное улучшение на корпусе (accuracy ↑, LLM ↓) усиливает веса полезных типов правил.

---

## 📊 **Пример JSON-результатов после цикла**

```json
{
  "cycle": 12,
  "rules_applied": 3,
  "avg_policy_score": 0.68,
  "temporal_weight": 1.32,
  "semantic_weight": 0.98,
  "structural_weight": 0.75,
  "accuracy_gain": 0.042,
  "llm_usage_drop": 0.062,
  "conflict_rate": 0.009
}
```

---

## ✅ **Итог**

Этот `policy_config.yaml`:

* задаёт **матрицу обучения** Policy Optimizer;
* позволяет управлять **весами, порогами и поведением Reinforcement-логики** без изменения кода;
* формализует **«здравый смысл» самообучающейся юридической системы**:
  — *точность и экономия важнее агрессивного роста правил*,
  — *временные закономерности ценнее семантических по вкладу в стабильность*.

---

Хочешь, чтобы я следующим шагом показал, как этот Policy Optimizer подключается в **DSPy YAML-workflow** (через `ldup_system.yaml` → `policy_optimizer` секцию) и как он взаимодействует с YAML-Store и SRC-модулями в коде?
