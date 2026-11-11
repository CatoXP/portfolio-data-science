"""
generador.py - Modulo de generación del proyecto RAG de regulación bancaria.

Autor: Brandon Uriel Garcia Sanchez
Copyright (c) 2026 Brandon Uriel García Sánchez. Todos los derechos reservados.
Github: https://github.com/CatoXP
Linkedin: https://www.linkedin.com/in/brandon-uriel-garcia-sanchez-9ab77b320/

¿Qué es la generación? Es la "G" de RAG. TOma la pregunta del usuario y los fragmentos de ley
que encontró el buscador, y le pide a un modelo de lenguaje (LLM) que
redacte una respuesta basada unicamente en estos fragmentos.

¿Qué hace este modulo?
1. Piide el buscador los chunks más relevantes para la pregunta.
2. Arma el contexto: los chunks con su articulo y sus notas.
3. Envia instrucciones, contexto y preugnta a un LLM local (OLLAMA).
4. Devuelve la respuesta junto con las fuentes que se usaros.

Requisitos:
    - Haber corrido ingesta.py para que exista la base vectorial.
    - Tener Ollama instalado y el modelo descargado: ollama pull gemma3:4b

"""

import ollama
from buscador import Buscador


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

# Modelo de lenguaje que corre en local con Ollama.
MODELO_LLM = "gemma3:4b"

# Tamaño de la ventana de contexto, en tokens. Debe alcanzar para las
# instrucciones, los 5 chunks y la pregunta; si no, Ollama recorta el texto.
VENTANA_CONTEXTO = 8192

# Instrucciones fijas que definen cómo debe comportarse el modelo.
INSTRUCCIONES = """Eres un asistente especializado en regulación bancaria mexicana.

Responde la pregunta usando ÚNICAMENTE los fragmentos de ley que se te dan.

Reglas:
1. Cita el artículo que respalda cada afirmación, entre paréntesis.
   Ejemplo: (Artículo 46).
2. Si los fragmentos no contienen la respuesta, contesta exactamente:
   "No encontré esa información en los documentos consultados."
   No uses conocimiento propio ni inventes artículos.
3. Explica con tus propias palabras, en español claro y sencillo, como
   si se lo explicaras a alguien que no es abogado. No copies el texto
   de la ley palabra por palabra.
4. Sé breve: primero la respuesta directa y luego los puntos clave.
5. Las líneas que empiezan con "Nota:" son aclaraciones de apoyo;
   no forman parte del texto de la ley, pero puedes usarlas para
   explicar a qué se refiere un artículo."""


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def armar_contexto(resultados):
    """
    Convierte los resultados del buscador en un solo texto para el LLM.

    Cada fragmento se etiqueta con su artículo y su fuente, para que el
    modelo pueda citarlos. Si el chunk tiene notas del glosario, se agregan.

    Parámetros:
        resultados: lista devuelta por Buscador.buscar().

    Devuelve:
        Un string con todos los fragmentos, separados por líneas en blanco.
    """
    bloques = []
    for r in resultados:
        bloque = f"[Artículo {r['articulo']} - {r['fuente']}]\n{r['texto']}"
        if r["notas"]:
            bloque += "\n" + r["notas"]
        bloques.append(bloque)
    return "\n\n".join(bloques)


def responder(pregunta, buscador):
    """
    Responde una pregunta usando la ley como única fuente.

    Parámetros:
        pregunta: texto de la pregunta en lenguaje natural.
        buscador: instancia de Buscador ya cargada.

    Devuelve:
        Una tupla (respuesta, resultados):
            respuesta: texto redactado por el LLM.
            resultados: los chunks que se le dieron como contexto.
    """
    resultados = buscador.buscar(pregunta)
    contexto = armar_contexto(resultados)

    salida = ollama.chat(
        model=MODELO_LLM,
        messages=[
            {"role": "system", "content": INSTRUCCIONES},
            {
                "role": "user",
                "content": f"Fragmentos de la ley:\n\n{contexto}\n\nPregunta: {pregunta}",
            },
        ],
        # temperature 0 = respuestas consistentes, sin creatividad.
        options={"temperature": 0, "num_ctx": VENTANA_CONTEXTO},
    )
    return salida["message"]["content"], resultados


# ---------------------------------------------------------------------------
# Prueba: asistente interactivo en la terminal
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    buscador = Buscador()
    while True:
        pregunta = input("\nPregunta (Enter para salir): ").strip()
        if not pregunta:
            break
        respuesta, resultados = responder(pregunta, buscador)
        print("\n" + respuesta)
        print("\nFuentes consultadas:", [r["articulo"] for r in resultados])