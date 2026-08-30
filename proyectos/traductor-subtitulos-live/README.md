# Traductor de subtítulos en vivo (inglés → español)

Lee por OCR la franja de subtítulos que se ve en **tu** pantalla —por ejemplo la
transmisión de Discord de alguien más—, la traduce **sin conexión** y la muestra en un
overlay flotante encima del video.

- 100% local: no sube nada a internet, no necesita API keys, no cuesta nada.
- Sin atajos de teclado globales: todo se maneja con botones, para no estorbar a Discord,
  al navegador ni a ningún juego.
- ~230 ms desde que aparece el subtítulo hasta que se ve traducido (medido en Ryzen 5 5600G).

---

## Instalación (una sola vez)

```bash
pip install -r requirements.txt
python instalar_modelo.py      # descarga el modelo en→es (~100 MB)
```

## Uso

Doble clic en **Traductor de Subtítulos**, el acceso directo del Escritorio.
También sirve `Traductor.bat` dentro de la carpeta, o desde la terminal:

```bash
python main.py
```

Si el acceso directo se pierde o mueves la carpeta, se regenera con:

```powershell
powershell -ExecutionPolicy Bypass -File crear_acceso_directo.ps1
```

Se abren dos ventanas: el **panel de control** y el **overlay** (la barra negra donde
aparecerá el español).

1. Pon la transmisión **en pantalla completa** — mientras más grande el subtítulo, mejor lee el OCR.
2. Pulsa **Marcar zona de subtítulos** y arrastra un rectángulo sobre la franja donde salen
   los subtítulos en inglés. Ajusta un poco más ancho y alto de lo necesario.
3. Pulsa **Iniciar**.
4. Arrastra el overlay con el mouse a donde te acomode y ajusta el tamaño de letra con `+` / `−`.

La primera vez tarda unos segundos en cargar los modelos; el estado se muestra en el panel.

### Botones

| Botón | Qué hace |
|---|---|
| **Iniciar / Pausar** | Arranca o detiene la traducción |
| **Ocultar / Mostrar subtítulos** | Esconde el overlay sin detener nada |
| **Marcar zona de subtítulos** | Vuelve a definir qué parte de la pantalla se lee |
| **+ / −** | Tamaño de letra del overlay |
| **Salir** | Cierra y guarda la configuración |

Tu configuración (zona, posición del overlay, tamaño de letra) se guarda sola en
`config.json`.

---

## Si algo no funciona

**No aparece nada / el estado dice "Zona en negro"**
La captura salió negra. Pasa cuando el video se dibuja con aceleración por hardware.
Comprueba con:

```bash
python main.py --diagnostico     # guarda diagnostico.png con lo que ve la app
```

Abre ese PNG. Si está negro: en Discord entra a **Ajustes → Avanzado** y desactiva
**Aceleración por hardware**, reinicia Discord y vuelve a probar.

**Lee mal el texto**
Casi siempre es que el subtítulo tiene pocos píxeles. Pon la transmisión en pantalla
completa y vuelve a **Marcar zona** ajustando bien al área del texto. También puedes probar
el OCR sobre una captura fija:

```bash
python main.py --test-imagen mi_captura.png
```

**Va lento**
Sube `fps` en `config.json` solo si tienes CPU de sobra; bajarlo a `2.0` alivia la carga.
En `hilos_ocr` puedes fijar el número de hilos (por defecto 6; más no ayuda).

**El overlay tapa el video**
Arrástralo. Si lo pones encima de la zona que se lee no pasa nada: la app tapa
automáticamente su propia área antes de pasar la imagen al OCR, para no traducir su propio
texto en bucle.

---

## Cómo está hecho

```
[hilo trabajador]  captura (mss) → OCR (RapidOCR/ONNX) → filtro anti-repetición
                   → traducción (Argos/CTranslate2) → cola
[hilo de Tk]       drena la cola cada 100 ms y repinta el overlay
```

| Archivo | Rol |
|---|---|
| `main.py` | Panel de control, hilos y modos de línea de comandos |
| `captura.py` | Captura de la región de pantalla |
| `ocr.py` | Preprocesado, OCR y filtro anti-repetición |
| `traductor.py` | Traducción offline en→es |
| `overlay.py` | Ventana flotante |
| `ui.py` | Paleta, tipografía y widgets dibujados a mano |
| `selector_region.py` | Selección visual de la zona |
| `config.py` | Configuración persistente |
| `generar_icono.py` | Genera `icono.ico` |
| `crear_acceso_directo.ps1` | Crea el acceso directo del Escritorio |

### Diseño

Monocromo cálido con acentos en pastel apagado, usados solo cuando significan algo (el
estado de la app). Tipografía con contraste: serif editorial para el nombre, monoespaciada
para los metadatos, sans del sistema para los controles. Bordes hairline de 1px, sin
sombras ni degradados.

Tkinter no trae botones planos ni esquinas redondeadas, así que los controles se dibujan
sobre un `Canvas` (`ui.py`) y la ventana se redondea con DWM en Windows 11. Al quitar la
barra de título nativa Windows deja de listar la app en la barra de tareas; se corrige
cambiando los estilos extendidos (`WS_EX_APPWINDOW`), pero **después** de posicionar la
ventana, porque reaparecer la reubica.

El overlay es oscuro por necesidad —va sobre video y es lo único que garantiza contraste
sobre cualquier escena—. Su jerarquía es tipográfica, no de cajas: la línea anterior queda
atenuada y más chica, la actual en blanco y con peso.

### Dos detalles que importan

**El OCR era 11× más lento de lo necesario.** RapidOCR viene configurado con
`limit_type: min` y `limit_side_len: 736`, es decir que *amplía* la imagen hasta que su lado
**corto** mida 736 px. Una franja de subtítulos es ancha y bajita (1100×190), así que la
ampliaba unas 4× antes de detectar: **2768 ms** por frame. Cambiando a `limit_type: max` y
apagando el clasificador de rotación (inútil aquí, los subtítulos nunca vienen al revés):
**252 ms**, con texto idéntico. La configuración se pasa por archivo (`ocr_config.yaml`,
generado automáticamente) porque el sistema de `kwargs` del constructor descarta valores
en la versión 1.4.x.

**El filtro anti-repetición.** Un subtítulo dura ~3 s en pantalla, o sea ~9 capturas del
mismo texto. Se normaliza cada lectura y se compara con la anterior por similitud
(`difflib`, umbral 0.90); si es la misma frase se descarta sin traducir. Sin esto, la app
traduciría nueve veces cada línea.

### Latencia medida (Ryzen 5 5600G, CPU, sin GPU)

| Etapa | Tiempo |
|---|---|
| OCR | ~170 ms |
| Traducción | ~56 ms |
| **Total por línea nueva** | **~226 ms** |
| Frame sin subtítulo (el caso más común) | ~64 ms |

---

## Nota

Es una ayuda personal de accesibilidad: traduce en el momento lo que ya estás viendo y no
guarda ninguna transcripción en disco. El texto vive solo en pantalla mientras se muestra.
