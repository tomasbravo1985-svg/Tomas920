"""Banco de imágenes y logo de GIORGIO GUÍAS.

    python recursos.py pendientes                 ¿Qué imágenes faltan?
    python recursos.py importar                   Incorpora las fotos dejadas en recursos/entrada/
    python recursos.py logo  ruta/al/logo.png     Guarda el logo (una sola vez)
    python recursos.py agregar ruta/foto.jpg --id desierto_atacama --tipo fotografia
                         --descripcion "..." --fuente "Wikimedia Commons, autor X" --licencia "CC BY-SA 4.0"
    python recursos.py lista                      Todo el banco de imágenes
"""
import argparse
import sys

from giorgio import recursos


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Banco de imágenes de GIORGIO GUÍAS")
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("pendientes")
    sub.add_parser("importar")
    sub.add_parser("lista")
    lg = sub.add_parser("logo")
    lg.add_argument("archivo")
    ag = sub.add_parser("agregar")
    ag.add_argument("archivo")
    ag.add_argument("--id", required=True)
    ag.add_argument("--tipo", default="fotografia", choices=recursos.TIPOS)
    ag.add_argument("--descripcion", default="")
    ag.add_argument("--fuente", default="")
    ag.add_argument("--licencia", default="")
    ag.add_argument("--autor", default="")
    a = p.parse_args()

    if a.orden == "pendientes":
        faltan = recursos.pendientes()
        recursos.escribir_pedido()
        print(f"Imágenes pendientes o provisorias: {len(faltan)}")
        for f in faltan:
            print(f"  - {f['id']}  ({f['estado']}): {f.get('descripcion', '')}")
        print(f"\nDetalle: {recursos.PEDIDO}")
    elif a.orden == "importar":
        hechos = recursos.importar_entrada()
        print(f"Imágenes incorporadas: {', '.join(hechos) if hechos else 'ninguna'}")
        print("Recuerda anotar la fuente de cada una con 'agregar' si la conoces.")
    elif a.orden == "lista":
        for f in recursos.cargar().values():
            print(f"{f['id']:<25} {f['estado']:<11} {f.get('tipo', ''):<20} {f.get('fuente', '')}")
    elif a.orden == "logo":
        calidad = recursos.registrar_logo(a.archivo)
        print(f"Logo guardado en {recursos.LOGO}. Se usará en todas las guías.")
        for x in calidad["problemas"]:
            print("  Ojo:", x)
    else:
        f = recursos.registrar(a.archivo, a.id, a.tipo, a.descripcion, a.fuente, a.licencia, a.autor)
        print(f"Agregada: {f['id']} -> {f['archivo']} ({f['estado']})")
        for x in recursos.evaluar_calidad(recursos.ruta_de(a.id), 7.4)["problemas"]:
            print("  Ojo:", x)


if __name__ == "__main__":
    main()
