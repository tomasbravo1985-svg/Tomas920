"""Fabrica sopas de letras y crucigramas (y sus soluciones).

Son funciones "puras": reciben palabras y devuelven cuadrículas.
BAUHAUS las usa para diseñar y REVISOR las comprueba por su cuenta.
"""
from __future__ import annotations

import random
import unicodedata

ALFABETO = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"

# Direcciones accesibles para 5.º a 8.º básico: sin palabras al revés.
DIRECCIONES_SOPA = {
    "horizontal": (0, 1),
    "vertical": (1, 0),
    "diagonal": (1, 1),
}


def normalizar(palabra: str) -> str:
    """'Atacama ' -> 'ATACAMA'; quita tildes pero conserva la Ñ."""
    palabra = palabra.strip().upper().replace("Ñ", "\0")
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", palabra)
                         if unicodedata.category(c) != "Mn")
    limpia = sin_tildes.replace("\0", "Ñ").replace(" ", "")
    if not limpia or any(c not in ALFABETO for c in limpia):
        raise ValueError(f"Palabra no válida para cuadrícula: {palabra!r}")
    return limpia


# ---------------------------------------------------------------- SOPA DE LETRAS

def crear_sopa(palabras: list[str], tamano: int = 14, semilla: int = 1,
               intentos: int = 300) -> dict:
    """Devuelve {"grilla": [[letra]], "ubicaciones": [{palabra, fila, col, direccion}]}."""
    palabras = sorted({normalizar(p) for p in palabras}, key=len, reverse=True)
    if palabras and len(palabras[0]) > tamano:
        raise ValueError(f"'{palabras[0]}' no cabe en una sopa de {tamano}x{tamano}")
    azar = random.Random(semilla)

    for _ in range(intentos):  # si una vuelta falla, se reintenta desde cero
        grilla = [[""] * tamano for _ in range(tamano)]
        ubicaciones = []
        for palabra in palabras:
            ubicada = _ubicar_en_sopa(grilla, palabra, azar)
            if not ubicada:
                break
            ubicaciones.append(ubicada)
        else:
            for f in range(tamano):
                for c in range(tamano):
                    if not grilla[f][c]:
                        grilla[f][c] = azar.choice(ALFABETO)
            return {"grilla": grilla, "ubicaciones": ubicaciones}
    raise ValueError("No se pudieron ubicar todas las palabras; usa una sopa más grande.")


def _ubicar_en_sopa(grilla, palabra, azar):
    n = len(grilla)
    opciones = []
    for nombre, (df, dc) in DIRECCIONES_SOPA.items():
        for f in range(n):
            for c in range(n):
                ff, cf = f + df * (len(palabra) - 1), c + dc * (len(palabra) - 1)
                if not (0 <= ff < n and 0 <= cf < n):
                    continue
                if all(grilla[f + df * i][c + dc * i] in ("", letra)
                       for i, letra in enumerate(palabra)):
                    opciones.append((f, c, nombre))
    if not opciones:
        return None
    f, c, nombre = azar.choice(opciones)
    df, dc = DIRECCIONES_SOPA[nombre]
    for i, letra in enumerate(palabra):
        grilla[f + df * i][c + dc * i] = letra
    return {"palabra": palabra, "fila": f, "col": c, "direccion": nombre}


def buscar_en_sopa(grilla: list[list[str]], palabra: str) -> list[tuple]:
    """Busca la palabra en las 8 direcciones. Devuelve todas las posiciones donde aparece.
    REVISOR la usa para comprobar la sopa SIN confiar en BAUHAUS."""
    palabra = normalizar(palabra)
    n_f, n_c = len(grilla), len(grilla[0])
    encontradas = []
    for f in range(n_f):
        for c in range(n_c):
            for df in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if df == dc == 0:
                        continue
                    ok = True
                    for i, letra in enumerate(palabra):
                        ff, cc = f + df * i, c + dc * i
                        if not (0 <= ff < n_f and 0 <= cc < n_c) or grilla[ff][cc] != letra:
                            ok = False
                            break
                    if ok:
                        encontradas.append((f, c, df, dc))
    return encontradas


# ---------------------------------------------------------------- CRUCIGRAMA

def crear_crucigrama(pistas: list[dict], semilla: int = 1, intentos: int = 60) -> dict:
    """pistas = [{"palabra": ..., "pista": ...}]. Prueba varios órdenes y se queda
    con el crucigrama que ubica más palabras y queda más compacto."""
    items = [{"palabra": normalizar(p["palabra"]), "pista": p["pista"]} for p in pistas]
    azar = random.Random(semilla)
    mejor = None
    for intento in range(intentos):
        orden = sorted(items, key=lambda x: len(x["palabra"]), reverse=True)
        if intento:
            azar.shuffle(orden)
        resultado = _armar_crucigrama(orden)
        clave = (len(resultado["no_ubicadas"]), resultado["alto"] * resultado["ancho"])
        if mejor is None or clave < mejor[0]:
            mejor = (clave, resultado)
    return mejor[1]


def _armar_crucigrama(items):
    celdas: dict[tuple[int, int], str] = {}
    direcciones_en: dict[tuple[int, int], set] = {}
    colocadas, no_ubicadas = [], []

    def puede(palabra, f, c, d):
        df, dc = (0, 1) if d == "H" else (1, 0)
        antes, despues = (f - df, c - dc), (f + df * len(palabra), c + dc * len(palabra))
        if antes in celdas or despues in celdas:
            return -1
        cruces = 0
        for i, letra in enumerate(palabra):
            pos = (f + df * i, c + dc * i)
            if pos in celdas:
                if celdas[pos] != letra or d in direcciones_en[pos]:
                    return -1
                cruces += 1
            else:  # no debe tocar letras de costado
                lado1 = (pos[0] + dc, pos[1] + df)
                lado2 = (pos[0] - dc, pos[1] - df)
                if lado1 in celdas or lado2 in celdas:
                    return -1
        return cruces

    def poner(item, f, c, d):
        df, dc = (0, 1) if d == "H" else (1, 0)
        for i, letra in enumerate(item["palabra"]):
            pos = (f + df * i, c + dc * i)
            celdas[pos] = letra
            direcciones_en.setdefault(pos, set()).add(d)
        colocadas.append({**item, "fila": f, "col": c, "direccion": d})

    for item in items:
        palabra = item["palabra"]
        if not colocadas:
            poner(item, 0, 0, "H")
            continue
        candidatos = []
        for (pf, pc), letra in list(celdas.items()):
            for i, l in enumerate(palabra):
                if l != letra:
                    continue
                for d in ("H", "V"):
                    f, c = (pf, pc - i) if d == "H" else (pf - i, pc)
                    cruces = puede(palabra, f, c, d)
                    if cruces > 0:
                        candidatos.append((cruces, f, c, d))
        if candidatos:
            candidatos.sort(key=lambda x: (-x[0], abs(x[1]) + abs(x[2])))
            _, f, c, d = candidatos[0]
            poner(item, f, c, d)
        else:
            no_ubicadas.append(item)

    # Recortar y llevar todo a coordenadas desde (0, 0)
    min_f = min(f for f, _ in celdas)
    min_c = min(c for _, c in celdas)
    alto = max(f for f, _ in celdas) - min_f + 1
    ancho = max(c for _, c in celdas) - min_c + 1
    grilla = [[""] * ancho for _ in range(alto)]
    for (f, c), letra in celdas.items():
        grilla[f - min_f][c - min_c] = letra
    for p in colocadas:
        p["fila"] -= min_f
        p["col"] -= min_c

    # Numerar en orden de lectura (arriba-abajo, izquierda-derecha)
    inicios = sorted({(p["fila"], p["col"]) for p in colocadas})
    numero_de = {pos: i + 1 for i, pos in enumerate(inicios)}
    for p in colocadas:
        p["numero"] = numero_de[(p["fila"], p["col"])]
    colocadas.sort(key=lambda p: (p["direccion"], p["numero"]))
    return {"grilla": grilla, "palabras": colocadas, "no_ubicadas": no_ubicadas,
            "alto": alto, "ancho": ancho}


def verificar_crucigrama(cruci: dict) -> list[str]:
    """REVISOR: comprueba letra por letra que cada palabra está bien escrita en la grilla."""
    problemas = []
    g = cruci["grilla"]
    for p in cruci["palabras"]:
        df, dc = (0, 1) if p["direccion"] == "H" else (1, 0)
        try:
            leida = "".join(g[p["fila"] + df * i][p["col"] + dc * i] for i in range(len(p["palabra"])))
        except IndexError:
            leida = ""
        if leida != p["palabra"]:
            problemas.append(f"La palabra {p['palabra']} no coincide con la grilla ({leida!r}).")
    for p in cruci["no_ubicadas"]:
        problemas.append(f"La palabra {p['palabra']} no quedó en el crucigrama.")
    return problemas
