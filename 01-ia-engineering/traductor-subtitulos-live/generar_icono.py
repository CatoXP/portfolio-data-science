"""Genera icono.ico: cuadrado casi negro con dos barras de subtitulo.

Se dibuja cada tamano a 8x y se reduce con LANCZOS para que los bordes salgan
limpios tambien a 16 px.
"""

from pathlib import Path

from PIL import Image, ImageDraw

TINTA = (17, 17, 17, 255)       # el #111111 del boton primario
HUESO = (251, 251, 250, 255)    # blanco calido
AZUL = (156, 201, 232, 255)     # acento pastel

TAMANOS = [16, 24, 32, 48, 64, 128, 256]
SUPER = 8


def dibujar(lado: int) -> Image.Image:
    n = lado * SUPER
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Placa de fondo con esquinas redondeadas (radio ~22% del lado).
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.22), fill=TINTA)

    # Dos barras: la de arriba larga, la de abajo corta y en color de acento.
    alto_barra = int(n * 0.105)
    radio = alto_barra / 2
    centro_y = n * 0.52
    hueco = int(n * 0.085)

    margen = n * 0.20
    y0 = centro_y - hueco / 2 - alto_barra
    d.rounded_rectangle(
        [margen, y0, n - margen, y0 + alto_barra], radius=radio, fill=HUESO
    )

    y1 = centro_y + hueco / 2
    d.rounded_rectangle(
        [margen, y1, n - margen * 1.9, y1 + alto_barra], radius=radio, fill=AZUL
    )

    return img.resize((lado, lado), Image.LANCZOS)


def main() -> None:
    destino = Path(__file__).resolve().parent / "icono.ico"
    capas = [dibujar(t) for t in TAMANOS]
    capas[-1].save(destino, format="ICO", sizes=[(t, t) for t in TAMANOS])
    print("Icono generado:", destino)

    # Vista previa grande, util para revisarlo a simple vista.
    dibujar(256).save(destino.with_name("icono_preview.png"))


if __name__ == "__main__":
    main()
