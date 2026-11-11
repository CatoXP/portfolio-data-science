"""Lectura de subtitulos en pantalla mediante OCR.

Dos cosas de aqui son las que hacen la app viable:

1. La configuracion del motor. RapidOCR viene con `limit_type: min` y
   `limit_side_len: 736`, o sea que AMPLIA la imagen hasta que su lado corto
   mida 736 px. Una franja de subtitulos es ancha y bajita (p. ej. 1100x190),
   asi que la ampliaba ~4x antes de detectar: 2.8 s por frame. Con
   `limit_type: max` baja a ~250 ms. Ademas se apaga el clasificador de
   rotacion (`use_cls`), que solo sirve para texto al reves.

2. El filtro anti-repeticion. Un subtitulo dura ~3 s en pantalla, o sea ~9
   capturas del MISMO texto. Sin filtro traduciriamos nueve veces la misma
   frase.
"""

from __future__ import annotations

import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import numpy as np

_NO_ALFANUM = re.compile(r"[^a-z0-9 ]+")
_ESPACIOS = re.compile(r"\s+")

# Lado maximo con el que trabaja el detector. 960 fue el punto optimo medido
# en CPU: mas grande cuesta tiempo, mas chico pierde precision.
LADO_DETECCION = 960

_RUTA_CFG = Path(__file__).resolve().parent / "ocr_config.yaml"


def _hilos_por_defecto() -> int:
    """6 hilos rinden mejor que 12: el hyperthreading se estorba a si mismo."""
    return max(1, min(6, (os.cpu_count() or 4)))


def _generar_config(hilos: int) -> Path:
    """Escribe un config.yaml propio a partir del que trae RapidOCR.

    Se usa `config_path` en vez de los kwargs del constructor porque el
    mecanismo de kwargs de rapidocr-onnxruntime 1.4.x descarta parte de los
    valores por un bug en `UpdateParameters.__call__`.
    """
    import rapidocr_onnxruntime
    import yaml

    base = Path(rapidocr_onnxruntime.__file__).parent / "config.yaml"
    cfg = yaml.safe_load(base.read_text(encoding="utf-8"))

    cfg["Global"]["use_cls"] = False  # los subtitulos nunca vienen al reves
    cfg["Det"]["limit_type"] = "max"  # <- la correccion importante
    cfg["Det"]["limit_side_len"] = LADO_DETECCION
    for modulo in ("Global", "Det", "Cls", "Rec"):
        cfg[modulo]["intra_op_num_threads"] = hilos
        cfg[modulo]["inter_op_num_threads"] = 1

    _RUTA_CFG.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    return _RUTA_CFG


def normalizar(texto: str) -> str:
    """Version canonica para comparar dos lecturas del OCR."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = _NO_ALFANUM.sub(" ", texto)
    return _ESPACIOS.sub(" ", texto).strip()


def preprocesar(frame: np.ndarray) -> np.ndarray:
    """Lleva la region al ancho de trabajo del detector.

    Solo se amplia cuando la zona es chica (stream en ventana pequena); si ya
    es grande se deja igual, porque el detector la reducira de todos modos.
    Se mantiene en color: binarizar empeora el resultado cuando el fondo del
    video es claro.
    """
    alto, ancho = frame.shape[:2]
    if ancho <= 0:
        return frame
    escala = LADO_DETECCION / float(max(ancho, alto))
    if escala <= 1.0:
        return frame
    escala = min(escala, 3.0)
    return cv2.resize(
        frame, None, fx=escala, fy=escala, interpolation=cv2.INTER_CUBIC
    )


class LectorSubtitulos:
    """Convierte frames en lineas de texto NUEVAS (ya sin repeticiones)."""

    def __init__(
        self,
        umbral_confianza: float = 0.5,
        umbral_similitud: float = 0.90,
        hilos: int | None = None,
    ):
        from rapidocr_onnxruntime import RapidOCR

        self._motor = RapidOCR(
            config_path=str(_generar_config(hilos or _hilos_por_defecto()))
        )
        self.umbral_confianza = umbral_confianza
        self.umbral_similitud = umbral_similitud
        self._ultima_norm = ""

    def _ordenar_y_unir(self, detecciones) -> str:
        """Une las cajas detectadas en una sola linea, en orden de lectura."""
        utiles = []
        for caja, texto, score in detecciones:
            if float(score) < self.umbral_confianza:
                continue
            texto = (texto or "").strip()
            if not texto:
                continue
            puntos = np.asarray(caja, dtype=float)
            arriba = float(puntos[:, 1].min())
            izquierda = float(puntos[:, 0].min())
            altura = float(puntos[:, 1].max()) - arriba
            utiles.append((arriba, izquierda, altura, texto))

        if not utiles:
            return ""

        utiles.sort(key=lambda it: (it[0], it[1]))
        # Dos cajas van en el mismo renglon si su Y difiere menos de media
        # altura de linea.
        tolerancia = max(8.0, np.median([it[2] for it in utiles]) * 0.6)

        renglones: list[list[tuple]] = []
        for item in utiles:
            if renglones and abs(item[0] - renglones[-1][0][0]) <= tolerancia:
                renglones[-1].append(item)
            else:
                renglones.append([item])

        partes = []
        for fila in renglones:
            fila.sort(key=lambda it: it[1])  # izquierda -> derecha
            partes.append(" ".join(it[3] for it in fila))
        return " ".join(partes).strip()

    def leer(self, frame: np.ndarray) -> str | None:
        """Devuelve la linea si es NUEVA; None si se repite o no hay texto."""
        imagen = preprocesar(frame)
        try:
            detecciones, _ = self._motor(imagen)
        except Exception:  # noqa: BLE001
            return None
        if not detecciones:
            self._ultima_norm = ""  # pantalla sin subtitulo: se reinicia
            return None

        texto = self._ordenar_y_unir(detecciones)
        if len(texto) < 2:
            return None

        norm = normalizar(texto)
        if not norm:
            return None

        if self._ultima_norm:
            similitud = SequenceMatcher(None, self._ultima_norm, norm).ratio()
            if similitud >= self.umbral_similitud:
                return None  # sigue siendo el mismo subtitulo en pantalla

        self._ultima_norm = norm
        return texto

    def reiniciar(self) -> None:
        self._ultima_norm = ""
