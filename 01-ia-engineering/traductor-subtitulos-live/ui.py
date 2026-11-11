"""Capa de widgets: paleta, tipografia y controles dibujados a mano.

Tkinter no trae botones planos ni esquinas redondeadas, asi que se dibujan
sobre un Canvas. La paleta es monocromo calido con acentos en pastel apagado,
usados solo cuando significan algo (el estado de la app).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

# --------------------------------------------------------------------- paleta
PAL = {
    "lienzo": "#FBFBFA",       # fondo del panel
    "superficie": "#FFFFFF",   # tarjetas
    "borde": "#EAEAEA",        # hairlines
    "tinta": "#2F3437",        # texto principal (nunca negro puro)
    "tinta_suave": "#787774",  # texto secundario
    "solido": "#111111",       # boton primario
    "solido_hover": "#333333",
    # Acentos pastel: fondo + texto
    "verde": ("#EDF3EC", "#346538"),
    "azul": ("#E1F3FE", "#1F6C9F"),
    "ambar": ("#FBF3DB", "#956400"),
    "rojo": ("#FDEBEC", "#9F2F2D"),
    "gris": ("#F1F1EF", "#787774"),
    # Overlay (oscuro por necesidad: va encima del video)
    "ov_fondo": "#15161A",
    "ov_texto": "#FFFFFF",
    "ov_tenue": "#8E8E88",
}


def _primera_disponible(candidatas: list[str], respaldo: str) -> str:
    disponibles = {f.lower() for f in tkfont.families()}
    for nombre in candidatas:
        if nombre.lower() in disponibles:
            return nombre
    return respaldo


class Fuentes:
    """Se resuelven una sola vez, despues de que exista la raiz de Tk."""

    def __init__(self):
        self.sans = _primera_disponible(
            ["Segoe UI Variable Text", "Segoe UI"], "Helvetica"
        )
        self.serif = _primera_disponible(
            ["Constantia", "Georgia", "Cambria"], "Times"
        )
        self.mono = _primera_disponible(
            ["Cascadia Mono", "Consolas", "Segoe UI Mono"], "Courier"
        )


def esquinas_redondeadas(ventana: tk.Misc) -> None:
    """Redondea la ventana usando DWM (Windows 11). Si no se puede, ni modo."""
    try:
        import ctypes

        ventana.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id())
        if not hwnd:
            return
        # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
        valor = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(valor), ctypes.sizeof(valor)
        )
    except Exception:  # noqa: BLE001
        pass


def mostrar_en_barra_tareas(ventana: tk.Misc) -> None:
    """Devuelve la ventana a la barra de tareas y al Alt+Tab.

    Al quitar la barra de titulo nativa (`overrideredirect`), Windows marca la
    ventana como herramienta y deja de listarla. Se corrige cambiando los
    estilos extendidos: fuera WS_EX_TOOLWINDOW, dentro WS_EX_APPWINDOW.
    """
    try:
        import ctypes

        GWL_EXSTYLE = -20
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        ventana.update_idletasks()
        user32 = ctypes.windll.user32
        hwnd = user32.GetParent(ventana.winfo_id())
        if not hwnd:
            return
        estilo = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        estilo = (estilo & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, estilo)

        # El cambio de estilo solo surte efecto al reaparecer la ventana, y al
        # reaparecer Windows la reubica. Por eso se toma la geometria ANTES de
        # esconderla y se vuelve a aplicar despues.
        geometria = ventana.geometry()

        def _restaurar():
            ventana.deiconify()
            ventana.geometry(geometria)
            ventana.attributes("-topmost", True)

        ventana.withdraw()
        ventana.after(10, _restaurar)
    except Exception:  # noqa: BLE001
        pass


def rect_redondeado(lienzo: tk.Canvas, x0, y0, x1, y1, r, **kw):
    """Rectangulo de esquinas redondeadas como poligono suavizado."""
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    puntos = [
        x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
        x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
        x0, y1, x0, y1 - r, x0, y0 + r, x0, y0,
    ]
    return lienzo.create_polygon(puntos, smooth=True, **kw)


class Boton(tk.Canvas):
    """Boton plano dibujado a mano, con estados de hover y pulsado.

    variante: "primario" (solido oscuro) o "secundario" (contorno de 1px).
    """

    def __init__(
        self,
        padre,
        texto: str,
        comando,
        fuentes: Fuentes,
        variante: str = "secundario",
        ancho: int = 236,
        alto: int = 38,
        fondo_padre: str | None = None,
    ):
        super().__init__(
            padre,
            width=ancho,
            height=alto,
            highlightthickness=0,
            bd=0,
            bg=fondo_padre or PAL["lienzo"],
        )
        self.comando = comando
        self.variante = variante
        self._activo = True

        if variante == "primario":
            self._relleno, self._relleno_hover = PAL["solido"], PAL["solido_hover"]
            self._contorno, self._color_texto = PAL["solido"], "#FFFFFF"
        else:
            self._relleno, self._relleno_hover = PAL["superficie"], "#F7F6F3"
            self._contorno, self._color_texto = PAL["borde"], PAL["tinta"]

        self._forma = rect_redondeado(
            self, 0.5, 0.5, ancho - 0.5, alto - 0.5, 6,
            fill=self._relleno, outline=self._contorno, width=1,
        )
        self._etq = self.create_text(
            ancho / 2, alto / 2 + 1, text=texto,
            fill=self._color_texto, font=(fuentes.sans, 10),
        )

        self.bind("<Enter>", self._entrar)
        self.bind("<Leave>", self._salir)
        self.bind("<ButtonPress-1>", self._presionar)
        self.bind("<ButtonRelease-1>", self._soltar)

    def configurar_texto(self, texto: str) -> None:
        self.itemconfig(self._etq, text=texto)

    def _entrar(self, _e=None):
        if self._activo:
            self.itemconfig(self._forma, fill=self._relleno_hover)
            self.config(cursor="hand2")

    def _salir(self, _e=None):
        self.itemconfig(self._forma, fill=self._relleno)

    def _presionar(self, _e=None):
        # Equivalente al scale(0.98) del protocolo: un hundido apenas visible.
        self.move(self._etq, 0, 1)

    def _soltar(self, _e=None):
        self.move(self._etq, 0, -1)
        if self._activo and self.comando:
            self.comando()


class Insignia(tk.Canvas):
    """Pastilla de estado: mayusculas diminutas con tracking amplio."""

    def __init__(self, padre, fuentes: Fuentes, ancho: int = 236, alto: int = 22):
        super().__init__(
            padre, width=ancho, height=alto,
            highlightthickness=0, bd=0, bg=PAL["lienzo"],
        )
        self._fuentes = fuentes
        self._ancho, self._alto = ancho, alto
        self._forma = None
        self._texto = None
        self.actualizar("Detenido", "gris")

    def actualizar(self, texto: str, tono: str = "gris") -> None:
        fondo, tinta = PAL.get(tono, PAL["gris"])
        # Con tracking manual: Tk no expone letter-spacing.
        etiqueta = " ".join(texto.upper())
        self.delete("all")
        temporal = tkfont.Font(family=self._fuentes.sans, size=7, weight="bold")
        ancho_txt = min(temporal.measure(etiqueta) + 22, self._ancho)
        self._forma = rect_redondeado(
            self, 0, 0, ancho_txt, self._alto, self._alto / 2,
            fill=fondo, outline="",
        )
        self._texto = self.create_text(
            ancho_txt / 2, self._alto / 2 + 1, text=etiqueta,
            fill=tinta, font=(self._fuentes.sans, 7, "bold"),
        )


def separador(padre, ancho: int = 236, fondo: str | None = None) -> tk.Frame:
    """Hairline de 1px, el unico divisor permitido."""
    linea = tk.Frame(
        padre, height=1, width=ancho, bg=PAL["borde"], bd=0, highlightthickness=0
    )
    return linea
