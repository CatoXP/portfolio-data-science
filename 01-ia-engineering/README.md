# 01 · IA Engineering

LLMs, RAG y modelos pre-entrenados convertidos en herramientas que funcionan.

| Proyecto | Qué resuelve | Resultado | Stack |
|---|---|---|---|
| [⚖️ Asistente de Regulación Bancaria (RAG + LLM local)](rag-regulacion-bancaria) | Responde en español preguntas sobre la Ley de Instituciones de Crédito citando el artículo; todo corre en local | **Recall@20 91%** · Recall@5 73% · MRR 0.61 en 22 preguntas | sentence-transformers · ChromaDB · Ollama (Gemma 3) · Gradio |
| [🎬 Traductor de subtítulos en vivo](traductor-subtitulos-live) | OCR + traducción offline inglés → español sobre cualquier video · [slides](traductor-subtitulos-live/slides/traductor_deck.pdf) | ~226 ms por línea · OCR 11x más rápido | RapidOCR · Argos Translate · Tkinter |

---
<sub>[← Volver al portafolio](../README.md)</sub>
