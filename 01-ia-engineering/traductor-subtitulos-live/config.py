"""Configuracion persistente del traductor de subtitulos."""

from __future__ import annotations

import copy
import json
from pathlib import Path

RUTA_CONFIG = Path(__file__).resolve().parent / "config.json"

CONFIG_POR_DEFECTO = {
    # Region de pantalla a leer: {"left","top","width","height"}.
    # None = se calcula la franja inferior de la pantalla principal.
    "region": None,
    # Cuantas veces por segundo se mira la pantalla. Un subtitulo dura 2-4 s,
    # asi que 3 sobra y deja la CPU libre para el video.
    "fps": 3.0,
    # Hilos de CPU para el OCR. None = automatico (6 rinde mejor que 12,
    # el hyperthreading se estorba a si mismo).
    "hilos_ocr": None,
    # Descarta detecciones dudosas del OCR.
    "umbral_confianza": 0.5,
    # Si la linea nueva se parece mas que esto a la anterior, es la misma
    # linea que sigue en pantalla: no se vuelve a traducir.
    "umbral_similitud": 0.90,
    # Lineas de historial visibles en el overlay.
    "lineas_visibles": 2,
    "overlay": {
        "x": None,
        "y": None,
        "ancho": 900,
        "alpha": 0.85,
        "tam_fuente": 22,
        "color_texto": "#FFFFFF",
        "color_fondo": "#000000",
    },
}


def _fusionar(base: dict, encima: dict) -> dict:
    """Mezcla recursiva: lo guardado pisa a los valores por defecto."""
    salida = copy.deepcopy(base)
    for clave, valor in (encima or {}).items():
        if isinstance(valor, dict) and isinstance(salida.get(clave), dict):
            salida[clave] = _fusionar(salida[clave], valor)
        else:
            salida[clave] = valor
    return salida


def cargar() -> dict:
    if RUTA_CONFIG.exists():
        try:
            guardado = json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            guardado = {}
    else:
        guardado = {}
    return _fusionar(CONFIG_POR_DEFECTO, guardado)


def guardar(cfg: dict) -> None:
    RUTA_CONFIG.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
    )
