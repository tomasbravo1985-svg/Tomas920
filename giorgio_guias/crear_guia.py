"""Crea UNA guía a partir de un archivo de contenido (modo manual).

Uso:
    python crear_guia.py contenidos/2026-11_historia_6C_ambientes_naturales.json
    python crear_guia.py contenidos/....json --prueba     (no la guarda en el archivo)
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

from giorgio import configuracion
from giorgio.agentes import Archivo, Atenea, Bauhaus, Revisor
from giorgio.almacenamiento.local import AlmacenLocal
from giorgio.expediente import Encargo
from giorgio.orquestador import producir_guia


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="GIORGIO GUÍAS: crear una guía")
    parser.add_argument("contenido", help="archivo .json de la carpeta contenidos/")
    parser.add_argument("--prueba", action="store_true", help="no guardar en el archivo de guías aprobadas")
    args = parser.parse_args()

    datos = json.loads(Path(args.contenido).read_text(encoding="utf-8"))
    encargo = Encargo(**datos["encargo"], fuente_contenido=str(Path(args.contenido).resolve()))
    sistema = configuracion.leer("sistema")
    almacen = AlmacenLocal(tempfile.mkdtemp()) if args.prueba else None

    exp = producir_guia(encargo, Archivo(almacen), Atenea(), Bauhaus(), Revisor(),
                        correcciones_maximas=sistema["revision"]["correcciones_maximas"])

    r = exp.revision
    print("\n=== GIORGIO GUÍAS ===")
    print(f"Guía: {exp.contenido.get('titulo')} · {encargo.asignatura} · {', '.join(encargo.cursos)}")
    print(f"Resultado: {exp.estado.upper()}  (correcciones realizadas: {exp.intentos_correccion})\n")
    print("REVISOR comprobó:")
    for x in r.get("comprobaciones", []):
        print("  [OK]", x)
    for x in r.get("observaciones", []):
        print(f"  [PROBLEMA para {x['responsable'].upper()}] {x['seccion']}: {x['problema']}")
    for x in r.get("advertencias", []):
        print("  [OJO]", x)
    print("\nArchivos:")
    for clave, ruta in exp.archivos.items():
        print(f"  {clave}: {ruta}")
    print("\nBitácora de los agentes:")
    for m in exp.bitacora:
        print(f"  {m.de.upper()} → {m.para.upper()} ({m.tipo}): {m.texto}")
    return 0 if exp.estado == "archivado" else 1


if __name__ == "__main__":
    raise SystemExit(main())
