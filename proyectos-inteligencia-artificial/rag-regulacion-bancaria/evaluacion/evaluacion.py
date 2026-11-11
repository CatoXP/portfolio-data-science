import json
import sys
from pathlib import Path

# El buscador vive en la carpeta backend; se agrega a las rutas donde
# Python busca módulos para poder importarlo desde aquí.
RAIZ = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ / "backend"))

from buscador import Buscador  # noqa: E402

PREGUNTAS = Path(__file__).resolve().parent / "preguntas.json"

# Cuántos resultados se revisan por pregunta.
K = 5


def evaluar():
    """
    Corre todas las preguntas de prueba e imprime el resultado.

    Para cada pregunta busca en qué posición aparece el primer artículo
    esperado. Al final imprime Recall@K y MRR.
    """
    casos = json.loads(PREGUNTAS.read_text(encoding="utf-8"))
    buscador = Buscador()

    aciertos = 0
    suma_rr = 0.0

    for caso in casos:
        resultados = buscador.buscar(caso["pregunta"], k=K)
        encontrados = [r["articulo"] for r in resultados]

        # Posición (empezando en 1) del primer artículo esperado; None si
        # ninguno apareció entre los K resultados.
        posicion = next(
            (i + 1 for i, art in enumerate(encontrados) if art in caso["articulos"]),
            None,
        )

        if posicion:
            aciertos += 1
            suma_rr += 1 / posicion
            marca = f"OK   posición {posicion}"
        else:
            marca = "FALLA"

        print(f"{marca:15s} esperado {caso['articulos']}  |  {caso['pregunta']}")

    total = len(casos)
    print("-" * 60)
    print(f"Preguntas: {total}")
    print(f"Recall@{K}: {aciertos / total:.0%}")
    print(f"MRR: {suma_rr / total:.2f}")


if __name__ == "__main__":
    evaluar()