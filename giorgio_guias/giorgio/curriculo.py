"""Verificación de Objetivos de Aprendizaje (OA) contra un registro de fuentes oficiales.

Regla de oro: un OA solo se considera VERIFICADO si está en
config/curriculo/oa_verificados.json, con su fuente oficial, y el texto coincide.
Todo lo demás queda "pendiente de confirmación". Nunca se inventa un número de OA.
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from datetime import date

from .configuracion import CARPETA_CONFIG

REGISTRO = CARPETA_CONFIG / "curriculo" / "oa_verificados.json"
ASIGNATURAS_INSTITUCIONALES = {"proyecto de regeneracion"}
SIMILITUD_MINIMA = 0.85


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ ]", " ", texto)).strip()


def niveles_de(cursos: list[str]) -> list[str]:
    """['6.º C'] -> ['6'];  ['5.º', '6.º'] -> ['5', '6']"""
    return sorted({m.group(1) for c in cursos if (m := re.match(r"\s*(\d+)", c))})


def codigo_de(texto: str) -> str | None:
    m = re.search(r"\bOA\s*[_\-]?\s*(\d+)\b", texto or "", re.IGNORECASE)
    return f"OA {int(m.group(1))}" if m else None


def cargar() -> list[dict]:
    return json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.is_file() else []


def agregar(asignatura: str, nivel: str, codigo: str, texto: str, fuente: str) -> dict:
    if not fuente.strip():
        raise ValueError("Un OA verificado necesita su fuente oficial.")
    codigo_n = codigo_de(codigo)
    if not codigo_n:
        raise ValueError("El código debe tener la forma 'OA 12'.")
    registro = cargar()
    registro = [r for r in registro if not (r["asignatura"] == asignatura and r["nivel"] == str(nivel)
                                            and r["codigo"] == codigo_n)]
    nuevo = {"asignatura": asignatura, "nivel": str(nivel), "codigo": codigo_n, "texto": texto.strip(),
             "fuente": fuente.strip(), "fecha_verificacion": date.today().isoformat()}
    registro.append(nuevo)
    REGISTRO.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    return nuevo


def _propuestas(oa) -> list[dict]:
    """Acepta el OA escrito como texto, como ficha o como lista de fichas."""
    if not oa:
        return []
    if isinstance(oa, str):
        return [{"codigo": codigo_de(oa), "texto": oa}]
    if isinstance(oa, dict):
        return [oa]
    return [x if isinstance(x, dict) else {"codigo": codigo_de(x), "texto": x} for x in oa]


def verificar(oa, asignatura: str, cursos: list[str]) -> list[dict]:
    """Devuelve una ficha por OA con estado: verificado / pendiente / institucional."""
    if _norm(asignatura) in ASIGNATURAS_INSTITUCIONALES and not oa:
        return [{"estado": "institucional", "codigo": None, "texto": "",
                 "motivo": "Proyecto de la escuela: no tiene OA propio en el currículum nacional."}]
    propuestas = _propuestas(oa)
    if not propuestas:
        return [{"estado": "pendiente", "codigo": None, "texto": "",
                 "motivo": "La guía no indica un objetivo de aprendizaje."}]
    niveles = niveles_de(cursos)
    registro = cargar()
    resultado = []
    for p in propuestas:
        codigo = p.get("codigo") or codigo_de(p.get("texto", ""))
        asig = p.get("asignatura", asignatura)
        candidatos = [r for r in registro if _norm(r["asignatura"]) == _norm(asig)
                      and r["nivel"] in (p.get("nivel") and [str(p["nivel"])] or niveles)
                      and r["codigo"] == codigo]
        if not codigo:
            resultado.append({"estado": "pendiente", "codigo": None, "texto": p.get("texto", ""),
                              "motivo": "No se indicó el número del OA."})
        elif not candidatos:
            resultado.append({"estado": "pendiente", "codigo": codigo, "texto": p.get("texto", ""),
                              "motivo": "No está en el registro de OA verificados con fuente oficial."})
        else:
            oficial = candidatos[0]
            texto_prop = re.sub(r"^\s*OA\s*\d+\s*(\([^)]*\))?\s*:?", "", p.get("texto", "")).strip()
            parecido = difflib.SequenceMatcher(None, _norm(texto_prop), _norm(oficial["texto"])).ratio()
            if texto_prop and parecido < SIMILITUD_MINIMA:
                resultado.append({"estado": "pendiente", "codigo": codigo, "texto": oficial["texto"],
                                  "fuente": oficial["fuente"],
                                  "motivo": "El texto escrito no coincide con el oficial; se usará el texto oficial tras confirmar."})
            else:
                resultado.append({"estado": "verificado", "codigo": codigo, "texto": oficial["texto"],
                                  "fuente": oficial["fuente"], "motivo": ""})
    return resultado
