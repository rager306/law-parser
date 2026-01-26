import sys
import os
from pathlib import Path
from lxml import etree
from loguru import logger

# Добавляем rlm-toolkit в путь
sys.path.append("/root/law-parser/research/AISecurity/repo/rlm-toolkit")

from rlm_toolkit.core.engine import RLM, RLMConfig
from rlm_toolkit.testing.mocks import MockProvider
from rlm_toolkit.memory_bridge.v2.hierarchical import HierarchicalMemoryStore, MemoryLevel

# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")

XML_PATH = "doc_domain_44fz/cons/44-FZ/44-FZ-2026.xml"
W_NS = "{http://schemas.microsoft.com/office/word/2003/wordml}"

def extract_articles_stream(xml_path):
    """Потоковый парсинг WordML для извлечения текстов статей."""
    context = etree.iterparse(xml_path, events=('end',), tag=f'{W_NS}p')
    current_article = []
    article_title = ""
    
    for event, elem in context:
        # Извлекаем весь текст из абзаца
        text = "".join(elem.itertext()).strip()
        
        # Простая эвристика поиска заголовка статьи
        if text.startswith("Статья "):
            if article_title:
                yield article_title, "\n".join(current_article)
            article_title = text
            current_article = []
        else:
            current_article.append(text)
            
        # Очищаем элемент для экономии памяти
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

def simulate_rlm_workflow():
    logger.info("Запуск архитектурного прототипа LDUP v4 + RLM")
    
    # 1. Инициализация RLM с Mock-провайдером (для CPU-валидации логики)
    mock_llm = MockProvider(responses=["FINAL(Связь обнаружена: Статья 34 изменена Статьей 112)"])
    rlm = RLM(root=mock_llm, config=RLMConfig(sandbox=True))
    
    # 2. Инициализация хранилища фактов (SQLite)
    db_path = Path(".rlm_test/memory_bridge_v2.db")
    if db_path.exists(): db_path.unlink()
    db_path.parent.mkdir(exist_ok=True)
    store = HierarchicalMemoryStore(db_path=db_path)
    
    logger.info("Обработка XML в потоковом режиме...")
    
    count = 0
    # 3. Имитация процесса индексации (первые 5 статей для теста)
    for title, content in extract_articles_stream(XML_PATH):
        count += 1
        # Добавляем факт в RLM-хранилище
        store.add_fact(
            content=f"{title}\n{content[:200]}...", # Сохраняем только начало для теста
            level=MemoryLevel.L1_DOMAIN,
            domain="44-fz-structure",
            source="xml_parser"
        )
        if count >= 5: break
        
    logger.info(f"Индексация завершена. Сохранено {count} статей в SQLite.")
    
    # 4. Валидация идеи Causal Chain (Причинно-следственной связи)
    logger.info("Валидация хранилища фактов...")
    all_facts = store.get_all_facts()
    
    if all_facts:
        logger.info(f"RLM сохранил факты. Всего записей: {len(all_facts)}")
        for fact in all_facts:
            if "Статья 1" in fact.content:
                logger.info(f"Найден целевой факт: {fact.content[:50]}...")
        
        logger.info("Идея TCGR: Данные успешно структурированы и сохранены в SQLite. Семантический поиск может быть добавлен через EmbeddingRetriever.")
    else:
        logger.error("Факты не найдены в хранилище!")

if __name__ == "__main__":
    if not Path(XML_PATH).exists():
        logger.error(f"Файл {XML_PATH} не найден!")
    else:
        simulate_rlm_workflow()
