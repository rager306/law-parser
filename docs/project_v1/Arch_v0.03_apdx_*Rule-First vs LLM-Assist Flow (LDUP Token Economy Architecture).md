Отлично. Ниже — диаграмма, которая визуализирует **архитектурную логику LDUP**:
где именно участвуют детерминированные модули DSPy, где — активируется LLM-ассистент, и как SRC-петля постепенно **снижает долю LLM**, превращая её в новый формализованный шаг.

---

## 🧩 **Rule-First vs LLM-Assist Flow (LDUP Token Economy Architecture)**

```mermaid
graph TD
    %% INPUT
    A[📥 Input Document<br>(XML / DOCX / HTML / RTF)] --> B[⚙️ Preprocessor / Normalizer]

    %% STRUCTURAL LAYER
    subgraph S1[🧱 Rule-Based Structural Layer]
        B --> C1[GEPA 3.5 – Structural Parser<br>• chapters • articles • clauses]
        C1 --> C2[Cross-Ref Resolver + MetaLex ID]
    end

    %% SEMANTIC / MORPHO LAYER
    subgraph S2[🧩 Morpho-Semantic & Temporal Layer]
        C2 --> D1[SIMBA 2.2 – Morpho-Semantic Analyzer<br>• obligations • prohibitions • rights]
        D1 --> D2[MiPROv2 + Temporal Memory v3<br>• effectiveFrom / To • validity intervals]
        D2 --> D3[TCGR Plugin – Causal Linking<br>• amendments • repeals]
    end

    %% DECISION POINT
    D3 --> E{❓ Is structure/semantics fully resolved?}

    %% RULE BRANCH
    E -- ✅ Yes --> F1[🟢 Rule-Path<br>Export via Akoma Ntoso / LegalRuleML]
    F1 --> F2[Store in FalkorDB + Graffiti Temporal Layer]

    %% LLM BRANCH
    E -- ⚠️ No --> G1[🟡 LLM-Assist Module<br>• non-standard clauses<br>• ambiguous syntax]
    G1 --> G2[SRC v2 Feedback Controller<br>• auto-labeling • rule refinement]
    G2 --> G3[HCO Cache Update<br>• embed semantic patterns]
    G3 --> D1

    %% EXPORT
    F2 --> H[🧾 Outputs:<br>AKN / LegalRuleML / NormML / Graph Triples]

    %% LOOP LEGEND
    style G1 fill:#fff5cc,stroke:#e6a700,stroke-width:2px
    style S1 fill:#f3f3f3,stroke:#888,stroke-width:1px
    style S2 fill:#f3f3f3,stroke:#888,stroke-width:1px
    style F1 fill:#d3f9d8,stroke:#2e8b57,stroke-width:2px
    style G2 fill:#d1e0ff,stroke:#0044cc,stroke-width:1px
    style G3 fill:#d1e0ff,stroke:#0044cc,stroke-width:1px
```

---

## 🧠 Объяснение потоков

| Зона                       | Тип логики                         | Модули                            | Token-затраты |
| -------------------------- | ---------------------------------- | --------------------------------- | ------------- |
| **S1 — Structural Layer**  | 💡 Детерминированная               | GEPA 3.5, Cross-Ref Resolver      | ≈ 0           |
| **S2 — Semantic/Temporal** | 💡 Алгоритмическая + символическая | SIMBA 2.2, MiPROv2, TCGR          | ≈ 0–5 %       |
| **Decision Node E**        | ⚙️ Контроль полноты анализа        | GEPA + SIMBA результаты → условие | —             |
| **LLM-Assist Path**        | 🤖 Неформализуемые случаи          | LLM-Assist Node                   | до 20 %       |
| **SRC Loop**               | 🔁 Самообучение                    | SRC v2, HCO                       | −Δ LLM доля   |
| **Export Layer**           | 📤 Стандарты                       | Akoma Ntoso, LegalRuleML, NormML  | 0             |

---

## 📉 Как работает экономия токенов

1️⃣ На первом цикле LLM участвует в ~30 % случаев.
2️⃣ SRC формирует JSON-feedback и обновляет YAML-правила.
3️⃣ При следующем запуске DSPy-модули (GEPA / SIMBA / MiPROv2) берут эти правила →
доля LLM падает до < 20 %.
4️⃣ HCO-Cache хранит векторные шаблоны, что ещё больше снижает обращения.

---

## 🔁 Итоговая логика экономии

```text
Rule-based first  →  LLM only when necessary  →  Learn from feedback  →  Reduce LLM dependency
```

---

