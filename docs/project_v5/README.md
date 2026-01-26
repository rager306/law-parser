# LDUP v5: Recursive Legal Document Understanding Parser

**Версия:** 5.1 (Revision 2026.01.26 - Core Focus)
**Статус:** Промышленная спецификация (CPU-Optimized)
**Фокус:** Извлечение знаний, масштабируемость, отказ от избыточных протоколов (MCP).

## Обзор
LDUP v5 — это высокопроизводительная Python-библиотека для парсинга и анализа юридических документов. Система спроектирована как **базовый агент знаний** для будущей мультиагентной экосистемы, обеспечивающий импорт структурированных данных в **Temporal Graph RAG**.

### Ключевые архитектурные решения (SOTA 2026)
1.  **Recursive Language Models (RLM):** Иерархическое сжатие контекста в «кристаллы» (C³) — [arXiv:2512.24601](https://arxiv.org/abs/2512.24601).
2.  **Streaming WordML Ingestion:** Потоковая обработка XML (SAX-based) для работы с файлами 500МБ+ при RAM < 512МБ.
3.  **Hybrid Retrieval:** Трехуровневый поиск (FTS5 + BM25 + ONNX Embeddings) без GPU.
4.  **TCGR (Temporal Causal Graph Reasoner):** Граф изменений на базе рекурсивных CTE-запросов SQLite с защитой от глубокой рекурсии.

## Документация

| Файл | Описание |
| :--- | :--- |
| [requirements.md](requirements.md) | Функциональные требования и лимиты. |
| [design.md](design.md) | Описание паттернов (RLM, TCGR, HCO). |
| [api.md](api.md) | Программный интерфейс (Core Library API). |
| [components.md](components.md) | Модульная структура системы. |
| [performance.md](performance.md) | Оптимизация под CPU и параллелизм. |
| [reliability.md](reliability.md) | Rate-limiting, Fallbacks и Safety Rails. |
| [evaluation.md](evaluation.md) | Оценка архитектуры (9.0/10). |

## Технологический стек
*   **Runtime:** Python 3.13 + uv.
*   **Logic:** RLM-Toolkit v2.1.
*   **Storage:** SQLite (FTS5, JSON1, WAL mode).
*   **Inference:** FastEmbed (ONNX) + LiteLLM (для fallback провайдеров).