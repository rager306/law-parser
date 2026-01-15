# LDUP v3 Self‑Improvement Protocol

## 1) Problem Detection (SRC/TRC/STC)

**Structural (STC)**
- неверные границы статьи/главы
- пропуск подпунктов (кириллица, смешанная нумерация)
- разрыв иерархии (Clause вне Part)

**Semantic (SRC)**
- неверная модальность (запрет ↔ разрешение)
- двойные отрицания
- утраченные определения

**Temporal (TRC)**
- invalid intervals (`valid_from >= valid_to`)
- отсутствует `effective_date`
- конкурирующие редакции

## 2) Feedback JSONL (обязательные поля)

```json
{
  "timestamp": "2026-01-15T12:00:00Z",
  "error_type": "semantic_misclassification",
  "module": "simba",
  "text_fragment": "запрещается не",
  "expected": "prohibition",
  "predicted": "permission",
  "confidence": 0.88,
  "source_id": "consultantplus_xml",
  "example_fragment": "Статья 33, часть 1, пункт 1"
}
```

## 3) YAML Patch (pending)

```yaml
semantic:
  modalities:
    - pending_add:
        pattern: "запрещается не"
        label: "prohibition_strong"
        rationale: "double negation should strengthen prohibition"
        source_id: "consultantplus_xml"
        example_fragment: "Статья 33, часть 1, пункт 1"
        status: "pending"
        confidence: 0.88
```

## 4) Validation & Simulation

- **Schema validation**: YAML structure + required fields
- **Conflict detection**: overlaps with existing rules
- **Mini‑corpus simulation**: N=10–20 docs, ensure no regressions

## 5) Versioning Policy

- **major**: изменение структуры или контрактов данных
- **minor**: новые правила/паттерны
- **patch**: исправление конфликтов/ошибок

## 6) DSPy 3.0.4 Constraints

- В DSPy нет нативных SRC/TRC/STC модулей → реализуются в LDUP.
- Policy Optimizer отсутствует → реализуется как кастомный LDUP‑компонент.
- В DSPy есть телепромптеры (GEPA/SIMBA/MIPROv2), которые **только compile‑time**.
