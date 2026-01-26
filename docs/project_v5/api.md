# Core API LDUP v5

## 1. Основные методы (Python Library)

Система проектируется как библиотека, предоставляющая интерфейс для интеграции в любые рабочие процессы.

### 1.1. `parser.ingest(path: str, version: str) -> str`
Запускает потоковый парсинг файла и возвращает `session_id` в RLM.
*   Использует `lxml.etree.iterparse`.
*   Наполняет `HierarchicalMemoryStore`.

### 1.2. `parser.query(text: str, top_k: int = 5) -> List[HierarchicalFact]`
Выполняет гибридный поиск (FTS5 + BM25 + Vectors) по базе кристаллов.

### 1.3. `parser.get_changes(article_id: str, max_depth: int = 5) -> Graph`
Возвращает цепочку изменений для статьи, используя TCGR алгоритм.

## 2. Модели данных (Pydantic)

```python
class HCOEntry(BaseModel):
    hash_v1: str  # sha256
    cache_version: int = 1
    content_crystal: str
    modality: str
    confidence: float

class CausalLink(BaseModel):
    source_id: str
    target_id: str
    link_type: str = "amends" # или "repeals", "enforces"
```