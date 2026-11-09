"""Dibuja 4 paisajes sencillos en escala de grises para la guía de prueba.

Son ilustraciones simples hechas con código. Más adelante se pueden reemplazar por
fotografías reales: basta con poner otra imagen con el mismo nombre en recursos/imagenes/.
Uso:  python herramientas/dibujos_de_prueba.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

DESTINO = Path(__file__).resolve().parent.parent / "recursos" / "imagenes"
W, H = 900, 560
NEGRO, GRIS_OSC, GRIS, GRIS_CLARO, BLANCO = 0, 90, 150, 210, 255


def lienzo():
    img = Image.new("L", (W, H), BLANCO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, H - 1], outline=NEGRO, width=4)
    return img, d


def sol(d, x, y, r=45):
    d.ellipse([x - r, y - r, x + r, y + r], fill=GRIS_CLARO, outline=NEGRO, width=3)
    for i in range(12):
        import math
        a = i * math.pi / 6
        d.line([x + (r + 10) * math.cos(a), y + (r + 10) * math.sin(a),
                x + (r + 35) * math.cos(a), y + (r + 35) * math.sin(a)], fill=NEGRO, width=3)


def cactus(d, x, base):
    d.rounded_rectangle([x, base - 170, x + 34, base], 16, fill=GRIS, outline=NEGRO, width=3)
    d.rounded_rectangle([x - 40, base - 120, x - 14, base - 60], 12, fill=GRIS, outline=NEGRO, width=3)
    d.rectangle([x - 20, base - 75, x + 2, base - 55], fill=GRIS, outline=NEGRO, width=3)
    d.rounded_rectangle([x + 48, base - 140, x + 74, base - 85], 12, fill=GRIS, outline=NEGRO, width=3)
    d.rectangle([x + 32, base - 100, x + 56, base - 80], fill=GRIS, outline=NEGRO, width=3)


def arbol(d, x, base, alto=150, ancho=70, relleno=GRIS):
    d.rectangle([x - 8, base - alto * 0.35, x + 8, base], fill=GRIS_OSC, outline=NEGRO, width=2)
    d.polygon([(x, base - alto), (x - ancho / 2, base - alto * 0.3), (x + ancho / 2, base - alto * 0.3)],
              fill=relleno, outline=NEGRO)


def desierto():
    img, d = lienzo()
    sol(d, 740, 120)
    d.polygon([(0, 360), (250, 300), (520, 370), (900, 320), (900, 560), (0, 560)], fill=GRIS_CLARO, outline=NEGRO)
    d.polygon([(0, 450), (300, 400), (620, 460), (900, 420), (900, 560), (0, 560)], fill=230, outline=NEGRO)
    cactus(d, 200, 470)
    cactus(d, 640, 440)
    for x, y in [(100, 500), (420, 490), (780, 500)]:
        d.ellipse([x, y, x + 40, y + 18], fill=GRIS, outline=NEGRO, width=2)
    return img


def mediterraneo():
    img, d = lienzo()
    sol(d, 130, 110, 35)
    d.polygon([(250, 260), (420, 90), (560, 230), (700, 120), (900, 280), (900, 300), (250, 300)], fill=GRIS, outline=NEGRO)
    d.polygon([(380, 135), (420, 90), (460, 135), (440, 125), (420, 140), (400, 125)], fill=BLANCO, outline=NEGRO)
    d.polygon([(0, 330), (220, 250), (450, 330), (900, 290), (900, 560), (0, 560)], fill=GRIS_CLARO, outline=NEGRO)
    for fila in range(4):  # cultivos
        y = 400 + fila * 35
        d.line([480, y, 880, y - 20], fill=GRIS_OSC, width=3)
        for x in range(500, 880, 40):
            d.ellipse([x, y - 14 - (x - 480) // 20, x + 14, y - (x - 480) // 20], fill=GRIS, outline=NEGRO)
    d.polygon([(260, 560), (330, 420), (420, 330), (450, 330), (380, 430), (340, 560)], fill=BLANCO, outline=NEGRO, width=3)
    for x in (80, 160, 220):
        d.ellipse([x - 40, 330, x + 40, 400], fill=GRIS, outline=NEGRO, width=3)
        d.rectangle([x - 6, 395, x + 6, 450], fill=GRIS_OSC, outline=NEGRO)
    return img


def lluvioso():
    img, d = lienzo()
    for x, w in [(60, 240), (300, 280), (600, 260)]:
        d.ellipse([x, 20, x + w, 120], fill=GRIS, outline=NEGRO, width=3)
    for i in range(70):
        x = (i * 53) % 880 + 10
        y = 130 + (i * 37) % 200
        d.line([x, y, x - 10, y + 25], fill=GRIS_OSC, width=2)
    d.rectangle([0, 470, W, H], fill=GRIS_CLARO, outline=NEGRO)
    for i, x in enumerate(range(40, 900, 70)):
        arbol(d, x, 480 - (i % 2) * 15, alto=230 + (i % 3) * 30, ancho=90, relleno=GRIS_OSC if i % 2 else GRIS)
    for x in (150, 450, 720):
        d.ellipse([x, 500, x + 110, 530], fill=BLANCO, outline=NEGRO, width=2)  # charcos
    return img


def polar():
    img, d = lienzo()
    d.polygon([(0, 300), (150, 110), (280, 260), (420, 60), (600, 250), (760, 120), (900, 280), (900, 330), (0, 330)],
              fill=GRIS_CLARO, outline=NEGRO)
    for x0, xt, y in [(110, 150, 110), (380, 420, 60), (720, 760, 120)]:
        d.polygon([(x0, y + 60), (xt, y), (xt + 40, y + 60), (xt + 15, y + 45), (xt, y + 65)], fill=BLANCO, outline=NEGRO)
    d.polygon([(330, 330), (420, 160), (510, 330)], fill=BLANCO, outline=NEGRO, width=3)  # glaciar
    for y in range(200, 330, 30):
        d.line([420 - (y - 160) * 0.5 + 15, y, 420 + (y - 160) * 0.5 - 15, y], fill=GRIS, width=2)
    d.rectangle([0, 330, W, H], fill=GRIS, outline=NEGRO)  # mar
    for y in range(360, 560, 40):
        for x in range(20, 900, 90):
            d.arc([x, y, x + 50, y + 20], 0, 180, fill=NEGRO, width=2)
    for x, w in [(120, 160), (560, 220)]:
        d.polygon([(x, 420), (x + 30, 380), (x + w - 30, 380), (x + w, 420)], fill=BLANCO, outline=NEGRO, width=3)
    return img


if __name__ == "__main__":
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre, f in [("desierto", desierto), ("mediterraneo", mediterraneo),
                      ("lluvioso", lluvioso), ("polar", polar)]:
        ruta = DESTINO / f"paisaje_{nombre}.png"
        f().save(ruta)
        print("creado", ruta)
