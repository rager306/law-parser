# Компоненты системы LDUP v5

## 1. Streaming Ingester (Ingester-S)
*   **Технология:** Python `lxml` (C-lib).
*   **Задача:** Токенизация WordML потока.
*   **Источник:** Проверенная логика в `scripts/validate_rlm_parsing.py`.

## 2. RLM-Core (Движок)
*   **Технология:** [RLM-Toolkit v2.1](research/AISecurity/repo/rlm-toolkit/).
*   **Функция:** Управление жизненным циклом фактов (L0-L3).
*   **SOTA:** Recursive Context Management (arXiv:2512.24601).

## 3. SQLite Knowledge Store
*   **Технология:** SQLite FTS5 + JSON1 extension.
*   **Задача:** Персистентное хранение кристаллов (C³) и иерархии связей.

## 4. Neuro-Symbolic Validator
*   **Технология:** Pydantic v2 + [FastEmbed](https://github.com/qdrant/fastembed).
*   **Задача:** Смешанная проверка на соответствие правилам (Regex) и семантическую корректность (LLM).
