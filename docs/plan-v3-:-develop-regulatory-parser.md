I have created the following plan after thorough exploration and analysis of the codebase. Follow the below plan verbatim. Trust the files and references. Do not re-verify what's written in the plan. Explore only when absolutely necessary. First implement all the proposed file changes and then I'll review all the changes together at the end.

## Наблюдения по кодовой базе

Проект находится на начальной стадии разработки. Существует обширная документация по архитектуре LDUP (Legal Document Universal Parser) — **самообучающейся когнитивной системе**, основанной на DSPy 3.0.4 (см. `docs/project_v1/Arch_v0.01.md`, `arch_v0.02.md`, `arch_v0.03.md`). 

**Ключевые особенности архитектуры:**

1. **Многоформатная поддержка** (LDUP_PRD_v1.0.md, строка 31): "Поддержка всех форматов: WordML 2003, DOCX, RTF, HTML, PDF, TXT" — Word 2003 XML это только начальный этап, система должна адаптироваться к любому формату источника.

2. **Источник-специфичные паттерны** (LDUP_PRD_v1.0.md, строки 55-60): "General Skill YAML" (универсальные паттерны для всех НПА) + "Private Skill YAML" (частные шаблоны для конкретных актов и источников). Это означает, что система должна иметь механизм выбора правильного набора паттернов в зависимости от источника (КонсультантПлюс, Гарант, pravo.gov.ru).

3. **Tri-Layer Reflexive Parsing Model** (Arch_v0.01.md, строки 20-26): 
   - Structural-Contextual Layer (GEPA 3.5 + Structure-Aware LLM)
   - Semantic-Temporal Layer (SIMBA 2.2 + MiPROv3 + Temporal-Causal Graphs)
   - Reflexive Reasoning Layer (DSPy-SRC v2 + Neural Policy Tuning)

4. **Workflow парсера перед LangGraph интеграцией** (arch_v0.02_mvp.md, строки 6-12): "Сначала Workflow, потом Agent" — DSPy Graph должен быть отлажен как standalone система перед обертыванием в LangGraph.

5. **Pipeline с 6 этапами** (contracts/api.yaml, строки 28, 236-290): ingestion, preprocessing, structure, references, classification, postprocessing — каждый этап имеет свой интерфейс и выходную схему.

В папке `prompt_domain_44fz` содержатся YAML-спецификации как **декларативный язык права** — правила компилируются в DSPy Graph и обновляются автоматически через feedback. 44-ФЗ — это **первый тестовый документ для обучения системы**. Когда придёт документ с иной структурой (УК, НК, ТК), система должна обнаружить отклонения, сгенерировать новые гипотезы через SRC, обновить YAML через Policy Optimizer и адаптировать DSPy Graph без переписывания кода.

Технологический стек: Python 3.13, UV, lxml, pydantic, DSPy 3.0.4, LangGraph v2, FalkorDB, pymorphy3, razdel.

## Подход к реализации

Реализуем **самообучающуюся когнитивную систему** с 7 слоями (LDUP — Legal Neural Architecture.md):

1. **Perception Layer** — загрузка и нормализация (поддержка множества форматов и источников)
2. **Understanding Layer** — GEPA (иерархическое извлечение), SIMBA (морфо-семантика), MiPROv2 (темпоральность)
3. **Reasoning Layer** — TCGR (причинно-временные связи), GraphBuilder
4. **Learning Layer** — SRC/TRC/STC (обнаружение ошибок через feedback)
5. **Adaptation Layer** — Policy Optimizer (приоритизация правил через reinforcement)
6. **Action Layer** — экспорт в стандарты (Akoma Ntoso, LegalRuleML, NormML)
7. **Evolution Layer** — автоматическое обновление YAML и адаптация к новым структурам

YAML-спецификации — это **декларативный язык права**, который компилируется в исполняемый DSPy Graph, верифицируется формально и эмпирически, и обновляется через unified feedback architecture. Система готова к масштабированию на любые нормативные акты с произвольной структурой и источниками.

## Архитектурные слои и компоненты

### Слой 1: Perception (Восприятие)

**Ссылка на архитектуру:** LDUP — Legal Neural Architecture.md, таблица "Пояснение цикла LDUP Cognitive Loop", строка "Perception" → "Preprocessor, GEPA, SIMBA"

**Компоненты:**

1. **DocumentIngester** (поддержка множества форматов)
   - Загрузка Word 2003 XML (КонсультантПлюс) — основной формат
   - Загрузка DOCX (через python-docx)
   - Загрузка PDF (через PyMuPDF + docling)
   - Загрузка HTML (через lxml)
   - Загрузка TXT (plain text)
   - Определение формата автоматически
   - Ссылка: LDUP_PRD_v1.0.md, строка 31 — "Поддержка всех форматов: WordML 2003, DOCX, RTF, HTML, PDF, TXT"

2. **SourceDetector** (определение источника для выбора правильных паттернов)
   - Определение источника: КонсультантПлюс, Гарант, pravo.gov.ru, другие
   - Анализ метаданных документа (producer, version, encoding)
   - Выбор правильного набора паттернов (General YAML + Private YAML для источника)
   - Ссылка: LDUP_PRD_v1.0.md, строки 55-60 — "General Skill YAML" + "Private Skill YAML"

3. **FormatNormalizer** (нормализация к единому внутреннему формату)
   - Нормализация пробелов и кириллических кавычек
   - Декодирование HTML entities (&#167; → §, &#34; → ")
   - Удаление XML-комментариев, служебных тегов
   - Сохранение структуры параграфов и стилей (жирный текст для заголовков)
   - Ссылка: consultant_word2003xml.yaml, строки 11-26 — preprocessing rules

4. **MetadataExtractor** (извлечение метаданных документа)
   - Название документа
   - Номер документа (например, "44-ФЗ")
   - Дата принятия
   - Издатель/источник
   - Версия/редакция

**Выход:** нормализованный текст с метаданными источника и формата, готовый для Understanding Layer

**Критически важно:** система должна быть расширяемой для новых форматов и источников без изменения кода (через plugin-based ingestion, LDUP_PRD_v1.0.md, строка 24).

### Слой 2: Understanding (Понимание)

**Ссылка на архитектуру:** Arch_v0.01.md, строки 20-26 — "Semantic-Temporal Layer" (SIMBA-2.2 + MiPROv3 + Temporal-Causal Graphs)

**Компоненты:**

1. **GEPA** (Graph-Enhanced Prompt Architecture) — структурное извлечение
   - **Иерархическое парсинг** (не глобальный regex): Глава → Параграф → Статья → Часть → Пункт → Подпункт
   - Контекстный поиск паттернов только внутри родительского контекста
   - Адаптивные паттерны из YAML (загружаются из `parsing_prompt.yaml`)
   - Обнаружение нестандартных структур (например, "Раздел" вместо "Глава")
   - Ссылка: parsing_prompt.yaml, строки 31-140 — иерархия структуры нормативных актов
   - Ссылка: parsing_prompt.yaml, строки 235-250 — "hierarchical_parsing_required" правило (критически важно!)

2. **SIMBA** (Symbolic + Implicit Morphological Behavior Analyzer) — морфо-семантический анализ
   - Определение модальностей: обязанность, запрет, разрешение, определение, санкция
   - Русская морфология через pymorphy3 + razdel
   - Обнаружение двойных отрицаний ("запрещается не" = усиленный запрет)
   - Инверсии и сложные синтаксические конструкции
   - Ссылка: SRC correction cycle.md, строки 6-130 — пример обучения SIMBA на двойных отрицаниях
   - Ссылка: LDUP_PRD_v1.0.md, строка 45 — "Морфология (SIMBA): Морфоанализ и регулярные выражения"

3. **MiPROv2** (Temporal Resolver) — извлечение временных интервалов
   - Дата вступления в силу ("вступает в силу с")
   - Дата утраты силы ("утратил силу", "действует до")
   - Дата редакции ("в редакции от")
   - Bi-temporal модель: valid time (когда норма действует) vs transaction time (когда она была изменена)
   - Ссылка: parsing_prompt.yaml, строки 164-180 — temporal markers
   - Ссылка: Arch_v0.02.md, строка 86 — "MiPROv2 Temporal Memory v3 API"

4. **InvalidityDetector** — обнаружение недействующих норм
   - Маркеры утраты силы: "утратила силу", "утратил силу", "признана утратившей силу", "не применяется"
   - Ссылка: parsing_prompt.yaml, строки 141-163 — invalidity_detection patterns
   - Ссылка: 44fz.yaml, строки 92-103 — invalidity_markers для 44-ФЗ

5. **EditorialExtractor** — извлечение редакционных заметок
   - Извлечение редакционных заметок: "(в ред. от ...)"
   - Очистка текста от редакционных вставок
   - Ссылка: extractor-api.md, строки 116-170 — EditorialExtractor API

**Выход:** структурированное представление документа с семантикой и временем (Document объект с иерархией, модальностями, временными интервалами)

### Слой 3: Reasoning (Рассуждение)

**Ссылка на архитектуру:** LDUP — Legal Neural Architecture.md, таблица "Пояснение цикла LDUP Cognitive Loop", строка "Reasoning" → "TCGR, Graph Builder"

**Компоненты:**

1. **TCGR** (Temporal Causal Graph Reasoner) — причинно-временные связи
   - Связь между поправками и изменёнными нормами
   - Выявление конфликтов между версиями
   - Построение временного графа редакций
   - Определение причины изменения (какой ФЗ внёс изменение)
   - Ссылка: Arch_v0.02.md, строка 44 — "TCGR Extension: Инференс «почему изменилась норма»"
   - Ссылка: Arch_v0.01.md, строка 45 — "MiPROv3 Temporal Causal Resolver (AAAI 2026 Temporal-Reasoning Graphs)"

2. **GraphBuilder** — формирование RDF/JSON-LD представления
   - Создание узлов для каждого элемента (глава, статья, пункт)
   - Создание рёбер для иерархических и причинно-временных связей
   - Добавление метаданных (источник, версия, дата)
   - Подготовка к экспорту в FalkorDB
   - Ссылка: standarts.md, строки 191-237 — интеграция стандартов (Akoma Ntoso, LegalRuleML, MetaLex)

3. **CrossReferenceResolver** — разрешение внутренних и внешних ссылок
   - Разрешение ссылок на другие статьи ("см. статью 31")
   - Разрешение ссылок на другие законы ("Федеральный закон от 28.12.2013 N 396-ФЗ")
   - Ссылка: extractor-api.md, строки 13-71 — HyperlinkExtractor API

**Выход:** граф норм с причинно-временными связями, готовый для экспорта в FalkorDB

### Слой 4: Learning (Обучение)

**Ссылка на архитектуру:** LDUP — Legal Neural Architecture.md, таблица "Пояснение цикла LDUP Cognitive Loop", строка "Learning" → "SRC, TRC, STC"

**Компоненты:**

1. **SRC** (Semantic Refinement Controller) — обнаружение семантических ошибок
   - Сравнение ожидаемой vs предсказанной модальности
   - Обнаружение пропущенных паттернов (например, "запрещается не")
   - Генерация JSONL feedback с предложениями новых паттернов
   - Ссылка: SRC correction cycle.md, строки 1-194 — полный цикл обучения на примере "запрещается не"
   - Ссылка: SRC-cycles (temporal + semantic).md, строки 20-30 — таблица компонентов метасистемы

2. **TRC** (Temporal Refinement Controller) — обнаружение временных ошибок
   - Проверка логики интервалов (effectiveFrom < effectiveTo)
   - Обнаружение пропущенных дат
   - Обнаружение конфликтов между версиями
   - Генерация feedback для обновления MiPROv2 паттернов
   - Ссылка: SRC-cycles (temporal + semantic).md, строки 20-30 — TRC в таблице компонентов

3. **STC** (Structural Refinement Controller) — обнаружение структурных ошибок
   - Проверка иерархии (статья должна быть в главе)
   - Обнаружение нестандартных заголовков
   - Обнаружение новых уровней иерархии (например, "Раздел")
   - Генерация гипотез о новых структурных элементах
   - Ссылка: SRC-cycles (temporal + semantic).md, строки 20-30 — STC в таблице компонентов

4. **FeedbackQueue** — централизованная очередь всех feedback'ов
   - Объединение feedback'ов из SRC, TRC, STC
   - Приоритизация по типу и уверенности
   - Сохранение в JSONL формате
   - Передача в Policy Optimizer
   - Ссылка: SRC-cycles (temporal + semantic).md, строки 35-65 — диаграмма unified feedback architecture

**Выход:** JSONL файлы с предложениями по улучшению, готовые для Policy Optimizer

### Слой 5: Adaptation (Адаптация)

**Ссылка на архитектуру:** LDUP — Legal Neural Architecture.md, таблица "Пояснение цикла LDUP Cognitive Loop", строка "Policy" → "Policy Optimizer"

**Компоненты:**

1. **PolicyOptimizer** — мета-контроллер DSPy (reinforcement engine)
   - Загрузка feedback'ов из FeedbackQueue
   - Оценка полезности каждого правила:
     - ΔAccuracy: на сколько улучшит точность
     - ΔLLM: на сколько уменьшит обращения к LLM
     - ΔConflict: риск конфликта с существующими правилами
   - Приоритизация через multi-armed bandit алгоритм
   - Решение для каждого feedback: activate / pending / reject
   - Обновление весов на основе результатов
   - Ссылка: Policy Optimizer in DSPy-workflow LDUP.md, строки 1-202 — полная интеграция Policy Optimizer
   - Ссылка: SRC-cycles (temporal + semantic).md, строки 68-112 — как работает Policy Optimizer

2. **YAMLValidator** — проверка новых YAML-правил
   - Синтаксис и JSON-schema
   - Логические конфликты с существующими правилами
   - Симуляция на тестовом наборе (10-20 документов)
   - Проверка совместимости с иерархией
   - Возврат статуса: OK / WARN / REJECT
   - Ссылка: Arch v.0.3 YAML = Behavioral Specification Layer.md, строки 134-237 — верификация YAML-алгоритмов

3. **YAMLStore** — хранилище правил с версионированием
   - **active**: применяются в DSPy Graph
   - **pending**: ожидают валидации
   - **archived**: отклонённые или устаревшие
   - История версий для отката
   - Загрузка General YAML (универсальные паттерны)
   - Загрузка Private YAML (специфичные для источника/документа)
   - Ссылка: LDUP_PRD_v1.0.md, строки 55-60 — General Skill YAML + Private Skill YAML
   - Ссылка: Policy Optimizer in DSPy-workflow LDUP.md, строки 96-107 — YAML-Store Integration

4. **DSPyGraphBuilder** — компиляция YAML-правил в исполняемый DSPy Graph
   - Загрузка RuleSpec из YAMLStore
   - Создание узлов GEPA, SIMBA, MiPROv2, TCGR
   - Установка зависимостей между узлами
   - Пересборка при обновлении YAML-правил
   - Ссылка: Arch v.0.3 YAML = Behavioral Specification Layer.md, строки 25-132 — как YAML превращается в алгоритм

**Выход:** обновлённые YAML-правила, готовые к применению в DSPy Graph, и пересобранный DSPy Graph с новыми правилами

### Слой 6: Action (Действие)

**Ссылка на архитектуру:** LDUP — Legal Neural Architecture.md, таблица "Пояснение цикла LDUP Cognitive Loop", строка "Knowledge" → "FalkorDB, LegalRuleML, LangGraph"

**Компоненты:**

1. **AkomaNtosoExporter** — экспорт в Akoma Ntoso XML (международный стандарт)
   - Преобразование Document в Akoma Ntoso структуру
   - Ссылка: standarts.md, строки 32-76 — Akoma Ntoso интеграция

2. **LegalRuleMLExporter** — экспорт в LegalRuleML (логика и деонтика норм)
   - Преобразование модальностей в LegalRuleML структуру
   - Добавление временных характеристик
   - Ссылка: standarts.md, строки 79-115 — LegalRuleML интеграция

3. **NormMLExporter** — экспорт в NormML JSON (для обучения LLM)
   - Преобразование норм в NormML формат
   - Ссылка: standarts.md, строки 139-158 — NormML интеграция

4. **FalkorDBWriter** — запись в граф БД с temporal слоем
   - Запись узлов и рёбер в FalkorDB
   - Использование Graffiti Temporal Layer для bi-temporal модели
   - Ссылка: LDUP_PRD_v1.0.md, строка 84 — "Temporal Graph (FalkorDB + Graffiti)"

5. **LangGraphInterface** — интеграция с LangGraph агентами для RAG/QA
   - Обертывание DSPy Graph в LangGraph агента
   - Ссылка: arch_v0.02_mvp.md, строки 1-133 — стратегия интеграции с LangGraph

**Выход:** структурированные данные в стандартных форматах, готовые для использования в LangGraph агентах

### Слой 7: Evolution (Эволюция)

**Ссылка на архитектуру:** LDUP — Legal Neural Architecture.md, таблица "Пояснение цикла LDUP Cognitive Loop", строка "Reinforcement" → "Reinforcement Engine, Metrics"

**Компоненты:**

1. **MetricsCollector** — сбор метрик для каждого этапа
   - Structural Accuracy: % правильно извлечённых элементов
   - Temporal Extraction: % правильно извлечённых дат
   - Semantic Classification: % правильно определённых модальностей
   - LLM Usage Rate: % документов, требующих LLM-ассистента
   - Adaptation Speed: время адаптации к новой структуре
   - Rule Quality: % активных правил, которые улучшают точность
   - Ссылка: LDUP_PRD_v1.0.md, строки 99-108 — Success Criteria

2. **ReinforcementEngine** — усиление полезных правил
   - Обновление весов в Policy Optimizer
   - Отслеживание эволюции точности
   - Ссылка: SRC-cycles (temporal + semantic).md, строки 154-163 — Metrics Collector в диаграмме

3. **AdaptationMonitor** — мониторинг адаптации к новым структурам
   - Обнаружение новых типов документов
   - Отслеживание скорости адаптации
   - Ссылка: LDUP_PRD_v1.0.md, строка 26 — "Δ accuracy +5% после 3 циклов SRC"

**Выход:** метрики и статистика эволюции системы, используемые для reinforcement learning

### Структура директорий

```
src_parser/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── models.py              # Pydantic модели для всех слоёв
│   ├── exceptions.py          # Специфичные исключения
│   └── constants.py           # Константы и регулярные выражения
├── yaml_store/
│   ├── __init__.py
│   ├── loader.py              # Загрузчик YAML-спецификаций
│   ├── validator.py           # Валидатор YAML-правил
│   ├── store.py               # Хранилище с версионированием
│   └── schemas/               # JSON-схемы для YAML
├── perception/
│   ├── __init__.py
│   ├── loaders/
│   │   ├── base.py
│   │   └── xml_loader.py      # Word 2003 XML
│   ├── preprocessors/
│   │   ├── base.py
│   │   └── xml_preprocessor.py
│   └── source_detector.py
├── understanding/
│   ├── __init__.py
│   ├── gepa/
│   │   ├── structural_extractor.py  # Иерархическое извлечение
│   │   └── patterns.py              # Паттерны из YAML
│   ├── simba/
│   │   ├── semantic_analyzer.py     # Морфо-семантический анализ
│   │   └── modality_detector.py     # Определение модальностей
│   └── temporal/
│       ├── temporal_resolver.py     # MiPROv2
│       └── date_parser.py           # Парсинг дат
├── reasoning/
│   ├── __init__.py
│   ├── tcgr/
│   │   ├── causal_graph.py          # Причинно-временные связи
│   │   └── conflict_detector.py     # Обнаружение конфликтов
│   └── graph_builder.py             # Построение RDF/JSON-LD
├── learning/
│   ├── __init__.py
│   ├── controllers/
│   │   ├── semantic_rc.py           # SRC
│   │   ├── temporal_rc.py           # TRC
│   │   ├── structural_rc.py         # STC
│   │   └── feedback_queue.py        # Единая очередь
│   └── validators/
│       ├── structural_validator.py
│       └── semantic_validator.py
├── adaptation/
│   ├── __init__.py
│   ├── policy_optimizer.py          # Policy Optimizer (DSPy)
│   ├── reinforcement_engine.py      # Multi-armed bandit
│   └── metrics_collector.py         # Сбор метрик
├── exporters/
│   ├── __init__.py
│   ├── akoma_ntoso.py
│   ├── legal_ruleml.py
│   ├── normml.py
│   └── falkordb_writer.py
├── utils/
│   ├── __init__.py
│   ├── logging.py              # Структурированное логирование
│   └── metrics.py              # Сбор метрик
├── pipeline.py                 # LawParser класс (главный пайплайн)
├── dspy_graph.py               # Построение DSPy Graph
└── cli.py                      # CLI интерфейс
```

## Ключевые инновации архитектуры

### 1. Иерархический парсинг вместо глобального regex
**Проблема:** глобальный поиск `^\d+\.` даёт 771 ложное срабатывание вместо 3 корректных частей в статье 1.

**Решение:** 
```
Глава → Параграф → Статья → Часть → Пункт → Подпункт
```
Каждый уровень ищет паттерны только внутри контекста родителя.

**Ссылка:** parsing_prompt.yaml, строки 235-250 — "hierarchical_parsing_required" правило с тестовым результатом "Глобально: ~771 частей (ложные срабатывания) vs Контекстно: 3 части в Статье 1 (корректно)"

### 2. Многоформатная и многоисточниковая поддержка
**Вместо:** hardcoded поддержка только Word 2003 XML
**Используем:** plugin-based ingestion с поддержкой:
- Форматов: WordML 2003, DOCX, RTF, HTML, PDF, TXT (LDUP_PRD_v1.0.md, строка 31)
- Источников: КонсультантПлюс, Гарант, pravo.gov.ru, другие
- Выбор правильного набора паттернов (General YAML + Private YAML) в зависимости от источника

**Ссылка:** LDUP_PRD_v1.0.md, строки 55-60 — "General Skill YAML" + "Private Skill YAML"

### 3. YAML как декларативный язык права
**Вместо:** hardcoded паттерны в коде
**Используем:** YAML-спецификации (из `prompt_domain_44fz/`), которые:
- Читаются человеком (не требуют знания Python)
- Компилируются в DSPy Graph (GEPA/SIMBA/MiPROv2 узлы)
- Верифицируются формально (синтаксис, схема) и эмпирически (тестирование на корпусе)
- Обновляются автоматически через SRC-циклы без переписывания кода

**Ссылка:** Arch v.0.3 YAML = Behavioral Specification Layer.md, строки 1-255 — полная система верификации YAML-алгоритмов

### 4. Unified SRC-Policy Feedback Architecture
**Вместо:** отдельные feedback-циклы для каждого типа ошибки
**Используем:** единую `FeedbackQueue`, которую `PolicyOptimizer` приоритизирует и применяет

Все feedback'ы (semantic, temporal, structural) идут в одну очередь → Policy Optimizer оценивает полезность → YAMLValidator проверяет конфликты → YAMLStore обновляет правила → DSPy Graph пересобирается.

**Ссылка:** SRC-cycles (temporal + semantic).md, строки 35-65 — диаграмма unified feedback architecture

### 5. Reinforcement Learning для выбора правил
**Вместо:** ручного выбора, какие правила применять
**Используем:** multi-armed bandit алгоритм в Policy Optimizer, который:
- Оценивает каждое правило по метрикам: ΔAccuracy, ΔLLM, ΔConflict
- Усиливает полезные правила (повышает их вес)
- Ослабляет бесполезные (понижает вес или архивирует)
- Адаптирует стратегию на основе результатов

**Ссылка:** SRC-cycles (temporal + semantic).md, строки 82-112 — как работает Policy Optimizer

### 6. Адаптация к новым структурам документов
**Когда приходит новый документ с иной структурой (например, Уголовный кодекс):**

1. GEPA пытается применить известные паттерны (Глава, Статья, Часть)
2. Обнаруживает отклонения (например, "Раздел" вместо "Глава", "Пункт" вместо "Части")
3. STC (Structural Refinement Controller) генерирует гипотезы:
   - "Раздел" = новый уровень иерархии?
   - Где он находится в иерархии? (выше или ниже Главы?)
   - Какой паттерн его определяет?
4. Policy Optimizer оценивает гипотезы на тестовом наборе
5. Лучшие гипотезы добавляются в YAML как pending
6. YAMLValidator проверяет совместимость с существующими правилами
7. Новые правила активируются
8. DSPy Graph пересобирается
9. Система готова к следующему документу этого типа

**Результат:** система адаптируется к произвольным структурам без переписывания кода.

### 7. Tri-Layer Reflexive Parsing Model (2026)
**Архитектура состоит из трёх слоёв:**

1. **Structural-Contextual Layer** (GEPA 3.5 + Structure-Aware LLM)
   - Автоматическое извлечение структуры и ссылок
   - Ссылка: Arch_v0.01.md, строки 20-26

2. **Semantic-Temporal Layer** (SIMBA 2.2 + MiPROv3 + Temporal-Causal Graphs)
   - Морфология, логика норм, временные ограничения
   - Ссылка: Arch_v0.01.md, строки 20-26

3. **Reflexive Reasoning Layer** (DSPy-SRC v2 + Neural Policy Tuning)
   - Самообучение и реконфигурация пайплайна
   - Ссылка: Arch_v0.01.md, строки 20-26

### 8. Workflow парсера перед LangGraph интеграцией
**Стратегия:** "Сначала Workflow, потом Agent"

1. Отладка DSPy Workflow как standalone системы
2. Обертывание в LangGraph агента
3. Интеграция в async runtime (Fast-LangGraph)

**Ссылка:** arch_v0.02_mvp.md, строки 6-133 — полная стратегия интеграции

### 9. Pipeline с 6 этапами обработки
**Каждый этап имеет свой интерфейс и выходную схему:**

1. **Ingestion** — загрузка документа
2. **Preprocessing** — нормализация
3. **Structure** — извлечение структуры
4. **References** — извлечение ссылок
5. **Classification** — классификация
6. **Postprocessing** — постобработка

**Ссылка:** contracts/api.yaml, строки 28, 236-290 — полная спецификация pipeline этапов

## Модели данных (Pydantic)

Определить модели для представления структуры документа:

- `Document`: корневая модель (метаданные, главы, параграфы, статьи)
- `Chapter`: глава (номер, название, параграфы/статьи)
- `Paragraph`: параграф (номер, название, статьи)
- `Article`: статья (номер, название, части, статус действительности)
- `Part`: часть статьи (номер, текст, пункты)
- `Clause`: пункт (номер, текст, подпункты)
- `Subclause`: подпункт (буква, текст)
- `TemporalInfo`: временная информация (дата вступления, утраты силы, редакции)
- `EditorialNote`: редакционная заметка
- `Modality`: модальность нормы (обязанность, запрет, разрешение, определение, санкция)
- `Feedback`: JSONL feedback от SRC/TRC/STC
- `YAMLRule`: правило в YAML Store (с версионированием и статусом)

Модели должны:
- Поддерживать вложенную иерархию
- Валидировать на уровне Pydantic (длина полей, обязательность, типы)
- Сериализоваться в JSON для экспорта
- Поддерживать метаданные (источник, версия, дата)

## YAML Store и Компиляция в DSPy Graph

### YAMLStore (file:src_parser/yaml_store/store.py)
Хранилище правил с версионированием:
- Загрузка YAML-спецификаций из `prompt_domain_44fz/`
- Управление статусами: active / pending / archived
- История версий для отката
- API для обновления правил через Policy Optimizer

### YAMLValidator (file:src_parser/yaml_store/validator.py)
Валидация новых YAML-правил:
- Синтаксис и JSON-schema
- Логические конфликты с существующими правилами
- Симуляция на тестовом наборе (10-20 документов)
- Проверка совместимости с иерархией

### DSPyGraphBuilder (file:src_parser/dspy_graph.py)
Компиляция YAML-правил в исполняемый DSPy Graph:
- Загрузка RuleSpec из YAMLStore
- Создание узлов GEPA, SIMBA, MiPROv2, TCGR
- Установка зависимостей между узлами
- Пересборка при обновлении YAML-правил

### ParserConfig (file:src_parser/core/config.py)
Загрузка конфигураций:
- Загрузка `parsing_prompt.yaml` (паттерны структуры)
- Загрузка `structures/44fz.yaml` (специфика 44-ФЗ)
- Загрузка `sources/consultant_word2003xml.yaml` (правила предобработки)
- Загрузка `validation/structural_rules.yaml` и `validation/semantic_rules.yaml`
- Загрузка `legislation_hierarchy.yaml` (классификация документов)
- Поддержка переопределения паттернов через параметры
- Использовать `pydantic-settings` для валидации

## Perception Layer (Восприятие)

### XMLLoader (file:src_parser/perception/loaders/xml_loader.py)
Загрузка Word 2003 XML:
- Чтение XML файла с проверкой размера (макс. 10 МБ)
- Парсинг через `lxml.etree` с обработкой namespace `w:` (Word 2003 ML)
- Извлечение метаданных документа (название, номер, дата)
- Определение источника (КонсультантПлюс, Гарант, pravo.gov.ru)
- Возврат `lxml.etree.Element` для дальнейшей обработки
- Обработка ошибок: `XMLParsingError`, `ContentTooLargeError`

### XMLPreprocessor (file:src_parser/perception/preprocessors/xml_preprocessor.py)
Нормализация XML согласно `consultant_word2003xml.yaml`:
- Удаление XML-комментариев, `w:proofErr`, `w:rsid`
- Нормализация пробелов и кириллических кавычек
- Декодирование HTML entities (`&#167;` → `§`, `&#34;` → `"`)
- Извлечение текста из `w:t` элементов
- Определение жирного текста (`w:b`) для заголовков
- Сохранение структуры параграфов
- Возврат нормализованного текста с метаданными

### SourceDetector (file:src_parser/perception/source_detector.py)
Определение источника документа:
- Анализ метаданных XML (producer, version)
- Определение формата (Word 2003 XML, DOCX, HTML, TXT)
- Выбор правильного набора паттернов из YAML
- Возврат `SourceInfo` с типом источника и рекомендуемыми паттернами

## Understanding Layer (Понимание)

### GEPA - Structural Extractor (file:src_parser/understanding/gepa/structural_extractor.py)
Иерархическое извлечение структуры (критически важно: контекстный поиск, не глобальный regex):

**Алгоритм:**
```
1. Загрузить текст документа
2. Найти все главы (Глава N. НАЗВАНИЕ) — паттерн из YAML
3. Для каждой главы:
   a. Найти параграфы (§ N. НАЗВАНИЕ) внутри главы
   b. Для каждого параграфа (или главы, если нет параграфов):
      i. Найти статьи (Статья N. НАЗВАНИЕ)
      ii. Для каждой статьи:
          - Найти части (1. текст, 2. текст) внутри статьи
          - Для каждой части:
            * Найти пункты (1) текст, 2) текст) внутри части
            * Для каждого пункта:
              - Найти подпункты (а) текст, б) текст) внутри пункта
```

**Компоненты:**
- `extract_chapters()`: извлечение глав с паттерном из YAML
- `extract_paragraphs_in_chapter()`: контекстный поиск параграфов
- `extract_articles_in_context()`: контекстный поиск статей
- `extract_parts_in_article()`: контекстный поиск частей
- `extract_clauses_in_part()`: контекстный поиск пунктов (с поддержкой составной нумерации 7.1))
- `extract_subclauses_in_clause()`: контекстный поиск подпунктов

**Критически важно:** каждый уровень ищет паттерны только внутри контекста родителя. Это избегает 771 ложного срабатывания (из `parsing_prompt.yaml`).

### SIMBA - Semantic Analyzer (file:src_parser/understanding/simba/semantic_analyzer.py)
Морфо-семантический анализ:

**Компоненты:**
- `detect_modality()`: определение модальности (обязанность, запрет, разрешение, определение, санкция)
  - Использует pymorphy3 для морфологии
  - Использует YAML-паттерны для семантики
  - Обнаруживает двойные отрицания ("запрещается не" = усиленный запрет)
  
- `extract_editorial_notes()`: извлечение редакционных заметок ("в ред. от", "примечание")
- `detect_invalidity_markers()`: обнаружение маркеров утраты силы ("утратил силу", "не применяется")

**Использует:** pymorphy3, razdel для русской морфологии и синтаксиса

### MiPROv2 - Temporal Resolver (file:src_parser/understanding/temporal/temporal_resolver.py)
Извлечение временных интервалов:

**Компоненты:**
- `extract_effective_date()`: дата вступления в силу ("вступает в силу с")
- `extract_expiration_date()`: дата утраты силы ("утратил силу", "действует до")
- `extract_amendment_date()`: дата редакции ("в редакции от")
- `parse_date()`: парсинг дат в формате DD.MM.YYYY
- `build_temporal_intervals()`: построение bi-temporal модели (valid time vs transaction time)

**Выход:** `TemporalInfo` объекты с интервалами действия

## Reasoning Layer (Рассуждение)

### TCGR - Causal Graph Reasoner (file:src_parser/reasoning/tcgr/causal_graph.py)
Причинно-временные связи:
- Связь между поправками и изменёнными нормами
- Выявление конфликтов между версиями
- Построение временного графа редакций
- Определение причины изменения (какой ФЗ внёс изменение)

### GraphBuilder (file:src_parser/reasoning/graph_builder.py)
Формирование RDF/JSON-LD представления:
- Создание узлов для каждого элемента (глава, статья, пункт)
- Создание рёбер для иерархических и причинно-временных связей
- Добавление метаданных (источник, версия, дата)
- Подготовка к экспорту в FalkorDB

## Learning Layer (Обучение)

### SRC - Semantic Refinement Controller (file:src_parser/learning/controllers/semantic_rc.py)
Обнаружение семантических ошибок:
- Сравнение ожидаемой vs предсказанной модальности
- Обнаружение пропущенных паттернов (например, "запрещается не")
- Генерация JSONL feedback с предложениями новых паттернов
- Оценка уверенности (confidence)

### TRC - Temporal Refinement Controller (file:src_parser/learning/controllers/temporal_rc.py)
Обнаружение временных ошибок:
- Проверка логики интервалов (effectiveFrom < effectiveTo)
- Обнаружение пропущенных дат
- Обнаружение конфликтов между версиями
- Генерация feedback для обновления MiPROv2 паттернов

### STC - Structural Refinement Controller (file:src_parser/learning/controllers/structural_rc.py)
Обнаружение структурных ошибок:
- Проверка иерархии (статья должна быть в главе)
- Обнаружение нестандартных заголовков
- Обнаружение новых уровней иерархии (например, "Раздел")
- Генерация гипотез о новых структурных элементах

### FeedbackQueue (file:src_parser/learning/controllers/feedback_queue.py)
Централизованная очередь feedback'ов:
- Объединение feedback'ов из SRC, TRC, STC
- Приоритизация по типу и уверенности
- Сохранение в JSONL формате
- Передача в Policy Optimizer

## Adaptation Layer (Адаптация)

### PolicyOptimizer (file:src_parser/adaptation/policy_optimizer.py)
Мета-контроллер DSPy (reinforcement engine):
- Загрузка feedback'ов из FeedbackQueue
- Оценка полезности каждого правила:
  - ΔAccuracy: на сколько улучшит точность
  - ΔLLM: на сколько уменьшит обращения к LLM
  - ΔConflict: риск конфликта с существующими правилами
- Приоритизация через multi-armed bandit алгоритм
- Решение для каждого feedback: activate / pending / reject
- Обновление весов на основе результатов

### YAMLValidator (file:src_parser/adaptation/yaml_validator.py)
Проверка новых YAML-правил:
- Синтаксис и JSON-schema
- Логические конфликты с существующими правилами
- Симуляция на тестовом наборе (10-20 документов)
- Проверка совместимости с иерархией
- Возврат статуса: OK / WARN / REJECT

### MetricsCollector (file:src_parser/adaptation/metrics_collector.py)
Сбор метрик для reinforcement:
- Structural Accuracy: % правильно извлечённых элементов
- Temporal Extraction: % правильно извлечённых дат
- Semantic Classification: % правильно определённых модальностей
- LLM Usage Rate: % документов, требующих LLM-ассистента
- Adaptation Speed: время адаптации к новой структуре
- Rule Quality: % активных правил, которые улучшают точность

## Action Layer (Действие)

### Exporters (file:src_parser/exporters/)
Экспорт в стандартные форматы:
- `AkomaNtosoExporter`: Akoma Ntoso XML (международный стандарт)
- `LegalRuleMLExporter`: LegalRuleML (логика и деонтика норм)
- `NormMLExporter`: NormML JSON (для обучения LLM)
- `FalkorDBWriter`: запись в граф БД с temporal слоем

## Главный пайплайн (file:src_parser/pipeline.py)

Класс `LawParser` — главный оркестратор:

```python
class LawParser:
    def __init__(self, config: ParserConfig, enable_learning: bool = True):
        self.config = config
        self.yaml_store = YAMLStore(config)
        self.dspy_graph = DSPyGraphBuilder(self.yaml_store).build()
        self.enable_learning = enable_learning
        
        # Perception
        self.loader = XMLLoader()
        self.preprocessor = XMLPreprocessor(config)
        self.source_detector = SourceDetector()
        
        # Understanding
        self.gepa = GEPAExtractor(self.yaml_store)
        self.simba = SIMBAAnalyzer(self.yaml_store)
        self.temporal = TemporalResolver(self.yaml_store)
        
        # Reasoning
        self.tcgr = TCGRReasoner()
        self.graph_builder = GraphBuilder()
        
        # Learning (если включено)
        if self.enable_learning:
            self.src = SemanticRC()
            self.trc = TemporalRC()
            self.stc = StructuralRC()
            self.feedback_queue = FeedbackQueue()
            self.policy_optimizer = PolicyOptimizer(self.yaml_store)
        
        # Validators
        self.structural_validator = StructuralValidator(config)
        self.semantic_validator = SemanticValidator(config)
    
    def parse(self, xml_path: Path, ground_truth: Optional[Document] = None) -> Document:
        """
        Полный пайплайн парсинга с опциональным обучением.
        
        Этапы:
        1. Perception: загрузка и нормализация
        2. Understanding: извлечение структуры, семантики, времени
        3. Reasoning: построение графа и причинно-временных связей
        4. Learning (опционально): обнаружение ошибок и генерация feedback
        5. Adaptation (опционально): обновление YAML-правил через Policy Optimizer
        6. Validation: проверка результатов
        7. Action: экспорт в стандарты
        """
        # 1. Perception
        xml_element = self.loader.load(xml_path)
        normalized_text = self.preprocessor.preprocess(xml_element)
        source_info = self.source_detector.detect(xml_element)
        
        # 2. Understanding
        document = self.gepa.extract_structure(normalized_text)
        document = self.simba.analyze_semantics(document)
        document = self.temporal.extract_temporal_info(document)
        
        # 3. Reasoning
        document = self.tcgr.build_causal_graph(document)
        graph = self.graph_builder.build(document)
        
        # 4-5. Learning & Adaptation (если включено и есть ground truth)
        if self.enable_learning and ground_truth:
            errors = self._compare_with_ground_truth(document, ground_truth)
            for error in errors:
                feedback = self._generate_feedback(error)
                self.feedback_queue.add(feedback)
            
            # Policy Optimizer обрабатывает feedback
            self.policy_optimizer.process_feedback_queue(self.feedback_queue)
            
            # Пересобираем DSPy Graph с новыми правилами
            self.dspy_graph = DSPyGraphBuilder(self.yaml_store).build()
        
        # 6. Validation
        validation_errors = self.structural_validator.validate(document)
        validation_errors += self.semantic_validator.validate(document)
        
        # 7. Action (экспорт)
        document.metadata.validation_errors = validation_errors
        
        return document
```

Пайплайн логирует каждый этап через `structlog` и собирает метрики.

## CLI интерфейс (file:src_parser/cli.py)

```bash
law-parser parse <xml_file> --output <json_file> --validate --learn --verbose
```

Опции:
- `--output`: путь для сохранения результата (JSON/YAML)
- `--validate`: включить валидацию
- `--learn`: включить обучение (SRC-циклы)
- `--ground-truth`: путь к ground truth для обучения
- `--verbose`: детальное логирование
- `--config`: путь к кастомной YAML конфигурации

Использовать `rich` для красивого вывода прогресса и результатов.

## Тестирование

**Unit тесты** (`tests/unit/`):
- Тесты иерархического парсинга (GEPA)
- Тесты морфо-семантического анализа (SIMBA)
- Тесты временного разрешения (MiPROv2)
- Тесты SRC/TRC/STC контроллеров
- Тесты Policy Optimizer
- Тесты YAML валидации

**Integration тесты** (`tests/integration/`):
- Полный пайплайн на 44-ФЗ
- Адаптация к новой структуре (mock документ)
- SRC-цикл: ошибка → feedback → обновление YAML → улучшение

**Fixtures** (`tests/fixtures/`):
- Примеры из `prompt_domain_44fz/structures/archive/`
- Минимальные XML примеры для каждого уровня иерархии
- Примеры с ошибками для тестирования SRC

## Документация

- **Architecture.md**: полная архитектура с диаграммами (7 слоёв)
- **YAML_Specification.md**: как писать YAML-правила
- **Adaptation_Guide.md**: как система адаптируется к новым структурам
- **SRC_Learning_Cycles.md**: как работают SRC/TRC/STC циклы
- **Policy_Optimizer.md**: как Policy Optimizer приоритизирует правила
- **API_Reference.md**: API каждого компонента

## Фазы реализации

**Фаза 1 (Неделя 1-2):** Инфраструктура
- Модели данных (Pydantic)
- YAML Store и Validator
- Логирование и метрики

**Фаза 2 (Неделя 3-4):** Perception + Understanding
- XML Loader и Preprocessor
- GEPA (иерархическое извлечение)
- SIMBA (морфо-семантический анализ)
- MiPROv2 (временное разрешение)

**Фаза 3 (Неделя 5-6):** Reasoning + Learning
- TCGR (причинно-временные связи)
- SRC/TRC/STC (обнаружение ошибок)
- FeedbackQueue

**Фаза 4 (Неделя 7-8):** Adaptation
- Policy Optimizer
- Reinforcement Engine
- Автоматическое обновление YAML

**Фаза 5 (Неделя 9-10):** Action + Testing
- Exporters (Akoma Ntoso, LegalRuleML, NormML)
- FalkorDB Writer
- Unit и Integration тесты

**Фаза 6 (Неделя 11-12):** CLI, документация, оптимизация
- CLI интерфейс
- Полная документация
- Оптимизация производительности

## Критические успешные факторы

1. **Иерархический парсинг** — избежать 771 ложного срабатывания
2. **YAML как источник истины** — все правила в YAML, не в коде
3. **Unified feedback architecture** — все SRC-циклы в одной очереди
4. **Policy Optimizer** — интеллектуальный выбор, какие правила применять
5. **Автоматическая верификация** — новые правила проходят полный цикл проверки
6. **Метрики и мониторинг** — видеть прогресс адаптации
7. **Расширяемость** — легко добавить новый тип документа без переписывания кода

## Успех означает

- ✅ Парсер 44-ФЗ работает с точностью ≥95%
- ✅ Система обнаруживает новые структурные элементы в новых документах
- ✅ SRC-циклы автоматически генерируют улучшения
- ✅ Policy Optimizer приоритизирует полезные правила
- ✅ LLM-использование снижается с каждой итерацией
- ✅ Система готова к масштабированию на другие документы (УК, НК, ТК)
- ✅ Новый документ с иной структурой адаптируется за 1-2 цикла обучения
