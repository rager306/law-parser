# План v5: Разработка гибридного парсера НПА (LDUP/SALTP 2026)

Этот план полностью синхронизирован с архитектурными спецификациями в папке `docs/project_v1/` и содержит прямые ссылки на обосновывающие документы.

## 🧭 Когнитивная архитектура (SALTP 2026)
*Обоснование: [Arch_v0.01.md](docs/project_v1/Arch_v0.01.md) — Tri-Layer Reflexive Parsing Model.*

Реализуем **Self-Adaptive Legal Temporal Parser**, где DSPy 3.0.4 управляет рефлексивным ансамблем моделей.

### Слой 1: Perception (Восприятие)
*Цель: Формирование первичного структурированного образа документа.*
*Ссылка: [LDUP — Legal Neural Architecture.md](docs/project_v1/LDUP%20—%20Legal%20Neural%20Architecture.md) (уровень Perception).*
*   **DocumentIngester**: Мультиформатная загрузка (WordML 2003, DOCX, PDF, HTML). 
    *Обоснование: [LDUP_PRD_v1.0.md](docs/project_v1/LDUP_PRD_v1.0.md), стр. 31.*
*   **SourceDetector**: Определение источника (КонсультантПлюс, Гарант, pravo.gov.ru) для выбора набора правил (General vs Private YAML).
    *Обоснование: [ldup_system.yaml](docs/project_v1/ldup_system.yaml), секция inputs.*
*   **GEPA 3.5 (Structural Bootstrap)**: Первичное выделение «скелета» документа (главы, статьи) на основе XML-паттернов и эмбеддингов структуры.
    *Обоснование: [arch_v0.02.md](docs/project_v1/arch_v0.02.md), секция L1 Structural Layer.*
*   **SIMBA 2.2 (Morpho-Semantic Sensory)**: Первичное тегирование модальностей (обязанность, запрет) на уровне предложений.

### Слой 2: Understanding (Понимание)
*Цель: Глубокий семантический и темпоральный анализ.*
*Ссылка: [Arch_v0.01.md](docs/project_v1/Arch_v0.01.md) (слой Semantic-Temporal).*
*   **MiPROv3 (Temporal Resolver)**: Построение bi-temporal модели и извлечение интервалов действия.
    *Обоснование: [arch_v0.02.md](docs/project_v1/arch_v0.02.md), секция L2 Semantic-Temporal Layer.*
*   **S-LLM Segmenter**: Доуточнение границ сложных сегментов (сноски, примечания) с помощью Structure-Aware LLM.
    *Обоснование: [Arch_v0.01.md](docs/project_v1/Arch_v0.01.md), стр. 38.*
*   **HCO Cache (Hybrid Context Optimization)**: Кэширование семантических эмбеддингов между узлами для обеспечения 70-80% экономии токенов.
    *Обоснование: [Arch_v0.03_apdx_*Rule-First vs LLM-Assist Flow.md](docs/project_v1/Arch_v0.03_apdx_*Rule-First%20vs%20LLM-Assist%20Flow%20(LDUP%20Token%20Economy%20Architecture).md).*

### Слой 3: Reasoning (Рассуждение)
*Цель: Построение графа знаний и выявление связей.*
*Ссылка: [LDUP — Legal Neural Architecture.md](docs/project_v1/LDUP%20—%20Legal%20Neural%20Architecture.md) (уровень Reasoning).*
*   **TCGR (Temporal Causal Graph Reasoner)**: Плагин для инференса причинных связей («поправка X изменила норму Y»).
    *Обоснование: [arch_v0.02.md](docs/project_v1/arch_v0.02.md), секция E3 TCGR Plugin.*
*   **Cross-Reference Resolver**: Разрешение внутренних и внешних гиперссылок.
*   **GraphBuilder**: Формирование RDF*/JSON-LD триплетов с темпоральными ребрами.

### Слой 4: Learning (Обучение / Рефлексия)
*Цель: Обнаружение ошибок и генерация опыта.*
*Ссылка: [cycle SRC-feedback → YAML-patch.md](docs/project_v1/cycle%20SRC-feedback%20→%20YAML-patch.md).*
*   **SRC v2 (Reflexive Controllers)**: Группа контроллеров (Semantic, Temporal, Structural), генерирующих feedback.
    *Обоснование: [SRC correction cycle.md](docs/project_v1/SRC%20correction%20cycle.md).*
*   **Unified Feedback Queue**: Агрегация предложений по обновлению YAML-правил.

### Слой 5: Adaptation (Адаптация)
*Цель: Реконфигурация системы.*
*Ссылка: [Arch v.0.3 YAML = Behavioral Specification Layer.md](docs/project_v1/Arch%20v.0.3%20YAML%20=%20Behavioral%20Specification%20Layer.md).*
*   **Policy Optimizer**: Reinforcement-движок, принимающий решения об активации новых правил.
    *Обоснование: [Policy Optimizer in YAML (policy_config.yaml).md](docs/project_v1/Policy%20Optimizer%20in%20YAML%20(policy_config.yaml).md).*
*   **Neural Policy Tuning (NPT)**: Динамическая перенастройка маршрутов исполнения DSPy-графа.
    *Обоснование: [Arch_v0.01.md](docs/project_v1/Arch_v0.01.md), стр. 50.*
*   **YAML Validator**: Эмпирическая проверка правил на корпусе документов (simulation mode).

### Слой 6: Action (Действие / Экспорт)
*Цель: Выдача стандартизированных результатов.*
*Ссылка: [standarts.md](docs/project_v1/standarts.md).*
*   **Exporters**: 
    - Akoma Ntoso (международный)
    - **LegalDocML-Russia** (государственный РФ) — *Обоснование: [standarts.md](docs/project_v1/standarts.md), секция II.5.*
    - LegalRuleML (логический)
*   **Knowledge Persistence**: Запись в FalkorDB + Graffiti Temporal Layer.
    *Обоснование: [LDUP_PRD_v1.0.md](docs/project_v1/LDUP_PRD_v1.0.md), стр. 84.*

---

## 📂 Обновленная структура директорий (Blueprint)
*Обоснование структуры: [ldup_architecture.yaml](docs/project_v1/Architecture%20scheme%20in%20YAML-(ldup_architecture.yaml).md).*

```
src_parser/
├── core/
│   ├── hco_cache.py            # [Ref: arch_v0.03]
│   ├── models.py               # Pydantic (SALTP 2026 compliant)
│   └── policy_npt.py           # Neural Policy Tuning
├── perception/
│   ├── source_detector.py      # Выбор Private YAML (Consultant+)
│   └── preprocessors/          # Нормализаторы под WordML 2003
├── understanding/
│   ├── gepa_v35.py             # Structural Bootstrap (GEPA 3.5)
│   ├── simba_v22.py            # Morpho-Semantic Analysis (SIMBA 2.2)
│   └── miprov3_temporal.py     # Temporal Memory v3 Resolver
├── reasoning/
│   ├── tcgr_plugin.py          # Causal Reasoner (TCGR)
│   └── graph_builder.py        # RDF*/JSON-LD Generator
├── learning/
│   ├── src_controller_v2.py    # Reflexive Feedback (SRC v2)
│   └── feedback_queue.py       # Unified JSONL Queue
├── adaptation/
│   ├── policy_optimizer.py     # Policy Optimizer (Reinforcement)
│   └── yaml_validator.py       # [Ref: Arch v.0.3 YAML]
├── exporters/
│   ├── akoma_ntoso.py
│   ├── legaldocml_ru.py        # Спецификация РФ
│   └── legal_ruleml.py
├── yaml_store/
│   ├── general/                # Универсальные паттерны
│   └── private/                # Паттерны источников (44-ФЗ)
└── pipeline_saltp.py           # Главный рефлексивный пайплайн
```

---

## 🚀 План реализации (Ближайшие шаги)

1.  **Environment**: Настройка Python 3.13 и DSPy 3.0.4.
2.  **Declarative Base**: Создание `ldup_general.yaml` на основе [standarts.md](docs/project_v1/standarts.md).
3.  **HCO & Perception**: Реализация **HCO Cache** для обеспечения `llm_usage_rate < 0.2` ([LDUP_PRD_v1.0.md](docs/project_v1/LDUP_PRD_v1.0.md)).
4.  **Workflow**: Сборка Standalone DSPy графа (отладка перед LangGraph согласно [arch_v0.02_mvp.md](docs/project_v1/arch_v0.02_mvp.md)).
5.  **Reflexive Loop**: Настройка SRC v2 для 44-ФЗ ([cycle SRC-feedback → YAML-patch.md](docs/project_v1/cycle%20SRC-feedback%20→%20YAML-patch.md)).

---
**Критическое требование:** Соответствие "Rule-First vs LLM-Assist Flow". Доля LLM в анализе не должна превышать 20% после обучения на тестовом корпусе 44-ФЗ.
