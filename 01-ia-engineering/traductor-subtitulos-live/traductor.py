"""Traduccion offline ingles -> espanol.

Motor principal: Argos Translate (CTranslate2, rapido en CPU).
Motor de respaldo: MarianMT via transformers, por si Argos no esta instalado.
"""

from __future__ import annotations


class TraductorOffline:
    """Traduce texto en->es sin salir a internet."""

    def __init__(self, origen: str = "en", destino: str = "es"):
        self.origen = origen
        self.destino = destino
        self.motor = None
        self._traducir_fn = None
        self._cache: dict[str, str] = {}
        self._cargar()

    def _cargar(self) -> None:
        try:
            import argostranslate.translate as tr

            try:
                objeto = tr.get_translation_from_codes(self.origen, self.destino)
                self._traducir_fn = objeto.translate
            except Exception:
                # API antigua o paquete resuelto de otra forma
                self._traducir_fn = lambda t: tr.translate(t, self.origen, self.destino)
            # Calentamos el modelo para que la primera linea real no tarde.
            self._traducir_fn("Hello.")
            self.motor = "argos"
            return
        except Exception as exc:  # noqa: BLE001
            error_argos = exc

        try:
            from transformers import MarianMTModel, MarianTokenizer

            nombre = f"Helsinki-NLP/opus-mt-{self.origen}-{self.destino}"
            tok = MarianTokenizer.from_pretrained(nombre)
            modelo = MarianMTModel.from_pretrained(nombre)

            def _marian(texto: str) -> str:
                lotes = tok([texto], return_tensors="pt", padding=True)
                salida = modelo.generate(**lotes, max_new_tokens=256)
                return tok.decode(salida[0], skip_special_tokens=True)

            self._traducir_fn = _marian
            self.motor = "marian"
            return
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "No hay ningun motor de traduccion disponible.\n"
                f"  Argos fallo con: {error_argos}\n"
                f"  Marian fallo con: {exc}\n"
                "Instala el paquete en->es con:  python instalar_modelo.py"
            ) from exc

    def traducir(self, texto: str) -> str:
        texto = (texto or "").strip()
        if not texto:
            return ""
        if texto in self._cache:
            return self._cache[texto]
        try:
            resultado = (self._traducir_fn(texto) or "").strip()
        except Exception:  # noqa: BLE001
            resultado = texto  # ante un fallo, mejor mostrar el original
        # Cache acotado: los subtitulos se repiten (openings, muletillas).
        if len(self._cache) > 500:
            self._cache.clear()
        self._cache[texto] = resultado
        return resultado


if __name__ == "__main__":
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    frase = " ".join(sys.argv[1:]) or "Hello, how are you? I will protect everyone."
    t = TraductorOffline()
    print(f"[motor: {t.motor}]")
    print("EN:", frase)
    print("ES:", t.traducir(frase))
