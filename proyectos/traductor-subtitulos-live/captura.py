"""Captura de una region rectangular de la pantalla.

El backend esta aislado detras de la clase `Capturador` para poder cambiarlo
sin tocar el resto del pipeline (ver README: frames en negro).
"""

from __future__ import annotations

import numpy as np


def _sesion_mss():
    """mss.mss quedo obsoleto en mss 10; mss.MSS es el nombre nuevo."""
    import mss

    return (getattr(mss, "MSS", None) or mss.mss)()


class Capturador:
    """Toma fotos de una region de pantalla usando mss (GDI BitBlt)."""

    def __init__(self, region: dict):
        self.region = dict(region)
        self._sct = None  # mss NO es thread-safe: se crea en el hilo que lo usa

    def _asegurar_sesion(self):
        if self._sct is None:
            self._sct = _sesion_mss()

    def capturar(self) -> np.ndarray:
        """Devuelve la region actual como array BGR (alto, ancho, 3)."""
        self._asegurar_sesion()
        crudo = self._sct.grab(self.region)
        return np.asarray(crudo)[:, :, :3]  # descarta el canal alfa

    def cerrar(self) -> None:
        if self._sct is not None:
            self._sct.close()
            self._sct = None


def geometria_pantalla() -> dict:
    """Bounding box del monitor principal."""
    with _sesion_mss() as sct:
        mon = sct.monitors[1]  # [0] es el escritorio virtual completo
        return {
            "left": mon["left"],
            "top": mon["top"],
            "width": mon["width"],
            "height": mon["height"],
        }


def region_por_defecto() -> dict:
    """Franja inferior centrada: donde viven los subtitulos casi siempre.

    Sirve para que la app funcione sin configurar nada; el usuario puede
    afinarla despues con el boton "Marcar zona".
    """
    pantalla = geometria_pantalla()
    ancho = int(pantalla["width"] * 0.80)
    alto = int(pantalla["height"] * 0.22)
    return {
        "left": pantalla["left"] + (pantalla["width"] - ancho) // 2,
        "top": pantalla["top"] + pantalla["height"] - alto - int(pantalla["height"] * 0.03),
        "width": ancho,
        "height": alto,
    }


def esta_en_negro(frame: np.ndarray, umbral: int = 8) -> bool:
    """True si el frame es practicamente negro.

    Sintoma tipico de captura bloqueada por aceleracion por hardware o DRM.
    """
    return bool(frame.max() <= umbral)
