"""
app.py - Interfaz web del proyecto RAG de regulación bancaria.

Autor: Brandon Uriel Garcia Sanchez
Copyright (c) 2026 Brandon Uriel García Sánchez. Todos los derechos reservados.
Github: https://github.com/CatoXP
Linkedin: https://www.linkedin.com/in/brandon-uriel-garcia-sanchez-9ab77b320/

¿Qué hace este módulo?
    Levanta una página web local con un chat. Cada pregunta pasa por el
    sistema RAG completo: se buscan los artículos relevantes, un LLM
    redacta la respuesta y se muestran los artículos consultados.

Requisitos:
    - Haber corrido ingesta.py para que exista la base vectorial.
    - Tener Ollama instalado y el modelo descargado.

Uso:
    python backend/app.py
    Después abrir en el navegador la dirección que aparece en la terminal.
"""

import gradio as gr

from buscador import Buscador
from generador import responder

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

TITULO = "Asistente de Regulación Bancaria"

DESCRIPCION = (
    "Haz una pregunta sobre la Ley de Instituciones de Crédito de México. "
    "Las respuestas se generan únicamente a partir del texto de la ley y "
    "citan el artículo correspondiente. No constituye asesoría legal."
)

EJEMPLOS = [
    "¿Qué operaciones puede realizar un banco?",
    "¿Qué deben hacer los bancos para prevenir el lavado de dinero?",
    "¿Un banco puede dar información de mis cuentas a cualquiera?",
]

# El buscador se carga una sola vez al arrancar la aplicación, no en
# cada pregunta, porque cargar el modelo de embeddings tarda unos segundos.
buscador = Buscador()


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def contestar(mensaje, historial):
    """
    Atiende un mensaje del chat y devuelve la respuesta con sus fuentes.

    Parámetros:
        mensaje: la pregunta que escribió el usuario.
        historial: mensajes anteriores del chat. Gradio lo envía siempre,
            pero no se usa: cada pregunta se responde de forma independiente.

    Devuelve:
        Texto en formato Markdown con la respuesta y, al final, la lista
        de artículos que se consultaron.
    """
    respuesta, resultados = responder(mensaje, buscador)

    # Lista de artículos sin repetir, respetando el orden de relevancia.
    articulos = []
    for r in resultados:
        if r["articulo"] not in articulos:
            articulos.append(r["articulo"])
    fuentes = ", ".join(f"Art. {a}" for a in articulos)

    return f"{respuesta}\n\n---\n**Artículos consultados:** {fuentes}"


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------

demo = gr.ChatInterface(
    fn=contestar,
    title=TITULO,
    description=DESCRIPCION,
    examples=EJEMPLOS,
)

if __name__ == "__main__":
    demo.launch()