"""
buscador.py - Modulo de busqueda del proecto RAG de regulació
Autor: Brandon Uriel Garcia Sanchez
Copyright (c) 2026 Brandon Uriel García Sánchez. Todos los derechos reservados.
Github: https://github.com/CatoXP
Linkedin: https://www.linkedin.com/in/brandon-uriel-garcia-sanchez-9ab77b320/

¿Que es la busqueda (retrieval)?
Es la "R" de RAG. Dada una pregunta en lenguaje natural, encuentra los fragmentos de la ley que
más se parecen en significado, aunque no compartan las mismas palabras.

¿Que hace este modulo?
1. Convierte la pregunta en un embedding con el mismo modelo que se usó para la ingesta
2. Consulta la base vectorial para traer los chunks más parecidos.
3. Devuelve esos chunks con su articulo, su fuente y su similitud

El unico requisito para ejecutar este .py es ejecutar antes la ingesta.py para que exista nuestra
base de datos vectorial. :)
"""
import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer

from ingesta import BASE_VECTORIAL, COLECCION, MODELO_EMBEDDINGS

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

# Cuántos chunks se devuelven por pregunta.
TOP_K = 5

# Cuántos candidatos trae la búsqueda vectorial antes de reordenar.
# La evaluación mostró que el artículo correcto casi siempre está entre
# los primeros 20, aunque no entre los primeros 5.
CANDIDATOS = 20

# Modelo que reordena los candidatos (cross-encoder multilingüe).
MODELO_REORDENADOR = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


class Buscador:
    """
    Buscador semántico en dos etapas sobre la base vectorial.

    Etapa 1 (búsqueda): un modelo de embeddings trae rápido los candidatos
        más parecidos a la pregunta.
    Etapa 2 (reordenamiento): un cross-encoder lee la pregunta junto con
        cada candidato y los reordena con más precisión.

    Los modelos y la colección se cargan una sola vez al crear el objeto.
    """

    def __init__(self):
        """Carga los dos modelos y abre la colección de ChromaDB."""
        self.modelo = SentenceTransformer(MODELO_EMBEDDINGS)
        self.reordenador = CrossEncoder(MODELO_REORDENADOR)
        cliente = chromadb.PersistentClient(path=str(BASE_VECTORIAL))
        self.coleccion = cliente.get_collection(COLECCION)

    def buscar(self, pregunta, k=TOP_K, reordenar=True):
        """
        Busca los chunks más relevantes para una pregunta.

        Parámetros:
            pregunta: texto de la pregunta en lenguaje natural.
            k: cuántos resultados devolver.
            reordenar: si es True, aplica la segunda etapa (cross-encoder).
                Con False devuelve el orden de la búsqueda vectorial.

        Devuelve:
            Lista de diccionarios ordenada de más a menos relevante:
                "articulo": número del artículo.
                "fuente": documento de origen.
                "notas": aclaraciones del glosario (vacío si no tiene).
                "texto": contenido del chunk.
                "similitud": similitud coseno con la pregunta (0 a 1).
                "puntaje": calificación del cross-encoder (solo si se
                    reordenó; entre más alto, más relevante).
        """
        # Etapa 1: búsqueda vectorial.
        # Los modelos E5 piden el prefijo "query: " en las preguntas.
        embedding = self.modelo.encode(
            "query: " + pregunta, normalize_embeddings=True
        )
        cantidad = max(CANDIDATOS, k) if reordenar else k
        respuesta = self.coleccion.query(
            query_embeddings=[embedding.tolist()], n_results=cantidad
        )

        # Chroma devuelve una lista por cada pregunta; como solo se
        # mandó una, se toma la posición [0] de cada campo.
        resultados = []
        for texto, meta, distancia in zip(
            respuesta["documents"][0],
            respuesta["metadatas"][0],
            respuesta["distances"][0],
        ):
            resultados.append({
                "articulo": meta["articulo"],
                "fuente": meta["fuente"],
                "notas": meta.get("notas", ""),
                "texto": texto,
                # Chroma devuelve distancia coseno; similitud = 1 - distancia.
                "similitud": 1 - distancia,
            })

        if not reordenar:
            return resultados[:k]

        # Etapa 2: el cross-encoder califica cada pareja (pregunta, chunk).
        # Se incluyen las notas del glosario para que también las lea.
        parejas = [(pregunta, r["texto"] + "\n" + r["notas"]) for r in resultados]
        puntajes = self.reordenador.predict(parejas)
        for r, puntaje in zip(resultados, puntajes):
            r["puntaje"] = float(puntaje)

        resultados.sort(key=lambda r: r["puntaje"], reverse=True)
        return resultados[:k]


# ---------------------------------------------------------------------------
# Prueba: buscador interactivo en la terminal
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    buscador = Buscador()
    while True:
        pregunta = input("\nPregunta (Enter para salir): ").strip()
        if not pregunta:
            break
        for r in buscador.buscar(pregunta):
            print(f"\n[{r['puntaje']:.2f}] Artículo {r['articulo']}")
            print(r["texto"][:300])