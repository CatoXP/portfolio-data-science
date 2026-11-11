"""
verificar.py - Revisión manual del conjunto de preguntas de prueba.

Autor: Brandon Uriel Garcia Sanchez
Copyright (c) 2026 Brandon Uriel García Sánchez. Todos los derechos reservados.

¿Qué hace este módulo?
    Para cada pregunta de preguntas.json muestra el inicio de los artículos
    esperados, para confirmar a mano que de verdad contestan la pregunta.
    Una evaluación solo es confiable si sus respuestas esperadas lo son.

Uso:
    python evaluacion/verificar.py
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ / "backend"))

from buscador import Buscador  # noqa: E402

PREGUNTAS = Path(__file__).resolve().parent / "preguntas.json"

casos = json.loads(PREGUNTAS.read_text(encoding="utf-8"))
coleccion = Buscador().coleccion

for numero, caso in enumerate(casos, start=1):
    print("=" * 70)
    print(f"{numero}. {caso['pregunta']}")
    for articulo in caso["articulos"]:
        # El primer chunk de cada artículo tiene el id "<artículo>-1".
        encontrado = coleccion.get(ids=[f"{articulo}-1"])
        if encontrado["documents"]:
            print(f"\n   {encontrado['documents'][0][:350]}")
        else:
            print(f"\n   *** El artículo {articulo} NO existe en la base ***")