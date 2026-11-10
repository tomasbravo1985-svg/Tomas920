"""MEMORIA DE CORRECCIONES (la administra ARCHIVO).

Ciclo de una corrección:
  1. PROPUESTA: REVISOR encontró un problema (o el profesor anotó una mejora).
  2. APROBADA: el profesor la aprueba -> se aplicará en TODAS las guías futuras.
  3. DESCARTADA: el profesor decide que no aplica.

Una corrección aprobada puede ser:
- una NOTA para ATENEA (ej.: "Usar ejemplos de Renca en la actividad inicial"), o
- una REGLA que REVISOR y BAUHAUS aplican solos. Reglas disponibles:
"""
from __future__ import annotations

import json
from datetime import date

from .configuracion import RAIZ, leer

ARCHIVO_MEMORIA = RAIZ / "datos" / "memoria" / "correcciones.json"
LECCIONES_MD = RAIZ / "contenidos" / "LECCIONES_APROBADAS.md"

REGLAS = {
    "palabras_prohibidas": "Lista de palabras que no deben aparecer en las guías (ej.: [\"obvio\", \"fácil\"]).",
    "max_palabras_instruccion": "Máximo de palabras en cada instrucción.",
    "max_palabras_oracion": "Máximo de palabras por oración en la lectura.",
    "legibilidad_minima": "Índice INFLESZ mínimo de la lectura.",
    "min_lineas_respuesta": "Mínimo de líneas para escribir en cada pregunta abierta.",
    "extension_flexible": "GG-001: mínimo de caras, sin máximo rígido, tiempos para 90 minutos y diagramación.",
    "nota": "Indicación pedagógica o de diseño para ATENEA o BAUHAUS (texto libre).",
}
__doc__ += "".join(f"\n  - {k}: {v}" for k, v in REGLAS.items())


def sincronizar_reglas_oficiales() -> list[dict]:
    """Copia a la memoria las reglas de config/reglas_aprobadas.toml (si aún no están).
    Así una regla aprobada oficialmente queda registrada UNA vez y se aplica siempre."""
    oficiales = leer("reglas_aprobadas").get("reglas", [])
    lista = cargar()
    cambios = False
    for r in oficiales:
        existente = next((c for c in lista if c.get("codigo") == r["codigo"]), None)
        datos = {"codigo": r["codigo"], "fecha": r["fecha_aprobacion"], "origen": "profesor",
                 "agente": "todos", "categoria": r["nombre"], "descripcion": r["descripcion"],
                 "estado": "aprobada", "fecha_aprobacion": r["fecha_aprobacion"],
                 "aprobada_por": r.get("aprobada_por", "profesor"),
                 "regla": {"tipo": r["tipo"], "valor": r.get("valor")}, "guias": [], "veces": 1}
        if existente is None:
            datos["id"] = _nuevo_id(lista)
            lista.append(datos)
            cambios = True
        elif any(existente.get(k) != v for k, v in datos.items() if k not in ("guias", "veces")):
            existente.update({k: v for k, v in datos.items() if k not in ("guias", "veces")})
            cambios = True
    if cambios:
        _guardar(lista)
        escribir_lecciones()
    return [c for c in lista if c.get("codigo")]


def cargar() -> list[dict]:
    if ARCHIVO_MEMORIA.is_file():
        return json.loads(ARCHIVO_MEMORIA.read_text(encoding="utf-8"))
    return []


def _guardar(lista: list[dict]) -> None:
    ARCHIVO_MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO_MEMORIA.write_text(json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8")


def _nuevo_id(lista) -> int:
    return max((c["id"] for c in lista), default=0) + 1


def proponer(agente: str, categoria: str, descripcion: str, guia: str = "", origen: str = "revisor") -> dict | None:
    """Agrega una propuesta, salvo que ya exista una igual (así no se repite)."""
    lista = cargar()
    for c in lista:
        if c["agente"] == agente and c["descripcion"] == descripcion:
            if guia and guia not in c["guias"]:
                c["guias"].append(guia)
                c["veces"] = c.get("veces", 1) + 1
                _guardar(lista)
            return None
    nueva = {"id": _nuevo_id(lista), "fecha": date.today().isoformat(), "origen": origen,
             "agente": agente, "categoria": categoria, "descripcion": descripcion,
             "estado": "propuesta", "regla": None, "guias": [guia] if guia else [], "veces": 1}
    lista.append(nueva)
    _guardar(lista)
    return nueva


def _validar_regla(regla: dict | None):
    if regla is None:
        return
    if regla.get("tipo") not in REGLAS:
        raise ValueError(f"Regla desconocida: {regla.get('tipo')}. Opciones: {', '.join(REGLAS)}")


def aprobar(id_: int, regla: dict | None = None) -> dict:
    _validar_regla(regla)
    lista = cargar()
    for c in lista:
        if c["id"] == id_:
            c["estado"] = "aprobada"
            c["fecha_aprobacion"] = date.today().isoformat()
            if regla:
                c["regla"] = regla
            _guardar(lista)
            escribir_lecciones()
            return c
    raise KeyError(f"No existe la corrección {id_}")


def descartar(id_: int) -> dict:
    lista = cargar()
    for c in lista:
        if c["id"] == id_:
            c["estado"] = "descartada"
            _guardar(lista)
            escribir_lecciones()
            return c
    raise KeyError(f"No existe la corrección {id_}")


def agregar_del_profesor(descripcion: str, agente: str = "atenea", regla: dict | None = None,
                         asignatura: str = "") -> dict:
    """Corrección escrita por el profesor: queda aprobada de inmediato."""
    _validar_regla(regla)
    lista = cargar()
    nueva = {"id": _nuevo_id(lista), "fecha": date.today().isoformat(), "origen": "profesor",
             "agente": agente, "categoria": regla["tipo"] if regla else "nota", "descripcion": descripcion,
             "estado": "aprobada", "fecha_aprobacion": date.today().isoformat(),
             "regla": regla or {"tipo": "nota"}, "asignatura": asignatura, "guias": [], "veces": 1}
    lista.append(nueva)
    _guardar(lista)
    escribir_lecciones()
    return nueva


def aprobadas(asignatura: str = "") -> list[dict]:
    return [c for c in cargar() if c["estado"] == "aprobada"
            and (not c.get("asignatura") or not asignatura or c["asignatura"] == asignatura)]


def reglas(lecciones: list[dict]) -> dict:
    """Junta las reglas aprobadas en un diccionario {tipo: valor}."""
    resultado: dict = {}
    for c in lecciones:
        r = c.get("regla") or {}
        tipo = r.get("tipo")
        if tipo == "palabras_prohibidas":
            resultado.setdefault(tipo, [])
            resultado[tipo] += [p.lower() for p in r.get("valor", [])]
        elif tipo == "extension_flexible":
            resultado.update(r.get("valor") or {})
            resultado["extension_flexible"] = c.get("codigo", "GG")
        elif tipo and tipo != "nota":
            resultado[tipo] = r.get("valor")
    return resultado


def escribir_lecciones() -> None:
    """Resumen que ATENEA (Claude Code en modo manual) lee ANTES de escribir una guía."""
    lineas = ["# Lecciones aprobadas por el profesor",
              "",
              "ATENEA debe aplicar estas indicaciones en cada guía nueva.",
              "Este archivo se actualiza solo; no lo edites a mano (usa `python memoria.py`).", ""]
    lista = aprobadas()
    if not lista:
        lineas.append("Todavía no hay lecciones aprobadas.")
    for c in lista:
        regla = c.get("regla") or {}
        extra = "" if regla.get("tipo") in (None, "nota") else f"  (regla automática: {regla['tipo']} = {regla.get('valor')})"
        alcance = f" [solo {c['asignatura']}]" if c.get("asignatura") else ""
        etiqueta = c.get("codigo") or f"#{c['id']}"
        if regla.get("tipo") == "extension_flexible":
            extra = f"  (aprobada el {c.get('fecha_aprobacion')})"
        lineas.append(f"- **{etiqueta}** ({c['agente'].upper()}){alcance}: {c['descripcion']}{extra}")
    LECCIONES_MD.parent.mkdir(parents=True, exist_ok=True)
    LECCIONES_MD.write_text("\n".join(lineas) + "\n", encoding="utf-8")
