"""
ingesta.py - Modulo de ingesta del proyecto RAG de regulación bancaria.

Autor: Brandon Uriel Garcia Sanchez
Copyright (c) 2026 Brandon Uriel García Sánchez. Todos los derechos reservados.
Github: https://github.com/CatoXP
Linkedin: https://www.linkedin.com/in/brandon-uriel-garcia-sanchez-9ab77b320/

¿Qué es la ingesta? 
Es la primera parte de la etapa de un sistema RAG (Retrieval-Augmented Generation).
Consiste en tomar los documentos fuente (leyes en PDF ) y dejarlos listos para que 
el sistema pueda buscar en ellos.

¿Qué hace este modulo?
1. Extrae el texto de cada pagina del PDF.
2. Limpia el texto: quita encabezados de página y notas de reforma.
3. Elimina los articulos transitorios, que no son contenido consultable.
4. parte el texto en articulos, guardando el numero de cada uno.
5. Divide los articulos largos en chunks que quepan en el modelo de embeddings.

Fuentes de datos: 
    Ley de Instituciones de Crédito, texto vigente publicado por la
    Cámara de Diputados (documento público). https://www.diputados.gob.mx/LeyesBiblio/ref/lic.htm

"""

import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
import pymupdf 
import re 


# ------------------------------------------------
# Configuración
# ------------------------------------------------

# Carpeta donde viven los PDFs. Se calcula a partir de la ubicación de este
# archivo para que el proyecto funcone en cualquier computadora
DATOS = Path(__file__).resolve().parent.parent / "datos"

# Tamaño máximo de un chunk, en caracteres. El modelo de embeddings solo
# lee unos 512 tokens (aprox. 1,500 a 2,000 caracteres) e ignora lo que sobra.
# Sin este límite, de un artículo largo solo se indexaría el inicio.
MAX_CARACTERES = 1500

# Carpeta donde ChromaDB guarda la base vectorial en disco.
BASE_VECTORIAL = DATOS.parent / "base_vectorial"

# Modelo pre-entrenado que convierte texto en embeddings. Es multilingüe
# ( entiende español ) y ligero, asi corre bien en CPU

MODELO_EMBEDDINGS = "intfloat/multilingual-e5-base"

# Nombre de la colección (el equivalentea una tabla) dentro de ChromaDB.
COLECCION = "regulacion_bancaria_e5_base"

# ---------------------------------------------------------------------------
# Patrones de texto (expresiones regulares)
# --------------------------------------------------------------------------

# Ultima linea del encabezado de cada pagina, por ejemplo: "6 de 321".
FIN_ENCABEZADO = re.compile(r"\d+ de \d+\s*\n")

# Notas de reforma, por ejemplo: "Articulo adicionado DOF 01-02-2008"
NOTA_REFORMA = re.compile(r"^[^\n]*DOF \d{2}-\d{2}-\d{4}[^\n]*\n", re.MULTILINE)

# Inicio de un articulo, por ejemplo "Articulo 7 Bis 3.-".
#  El grupo entre parentesis captura el numero ("7 Bis 3").                     
PATRON_ARTICULO = re.compile(r"^[ \t]*Artículo ([^\n]{1,25}?)\.-", re.MULTILINE)

# Titulo de la seleccion de transitorio: una linea que solo dice "Transitorios".
INICIO_TRANSITORIOS = re.compile(r"^\s*TRANSITORIOS?\s*$", re.MULTILINE | re.IGNORECASE)


# ---------------------------------------------------------------------------
# Glosario del dominio
# ---------------------------------------------------------------------------

# La ley cita delitos por su número de artículo en el Código Penal Federal,
# sin nombrarlos. Cada entrada une un patrón de texto con una nota que
# explica el concepto, para que la búsqueda por significado lo encuentre.
GLOSARIO = [
    (
        re.compile(r"400\s+Bis"),
        "Nota: el artículo 400 Bis del Código Penal Federal tipifica las "
        "operaciones con recursos de procedencia ilícita, conocidas como "
        "lavado de dinero.",
    ),
    (
        re.compile(r"1(?:39|48)\s[^.]{0,40}?Código\s+Penal\s+Federal"),
        "Nota: los artículos 139 y 148 Bis del Código Penal Federal "
        "tipifican el terrorismo y el terrorismo internacional.",
    ),
]

# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------

def extraer_texto(ruta_pdf):
    """
    Lee un PDF y devuelve su texto, página por página.

    Parámetros:
        ruta_pdf: ruta al archivo PDF.

    Devuelve:
        Lista de strings; cada elemento es el texto de una página.
    """
    doc = pymupdf.open(ruta_pdf)  
    return [pagina.get_text() for pagina in doc]




def limpiar_pagina(texto):
    """
    Quita de una página lo que no es contenido de la ley.

    Elimina dos cosas:
        - El encabezado que se repite en cada página (título de la ley,
          Cámara de Diputados, fecha de última reforma, "N de 321").
        - Las notas de reforma ("Párrafo reformado DOF dd-mm-aaaa").

    Parámetros:
        texto: texto crudo de una página.

    Devuelve:
        El texto de la página ya limpio.
    """
    # El encabezado siempre está al inicio, por eso solo se busca
    # en los primeros 400 caracteres.
    encabezado = FIN_ENCABEZADO.search(texto[:400])
    if encabezado:
      texto = texto[encabezado.end():]
    return NOTA_REFORMA.sub("", texto)




def quitar_transitorios(texto):
    """
    Corta el texto donde empieza la sección de artículos transitorios.

    Los transitorios son reglas temporales de cada reforma (por ejemplo,
    cuándo entra en vigor). No describen obligaciones de los bancos y sus
    nombres se repiten ("Único", "Primero"), así que no sirven para citar.

    Parámetros:
        texto: texto completo de la ley, ya limpio.

    Devuelve:
        El texto hasta antes del primer título "TRANSITORIOS".
    """
    corte = INICIO_TRANSITORIOS.search(texto)
    if corte:
        return texto[:corte.start()]
    return texto





def partir_en_articulos(texto):
    """
    Divide el texto de la ley en artículos.

    Cada artículo va desde su encabezado ("Artículo N.-") hasta donde
    empieza el siguiente. Se conserva el número para poder citarlo.

    Parámetros:
        texto: texto completo de la ley, limpio y sin transitorios.

    Devuelve:
        Lista de diccionarios con las llaves:
            "articulo": número del artículo, por ejemplo "7 Bis 3".
            "texto": contenido completo del artículo.
    """

    marcas = list(PATRON_ARTICULO.finditer(texto))
    articulos = []
    for i, marca in enumerate(marcas):
        # Red de seguridad: se descarta lo que no empiece con un dígito
        # (transitorios como "Único" o "Primero").
        if not marca.group(1)[0].isdigit():
            continue

        # El articulo termina donde empieza el siguiente; el ultimo
        # llega hasta el final del texto
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        articulos.append({
            "articulo": marca.group(1),
            "texto": texto[marca.start():fin].strip(),
        })
    return articulos






def partir_en_chunks(articulos):
    """
    Divide los artículos largos en chunks que quepan en el modelo.

    Los artículos cortos quedan como un solo chunk. Los largos se parten
    entre párrafos (nunca a media idea) en grupos de máximo MAX_CARACTERES.
    A partir de la segunda parte se antepone "Artículo N (continuación)"
    para que cada chunk conserve de qué artículo viene.

    Parámetros:
        articulos: lista devuelta por partir_en_articulos().

    Devuelve:
        Lista de diccionarios con las llaves:
            "id": identificador único del chunk, por ejemplo "122-3".
            "articulo": número del artículo al que pertenece.
            "texto": contenido del chunk.
    """


    chunks = []
    for art in articulos:
        # Los parrafos estan separados por lineas en banco
        parrafos = [p.strip() for p in re.split(r"\n\s*\n", art["texto"]) if p.strip()]

        # Se acumulan parrafos hasta que el siguiente ya no cabe.
        grupos = []
        actual = ""
        for p in parrafos:
            if actual and len(actual) + len(p) > MAX_CARACTERES:
                grupos.append(actual)
                actual = ""
            actual = (actual + "\n" + p).strip()
        if actual:
            grupos.append(actual)


        # Cada grupo se convierte en un chunk con su ID y su articulo
        for n, grupo in enumerate(grupos, start=1):
            if n > 1:
                grupo = f"Artículo {art['articulo']} (continuación)\n" + grupo
            chunks.append({
                "id": f"{art['articulo']}-{n}",
                "articulo": art["articulo"],
                "texto": grupo,
            })
    return chunks



def enriquecer(chunks):
    """
    Agrega a cada chunk las notas del glosario que le correspondan.

    Las notas explican conceptos que la ley solo cita por número de
    artículo. Se guardan aparte, en la llave "notas", para usarlas en
    la búsqueda sin modificar el texto original de la ley.

    Parámetros:
        chunks: lista devuelta por partir_en_chunks().

    Devuelve:
        La misma lista; cada chunk con la llave nueva "notas"
        (cadena vacía si no le aplica ninguna).
    """
    for c in chunks:
        notas = [nota for patron, nota in GLOSARIO if patron.search(c["texto"])]
        c["notas"] = " ".join(notas)
    return chunks


def indexar(chunks, fuente):
    """
    Convierte los chunks en embeddings y los guarda en la base vectorial.

    El embedding se calcula con el texto de la ley más sus notas del
    glosario, para mejorar la búsqueda. El texto que se guarda como
    documento es solo el original de la ley, sin modificar.

    Parámetros:
        chunks: lista devuelta por enriquecer().
        fuente: nombre del documento de origen, para poder citarlo.

    Devuelve:
        Número total de chunks guardados en la colección.
    """
    # Carga el modelo pre-entrenado (la primera vez lo descarga).
    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    # Los modelos E5 piden el prefijo "passage: " en los documentos.
    # Se indexa el texto de la ley más sus notas del glosario.
    textos = ["passage: " + c["texto"] + "\n" + c["notas"] for c in chunks]
    embeddings = modelo.encode(
        textos, normalize_embeddings=True, show_progress_bar=True
    )

    # Abre (o crea) la base en disco y la colección con distancia coseno.
    cliente = chromadb.PersistentClient(path=str(BASE_VECTORIAL))
    coleccion = cliente.get_or_create_collection(
        name=COLECCION, metadata={"hnsw:space": "cosine"}
    )

    # upsert = inserta si no existe, actualiza si ya existe.
    coleccion.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings.tolist(),
        documents=[c["texto"] for c in chunks],
        metadatas=[
            {"articulo": c["articulo"], "fuente": fuente, "notas": c["notas"]}
            for c in chunks
        ],
    )
    return coleccion.count()


# ---------------------------------------------------------------------------
# Prueba: solo corre al ejecutar este archivo directamente
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for pdf in DATOS.glob("*.pdf"):
        paginas = extraer_texto(pdf)
        texto = "\n".join(limpiar_pagina(p) for p in paginas)
        texto = quitar_transitorios(texto)
        articulos = partir_en_articulos(texto)
        chunks = partir_en_chunks(articulos)
        chunks = enriquecer(chunks)
        con_notas = [c["id"] for c in chunks if c["notas"]]

        print("Archivo:", pdf.name)
        print("Artículos:", len(articulos))
        print("Chunks:", len(chunks))
        print("Chunks enriquecidos con el glosario:", con_notas)
        print("Generando embeddings...")

        total = indexar(chunks, fuente=pdf.stem)
        print("Chunks guardados en la base vectorial:", total)