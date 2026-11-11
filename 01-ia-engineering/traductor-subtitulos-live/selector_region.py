"""Seleccion visual de la zona de la pantalla donde salen los subtitulos."""

from __future__ import annotations

import tkinter as tk


def _limites_escritorio() -> dict:
    """Bounding box de TODOS los monitores, para poder seleccionar en cualquiera."""
    from captura import _sesion_mss

    with _sesion_mss() as sct:
        return dict(sct.monitors[0])


def seleccionar_region(master: tk.Misc | None = None) -> dict | None:
    """Abre una capa translucida y deja dibujar un rectangulo con el mouse.

    Devuelve {"left","top","width","height"} en coordenadas de pantalla,
    o None si el usuario cancela con Escape.
    """
    escritorio = _limites_escritorio()
    off_x, off_y = escritorio["left"], escritorio["top"]

    propia = master is None
    raiz = tk.Tk() if propia else tk.Toplevel(master)
    raiz.overrideredirect(True)
    raiz.attributes("-topmost", True)
    raiz.attributes("-alpha", 0.35)
    raiz.configure(bg="black")
    raiz.geometry(
        f"{escritorio['width']}x{escritorio['height']}+{off_x}+{off_y}"
    )
    raiz.config(cursor="crosshair")

    lienzo = tk.Canvas(raiz, bg="black", highlightthickness=0)
    lienzo.pack(fill="both", expand=True)
    lienzo.create_text(
        escritorio["width"] // 2,
        60,
        text="Arrastra sobre la franja de los subtitulos.   Escape = cancelar",
        fill="white",
        font=("Segoe UI", 20, "bold"),
    )

    estado = {"x0": 0, "y0": 0, "rect": None, "resultado": None}

    def al_presionar(evento):
        estado["x0"], estado["y0"] = evento.x, evento.y
        if estado["rect"] is not None:
            lienzo.delete(estado["rect"])
        estado["rect"] = lienzo.create_rectangle(
            evento.x, evento.y, evento.x, evento.y, outline="#00FF7F", width=3
        )

    def al_arrastrar(evento):
        if estado["rect"] is not None:
            lienzo.coords(
                estado["rect"], estado["x0"], estado["y0"], evento.x, evento.y
            )

    def al_soltar(evento):
        x0, y0 = estado["x0"], estado["y0"]
        x1, y1 = evento.x, evento.y
        izq, der = sorted((x0, x1))
        arr, aba = sorted((y0, y1))
        if der - izq >= 40 and aba - arr >= 20:  # ignora clics accidentales
            estado["resultado"] = {
                "left": int(izq) + off_x,
                "top": int(arr) + off_y,
                "width": int(der - izq),
                "height": int(aba - arr),
            }
            raiz.destroy()

    lienzo.bind("<Button-1>", al_presionar)
    lienzo.bind("<B1-Motion>", al_arrastrar)
    lienzo.bind("<ButtonRelease-1>", al_soltar)
    raiz.bind("<Escape>", lambda _e: raiz.destroy())

    raiz.focus_force()
    if propia:
        raiz.mainloop()
    else:
        raiz.grab_set()
        raiz.wait_window()

    return estado["resultado"]


if __name__ == "__main__":
    print(seleccionar_region())
