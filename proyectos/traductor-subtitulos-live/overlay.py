"""Ventana flotante que muestra la traduccion encima del video."""

from __future__ import annotations

import tkinter as tk

from ui import PAL, Fuentes, esquinas_redondeadas


class Overlay:
    """Barra oscura sin bordes, siempre visible, arrastrable con el mouse.

    Va sobre video, asi que aqui la superficie es oscura por necesidad: es lo
    unico que garantiza contraste sobre cualquier escena. La jerarquia se hace
    con tipografia, no con cajas: la linea anterior queda atenuada y la actual
    en blanco.

    No usa atajos de teclado globales a proposito: interceptar teclas del
    sistema molestaria en Discord, el navegador o cualquier juego.
    """

    def __init__(self, master: tk.Misc, cfg: dict, fuentes: Fuentes):
        self.cfg = cfg
        self.fuentes = fuentes
        ov = cfg["overlay"]
        self._visible = True
        self._arrastre = {"x": 0, "y": 0}
        self._previa = ""
        self._actual = ""

        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", float(ov["alpha"]))
        self.win.configure(bg=PAL["ov_fondo"])

        ancho = int(ov["ancho"])
        self.marco = tk.Frame(self.win, bg=PAL["ov_fondo"], padx=26, pady=16)
        self.marco.pack(fill="both", expand=True)

        self.etq_previa = tk.Label(
            self.marco,
            text="",
            bg=PAL["ov_fondo"],
            fg=PAL["ov_tenue"],
            justify="center",
            wraplength=ancho - 52,
        )
        self.etq_actual = tk.Label(
            self.marco,
            text="",
            bg=PAL["ov_fondo"],
            fg=PAL["ov_texto"],
            justify="center",
            wraplength=ancho - 52,
        )
        self.etq_previa.pack(fill="x")
        self.etq_actual.pack(fill="x", pady=(3, 0))

        self._aplicar_fuentes()
        self._colocar(ancho, ov.get("x"), ov.get("y"))
        self._habilitar_arrastre()
        esquinas_redondeadas(self.win)
        self.mostrar_texto("Listo. Marca la zona y pulsa Iniciar.")

    # ------------------------------------------------------------------ estilo
    def _aplicar_fuentes(self) -> None:
        tam = int(self.cfg["overlay"]["tam_fuente"])
        # La linea previa va mas chica: contraste tipografico, no otra caja.
        self.etq_previa.config(font=(self.fuentes.sans, max(8, int(tam * 0.72))))
        self.etq_actual.config(font=(self.fuentes.sans, tam, "bold"))

    # ---------------------------------------------------------------- posicion
    def _colocar(self, ancho: int, x, y) -> None:
        self.win.update_idletasks()
        pantalla_w = self.win.winfo_screenwidth()
        pantalla_h = self.win.winfo_screenheight()
        alto = self.win.winfo_reqheight()
        if x is None or y is None:
            x = (pantalla_w - ancho) // 2
            # Justo ARRIBA de la zona que se lee por OCR. Si lo pusieramos
            # encima de ella, el OCR leeria nuestro propio texto en espanol y
            # lo volveria a traducir en bucle.
            region = self.cfg.get("region") or {}
            tope = region.get("top")
            y = (int(tope) - alto - 20) if tope else (pantalla_h - 230)
            y = max(10, y)
        self.win.geometry(f"{ancho}x{alto}+{int(x)}+{int(y)}")

    def _habilitar_arrastre(self) -> None:
        def iniciar(evento):
            self._arrastre["x"], self._arrastre["y"] = evento.x, evento.y

        def mover(evento):
            x = self.win.winfo_x() + evento.x - self._arrastre["x"]
            y = self.win.winfo_y() + evento.y - self._arrastre["y"]
            self.win.geometry(f"+{x}+{y}")

        for widget in (self.win, self.marco, self.etq_previa, self.etq_actual):
            widget.bind("<Button-1>", iniciar)
            widget.bind("<B1-Motion>", mover)
            widget.bind("<Enter>", lambda _e: self.win.config(cursor="fleur"))

    def posicion_actual(self) -> tuple[int, int]:
        return self.win.winfo_x(), self.win.winfo_y()

    def rect_en_pantalla(self) -> tuple[int, int, int, int]:
        """(x, y, ancho, alto) de la ventana en coordenadas de pantalla."""
        return (
            self.win.winfo_x(),
            self.win.winfo_y(),
            self.win.winfo_width(),
            self.win.winfo_height(),
        )

    # ----------------------------------------------------------------- contenido
    def mostrar_texto(self, texto: str) -> None:
        """Sustituye todo el contenido (mensajes de estado)."""
        self._previa, self._actual = "", texto
        self._repintar()

    def agregar_linea(self, texto: str) -> None:
        self._previa, self._actual = self._actual, texto
        self._repintar()

    def limpiar(self) -> None:
        self._previa, self._actual = "", ""
        self._repintar()

    def _repintar(self) -> None:
        self.etq_previa.config(text=self._previa)
        self.etq_actual.config(text=self._actual)
        # La linea previa desaparece del layout cuando esta vacia.
        if self._previa:
            if not self.etq_previa.winfo_ismapped():
                self.etq_previa.pack(fill="x", before=self.etq_actual)
        else:
            self.etq_previa.pack_forget()

        self.win.update_idletasks()
        ancho = int(self.cfg["overlay"]["ancho"])
        x, y = self.posicion_actual()
        self.win.geometry(f"{ancho}x{self.win.winfo_reqheight()}+{x}+{y}")

    # ---------------------------------------------------------------- visibilidad
    @property
    def visible(self) -> bool:
        return self._visible

    def alternar_visibilidad(self) -> bool:
        if self._visible:
            self.win.withdraw()
        else:
            self.win.deiconify()
            self.win.attributes("-topmost", True)
        self._visible = not self._visible
        return self._visible

    def aplicar_estilo(self) -> None:
        """Reaplica tamano de fuente / opacidad tras cambiarlos en caliente."""
        ov = self.cfg["overlay"]
        self.win.attributes("-alpha", float(ov["alpha"]))
        ancho = int(ov["ancho"])
        for etq in (self.etq_previa, self.etq_actual):
            etq.config(wraplength=ancho - 52)
        self._aplicar_fuentes()
        self._repintar()
