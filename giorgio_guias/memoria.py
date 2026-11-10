"""Memoria de correcciones (la administra ARCHIVO).

    python memoria.py lista                       Ver propuestas y aprobadas
    python memoria.py aprobar 3                   Aprobar la corrección #3 (como nota para los agentes)
    python memoria.py aprobar 3 --regla max_palabras_oracion --valor 18
    python memoria.py descartar 3
    python memoria.py agregar "Usar ejemplos de Renca en la actividad inicial"
    python memoria.py agregar "No usar la palabra fácil" --regla palabras_prohibidas --valor "fácil,obvio"
    python memoria.py reglas                      Ver los tipos de reglas automáticas
"""
import argparse
import sys

from giorgio import memoria


def _regla(tipo, valor):
    if not tipo:
        return None
    if tipo == "palabras_prohibidas":
        return {"tipo": tipo, "valor": [v.strip() for v in (valor or "").split(",") if v.strip()]}
    if tipo == "nota":
        return {"tipo": "nota"}
    return {"tipo": tipo, "valor": int(valor)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Correcciones aprobadas para futuras guías")
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("lista")
    sub.add_parser("reglas")
    for nombre in ("aprobar", "descartar"):
        s = sub.add_parser(nombre)
        s.add_argument("id", type=int)
        if nombre == "aprobar":
            s.add_argument("--regla", choices=list(memoria.REGLAS))
            s.add_argument("--valor")
    ag = sub.add_parser("agregar")
    ag.add_argument("texto")
    ag.add_argument("--agente", default="atenea", choices=["atenea", "bauhaus", "revisor"])
    ag.add_argument("--regla", choices=list(memoria.REGLAS))
    ag.add_argument("--valor")
    ag.add_argument("--asignatura", default="")
    a = p.parse_args()

    if a.orden == "lista":
        lista = memoria.cargar()
        if not lista:
            print("La memoria está vacía.")
        for estado in ("propuesta", "aprobada", "descartada"):
            grupo = [c for c in lista if c["estado"] == estado]
            if grupo:
                print(f"\n== {estado.upper()}S ({len(grupo)}) ==")
            for c in grupo:
                regla = c.get("regla") or {}
                extra = f"  [regla: {regla.get('tipo')} = {regla.get('valor')}]" if regla.get("valor") is not None else ""
                print(f"  {c.get('codigo') or '#' + str(c['id'])} {c['agente'].upper()} · {c['categoria']}: {c['descripcion']} (vista {c.get('veces', 1)} vez/veces){extra}")
    elif a.orden == "reglas":
        for k, v in memoria.REGLAS.items():
            print(f"  {k}: {v}")
    elif a.orden == "aprobar":
        c = memoria.aprobar(a.id, _regla(a.regla, a.valor))
        print(f"Aprobada #{c['id']}: se aplicará en las próximas guías.")
    elif a.orden == "descartar":
        memoria.descartar(a.id)
        print(f"Descartada #{a.id}.")
    else:
        c = memoria.agregar_del_profesor(a.texto, a.agente, _regla(a.regla, a.valor), a.asignatura)
        print(f"Agregada y aprobada #{c['id']}.")


if __name__ == "__main__":
    main()
