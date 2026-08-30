"""Traductor de subtitulos en vivo (ingles -> espanol).

Lee por OCR la franja de subtitulos que se ve en TU pantalla (por ejemplo la
transmision de Discord de alguien mas), la traduce sin conexion y la muestra en
un overlay flotante. Todo se controla con botones: no se capturan teclas del
sistema para no estorbar a Discord ni a ningun juego.

Uso:
    python main.py                 # abre la app
    python main.py --zona          # solo marcar la zona de subtitulos
    python main.py --diagnostico   # guarda un PNG de la zona (frames negros?)
    python main.py --test-imagen captura.png
"""

from __future__ import annotations

import argparse
import queue
import sys
import threading
import time
import tkinter as tk

try:  # la consola de Windows es cp1252 y revienta con ciertos caracteres
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

import config as cfg_mod
from captura import Capturador, esta_en_negro, region_por_defecto
from overlay import Overlay
from selector_region import seleccionar_region
from ui import (
    PAL,
    Boton,
    Fuentes,
    Insignia,
    esquinas_redondeadas,
    mostrar_en_barra_tareas,
)

ANCHO_PANEL = 268
ANCHO_CONTROL = 236
RUTA_ICONO = cfg_mod.RUTA_CONFIG.parent / "icono.ico"


class Aplicacion:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        if not self.cfg.get("region"):
            self.cfg["region"] = region_por_defecto()

        self.cola: queue.Queue[tuple[str, object]] = queue.Queue()
        self.activo = threading.Event()        # traduciendo si esta set
        self.detener = threading.Event()       # cierre del hilo trabajador
        self.reconfigurar = threading.Event()  # cambio de zona en caliente
        self._aviso_negro_dado = False
        # Rectangulo del overlay en pantalla, publicado por el hilo de Tk para
        # que el hilo trabajador pueda taparlo antes de pasar el frame al OCR.
        self._rect_overlay: tuple[int, int, int, int] | None = None
        self._arrastre = {"x": 0, "y": 0}

        self.raiz = tk.Tk()
        self.raiz.title("Traductor EN-ES")
        self.raiz.overrideredirect(True)   # chrome propio
        self.raiz.attributes("-topmost", True)
        self.raiz.configure(bg=PAL["lienzo"])
        self.raiz.protocol("WM_DELETE_WINDOW", self.salir)

        if RUTA_ICONO.exists():
            try:
                self.raiz.iconbitmap(default=str(RUTA_ICONO))
            except tk.TclError:
                pass

        self.fuentes = Fuentes()
        self._construir_panel()
        esquinas_redondeadas(self.raiz)
        # Ojo: la barra de tareas se arregla en ejecutar(), DESPUES de colocar
        # la ventana; hacerlo antes le pisaria la posicion.

        self.overlay = Overlay(self.raiz, self.cfg, self.fuentes)

        self.hilo = threading.Thread(target=self._bucle_trabajador, daemon=True)
        self.hilo.start()
        self.raiz.after(100, self._drenar_cola)

    # ------------------------------------------------------------------- panel
    def _construir_panel(self) -> None:
        # Un hairline de 1px como todo el borde de la ventana.
        borde = tk.Frame(self.raiz, bg=PAL["borde"], padx=1, pady=1)
        borde.pack(fill="both", expand=True)
        cuerpo = tk.Frame(borde, bg=PAL["lienzo"])
        cuerpo.pack(fill="both", expand=True)

        self._construir_encabezado(cuerpo)
        self._linea(cuerpo)

        contenido = tk.Frame(cuerpo, bg=PAL["lienzo"], padx=16, pady=16)
        contenido.pack(fill="both", expand=True)

        self.btn_iniciar = Boton(
            contenido, "Iniciar", self.alternar_traduccion, self.fuentes,
            variante="primario", ancho=ANCHO_CONTROL,
        )
        self.btn_iniciar.pack()

        self.btn_zona = Boton(
            contenido, "Marcar zona de subtítulos", self.marcar_zona,
            self.fuentes, ancho=ANCHO_CONTROL,
        )
        self.btn_zona.pack(pady=(8, 0))

        self.btn_ver = Boton(
            contenido, "Ocultar subtítulos", self.alternar_overlay,
            self.fuentes, ancho=ANCHO_CONTROL,
        )
        self.btn_ver.pack(pady=(8, 0))

        self._linea(contenido, pady=(18, 14))

        fila = tk.Frame(contenido, bg=PAL["lienzo"])
        fila.pack(fill="x")
        tk.Label(
            fila, text="Tamaño de letra", bg=PAL["lienzo"], fg=PAL["tinta_suave"],
            font=(self.fuentes.sans, 9),
        ).pack(side="left")
        Boton(
            fila, "+", lambda: self.ajustar_fuente(2), self.fuentes,
            ancho=30, alto=26,
        ).pack(side="right")
        Boton(
            fila, "−", lambda: self.ajustar_fuente(-2), self.fuentes,
            ancho=30, alto=26,
        ).pack(side="right", padx=(0, 6))

        self._linea(contenido, pady=(16, 14))

        self.insignia = Insignia(contenido, self.fuentes, ancho=ANCHO_CONTROL)
        self.insignia.pack(fill="x")

        self.etq_detalle = tk.Label(
            contenido, text="Sin iniciar", bg=PAL["lienzo"], fg=PAL["tinta_suave"],
            font=(self.fuentes.sans, 8), wraplength=ANCHO_CONTROL,
            justify="left", anchor="w",
        )
        self.etq_detalle.pack(fill="x", pady=(7, 0))

    def _construir_encabezado(self, padre) -> None:
        cabecera = tk.Frame(padre, bg=PAL["lienzo"], padx=16, pady=13)
        cabecera.pack(fill="x")

        izquierda = tk.Frame(cabecera, bg=PAL["lienzo"])
        izquierda.pack(side="left")
        tk.Label(
            izquierda, text="Subtítulos", bg=PAL["lienzo"], fg=PAL["tinta"],
            font=(self.fuentes.serif, 14),
        ).pack(anchor="w")
        tk.Label(
            izquierda, text="EN → ES  ·  sin conexión", bg=PAL["lienzo"],
            fg=PAL["tinta_suave"], font=(self.fuentes.mono, 7),
        ).pack(anchor="w", pady=(1, 0))

        cerrar = tk.Label(
            cabecera, text="×", bg=PAL["lienzo"], fg=PAL["tinta_suave"],
            font=(self.fuentes.sans, 15), cursor="hand2", padx=6,
        )
        cerrar.pack(side="right")
        cerrar.bind("<Button-1>", lambda _e: self.salir())
        cerrar.bind("<Enter>", lambda _e: cerrar.config(fg=PAL["tinta"]))
        cerrar.bind("<Leave>", lambda _e: cerrar.config(fg=PAL["tinta_suave"]))

        # La cabecera hace de barra de titulo: arrastra la ventana.
        for w in (cabecera, izquierda, *izquierda.winfo_children()):
            w.bind("<Button-1>", self._iniciar_arrastre)
            w.bind("<B1-Motion>", self._mover_ventana)

    def _linea(self, padre, pady=(0, 0)) -> None:
        tk.Frame(padre, height=1, bg=PAL["borde"]).pack(fill="x", pady=pady)

    def _iniciar_arrastre(self, evento):
        self._arrastre["x"], self._arrastre["y"] = evento.x, evento.y

    def _mover_ventana(self, evento):
        x = self.raiz.winfo_x() + evento.x - self._arrastre["x"]
        y = self.raiz.winfo_y() + evento.y - self._arrastre["y"]
        self.raiz.geometry(f"+{x}+{y}")

    def _estado(self, etiqueta: str, tono: str, detalle: str = "") -> None:
        self.insignia.actualizar(etiqueta, tono)
        if detalle:
            self.etq_detalle.config(text=detalle)

    # ------------------------------------------------------------------ acciones
    def alternar_traduccion(self) -> None:
        if self.activo.is_set():
            self.activo.clear()
            self.btn_iniciar.configurar_texto("Iniciar")
            self._estado("En pausa", "ambar", "Pulsa Iniciar para continuar.")
            self.overlay.mostrar_texto("En pausa")
        else:
            self._aviso_negro_dado = False
            self.activo.set()
            self.btn_iniciar.configurar_texto("Pausar")
            self._estado("Traduciendo", "verde", "Leyendo la zona marcada.")
            self.overlay.limpiar()

    def alternar_overlay(self) -> None:
        visible = self.overlay.alternar_visibilidad()
        self.btn_ver.configurar_texto(
            "Ocultar subtítulos" if visible else "Mostrar subtítulos"
        )

    def marcar_zona(self) -> None:
        estaba_activo = self.activo.is_set()
        self.activo.clear()
        overlay_visible = self.overlay.visible
        if overlay_visible:
            self.overlay.win.withdraw()
        self.raiz.withdraw()

        region = seleccionar_region(self.raiz)

        self.raiz.deiconify()
        if overlay_visible:
            self.overlay.win.deiconify()
            self.overlay.win.attributes("-topmost", True)

        if region:
            self.cfg["region"] = region
            cfg_mod.guardar(self.cfg)
            self.reconfigurar.set()
            self.etq_detalle.config(
                text=f"Zona marcada: {region['width']} x {region['height']} px"
            )
        if estaba_activo:
            self.activo.set()

    def ajustar_fuente(self, delta: int) -> None:
        tam = max(10, min(60, int(self.cfg["overlay"]["tam_fuente"]) + delta))
        self.cfg["overlay"]["tam_fuente"] = tam
        self.overlay.aplicar_estilo()

    def salir(self) -> None:
        self.detener.set()
        self.activo.clear()
        x, y = self.overlay.posicion_actual()
        self.cfg["overlay"]["x"], self.cfg["overlay"]["y"] = x, y
        cfg_mod.guardar(self.cfg)
        self.raiz.destroy()

    # -------------------------------------------------------------- hilo de fondo
    def _bucle_trabajador(self) -> None:
        """Captura -> OCR -> traduccion.

        Un solo hilo a proposito: asi siempre se toma el frame mas reciente en
        vez de ir acumulando frames viejos en una cola.
        """
        self.cola.put(
            ("estado", ("Cargando", "ambar", "Preparando modelos, tarda unos segundos."))
        )
        try:
            from ocr import LectorSubtitulos
            from traductor import TraductorOffline

            lector = LectorSubtitulos(
                umbral_confianza=self.cfg["umbral_confianza"],
                umbral_similitud=self.cfg["umbral_similitud"],
                hilos=self.cfg.get("hilos_ocr"),
            )
            traductor = TraductorOffline()
        except Exception as exc:  # noqa: BLE001
            self.cola.put(("error", f"No se pudieron cargar los modelos: {exc}"))
            return

        capturador = Capturador(self.cfg["region"])
        self.cola.put(
            ("estado", ("Listo", "azul", f"Motor {traductor.motor}. Marca la zona y pulsa Iniciar."))
        )
        periodo = 1.0 / max(0.5, float(self.cfg["fps"]))

        while not self.detener.is_set():
            if self.reconfigurar.is_set():
                capturador.cerrar()
                capturador = Capturador(self.cfg["region"])
                lector.reiniciar()
                self.reconfigurar.clear()

            if not self.activo.is_set():
                time.sleep(0.15)
                continue

            inicio = time.perf_counter()
            try:
                frame = capturador.capturar()
            except Exception as exc:  # noqa: BLE001
                self.cola.put(("error", f"Falló la captura: {exc}"))
                time.sleep(1.0)
                continue

            if esta_en_negro(frame):
                if not self._aviso_negro_dado:
                    self._aviso_negro_dado = True
                    self.cola.put(
                        (
                            "error",
                            "Zona en negro. Desactiva la aceleración por hardware "
                            "en Discord (Ajustes > Avanzado) y reinícialo.",
                        )
                    )
            else:
                self._aviso_negro_dado = False
                self._tapar_overlay(frame)
                texto = lector.leer(frame)
                if texto:
                    self.cola.put(("linea", traductor.traducir(texto)))

            restante = periodo - (time.perf_counter() - inicio)
            if restante > 0:
                time.sleep(restante)

        capturador.cerrar()

    def _tapar_overlay(self, frame) -> None:
        """Pinta de negro la parte del frame ocupada por nuestro propio overlay.

        Sin esto, si el overlay queda encima de la franja de subtitulos, el OCR
        leeria el texto en espanol que acabamos de escribir y lo volveria a
        traducir: un bucle de realimentacion que llena la pantalla de basura.
        """
        rect = self._rect_overlay
        if not rect:
            return
        ox, oy, ancho_ov, alto_ov = rect
        region = self.cfg["region"]
        # Interseccion entre el overlay y la zona capturada, en coordenadas
        # relativas al frame.
        x0 = max(ox, region["left"]) - region["left"]
        y0 = max(oy, region["top"]) - region["top"]
        x1 = min(ox + ancho_ov, region["left"] + region["width"]) - region["left"]
        y1 = min(oy + alto_ov, region["top"] + region["height"]) - region["top"]
        if x1 > x0 and y1 > y0:
            frame[y0:y1, x0:x1] = 0

    def _drenar_cola(self) -> None:
        # Se ejecuta en el hilo de Tk, el unico que puede consultar geometrias.
        self._rect_overlay = (
            self.overlay.rect_en_pantalla() if self.overlay.visible else None
        )
        try:
            while True:
                tipo, dato = self.cola.get_nowait()
                if tipo == "linea":
                    self.overlay.agregar_linea(dato)
                elif tipo == "estado":
                    etiqueta, tono, detalle = dato
                    self._estado(etiqueta, tono, detalle)
                elif tipo == "error":
                    self._estado("Error", "rojo", str(dato))
                    self.overlay.mostrar_texto(str(dato))
        except queue.Empty:
            pass
        if not self.detener.is_set():
            self.raiz.after(100, self._drenar_cola)

    def ejecutar(self) -> None:
        self.raiz.update_idletasks()
        # Arranca abajo a la derecha, fuera del camino del video.
        alto = self.raiz.winfo_reqheight()
        x = self.raiz.winfo_screenwidth() - ANCHO_PANEL - 28
        y = self.raiz.winfo_screenheight() - alto - 70
        self.raiz.geometry(f"{ANCHO_PANEL}x{alto}+{x}+{y}")
        self.raiz.update_idletasks()
        # Ya colocada: ahora si se puede devolver a la barra de tareas.
        mostrar_en_barra_tareas(self.raiz)
        self.raiz.mainloop()


# --------------------------------------------------------------------- modos CLI
def modo_zona(cfg: dict) -> int:
    region = seleccionar_region()
    if not region:
        print("Cancelado.")
        return 1
    cfg["region"] = region
    cfg_mod.guardar(cfg)
    print("Zona guardada:", region)
    return 0


def modo_diagnostico(cfg: dict) -> int:
    import cv2

    region = cfg.get("region") or region_por_defecto()
    cap = Capturador(region)
    frame = cap.capturar()
    cap.cerrar()
    salida = cfg_mod.RUTA_CONFIG.parent / "diagnostico.png"
    cv2.imwrite(str(salida), frame)
    print(f"Zona: {region}")
    print(f"Guardado: {salida}")
    if esta_en_negro(frame):
        print("\n[!] La imagen salio NEGRA.")
        print("    Discord > Ajustes > Avanzado > desactiva Aceleracion por hardware,")
        print("    reinicia Discord y vuelve a probar.")
    else:
        print("\nCaptura correcta. Abre el PNG y confirma que se lee el subtitulo.")
    return 0


def modo_test_imagen(cfg: dict, ruta: str) -> int:
    import cv2

    from ocr import LectorSubtitulos
    from traductor import TraductorOffline

    frame = cv2.imread(ruta)
    if frame is None:
        print(f"No pude abrir la imagen: {ruta}")
        return 1

    lector = LectorSubtitulos(
        umbral_confianza=cfg["umbral_confianza"],
        umbral_similitud=cfg["umbral_similitud"],
        hilos=cfg.get("hilos_ocr"),
    )
    texto = lector.leer(frame)
    print("OCR :", texto or "(no se detecto texto)")
    if texto:
        print("ES  :", TraductorOffline().traducir(texto))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Traductor de subtitulos en vivo")
    parser.add_argument("--zona", action="store_true", help="marcar la zona y salir")
    parser.add_argument(
        "--diagnostico", action="store_true", help="guardar PNG de la zona"
    )
    parser.add_argument(
        "--test-imagen", metavar="PNG", help="probar el OCR sobre una imagen"
    )
    args = parser.parse_args()

    cfg = cfg_mod.cargar()
    if args.zona:
        return modo_zona(cfg)
    if args.diagnostico:
        return modo_diagnostico(cfg)
    if args.test_imagen:
        return modo_test_imagen(cfg, args.test_imagen)

    Aplicacion(cfg).ejecutar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
