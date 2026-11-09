"""Registro de Objetivos de Aprendizaje verificados.

    python curriculo.py lista
    python curriculo.py agregar --asignatura "..." --nivel 6 --codigo "OA 12" --texto "..." --fuente "..."
"""
import argparse
import sys

from giorgio import curriculo


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="OA verificados con fuente oficial")
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("lista")
    a = sub.add_parser("agregar")
    for campo in ("asignatura", "nivel", "codigo", "texto", "fuente"):
        a.add_argument(f"--{campo}", required=True)
    args = p.parse_args()
    if args.orden == "lista":
        registro = curriculo.cargar()
        if not registro:
            print("Todavía no hay OA verificados. Todos quedarán 'pendientes de confirmación'.")
        for r in registro:
            print(f"{r['asignatura']} {r['nivel']}.º · {r['codigo']}: {r['texto'][:80]}...  [{r['fuente']}]")
    else:
        r = curriculo.agregar(args.asignatura, args.nivel, args.codigo, args.texto, args.fuente)
        print(f"Agregado: {r['codigo']} ({r['asignatura']}, {r['nivel']}.º)")


if __name__ == "__main__":
    main()
