"""Crea UNA guía a partir de un archivo de contenido (modo manual).

Uso:
    python crear_guia.py contenidos/2026-11_historia_6C_ambientes_naturales.json
    python crear_guia.py contenidos/....json --prueba     (no guarda nada en el archivo ni en la memoria)
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from giorgio import configuracion, memoria
from giorgio.agentes import Archivo, Atenea, Bauhaus, Revisor
from giorgio.almacenamiento.local import AlmacenLocal
from giorgio.expediente import Encargo
from giorgio.orquestador import producir_guia


ESTADOS = {"archivado": "✅ APROBADA Y GUARDADA", "requiere_profesor": "⚠️ NECESITA TU REVISIÓN"}


def escribir_informe(exp) -> Path | None:
    """Informe de control de calidad en lenguaje sencillo, junto a la guía."""
    from giorgio import tiempos
    from giorgio.configuracion import leer

    carpeta = exp.archivos.get("carpeta")
    if not carpeta:
        return None
    r, c = exp.revision, exp.contenido
    titulos = {x["id"]: x["titulo"] for x in leer("formato_guia")["secciones"]}
    version = f" (versión {c['version']})" if c.get("version") else ""
    L = [f"# Informe de control de calidad — {c.get('titulo', '')}{version}", "",
         f"**{', '.join(exp.encargo.cursos)} · {exp.encargo.asignatura}** · {exp.encargo.fecha}", "",
         f"## Resultado: {ESTADOS.get(exp.estado, exp.estado)}", ""]
    if r.get("observaciones"):
        L += ["## Problemas que impiden entregar", ""]
        L += [f"- **{o['responsable'].upper()}** ({o['seccion']}): {o['problema']}" for o in r["observaciones"]]
        L.append("")
    if c.get("cambios_v2") or c.get("cambios"):
        L += [f"## Cambios respecto de {c.get('basada_en', 'la versión anterior')}", ""]
        L += [f"- {x}" for x in c.get("cambios_v2") or c.get("cambios")]
        L.append("")

    gg = [l for l in exp.lecciones if l.get("codigo")]
    if gg:
        L += ["## Reglas aprobadas aplicadas", ""]
        L += [f"- **{l['codigo']}** ({l.get('categoria')}, aprobada el {l.get('fecha_aprobacion')})" for l in gg]
        m = exp.diseno.get("maqueta", {})
        if m.get("probadas"):
            L.append(f"- BAUHAUS probó {m['probadas']} distribuciones y eligió la que empieza página nueva en: "
                     f"{', '.join(titulos.get(x, x) for x in m['saltos']) or 'ninguna'} ({m['paginas']} páginas).")
        L.append("")

    secuencia = c.get("secuencia", {})
    if secuencia:
        estimados = tiempos.estimar(c)
        L += ["## Tiempo de la clase (90 minutos)", "",
              "| Actividad | Minutos asignados | Trabajo estimado | Habilidad |", "|---|---|---|---|"]
        for sec, d in secuencia.items():
            L.append(f"| {titulos.get(sec, sec)} | {d.get('minutos')} | {estimados.get(sec, '')} | {d.get('habilidad', '')} |")
        L.append(f"| **Total** | **{sum(d.get('minutos', 0) for d in secuencia.values())}** | "
                 f"**{round(sum(estimados.values()))}** | |")
        L += ["", "_El trabajo estimado es una referencia según la cantidad de lectura, preguntas y líneas de respuesta._", ""]

    dist = tiempos.distribucion(c)
    L += ["## Nivel de pensamiento de las consignas", "",
          " · ".join(f"{n.capitalize()}: {int(dist[n] * 100)} %" for n in tiempos.NIVELES) + f"  ({dist['total']} consignas)", ""]
    if r.get("advertencias"):
        L += ["## Pendientes y advertencias (no impiden entregar)", ""]
        L += [f"- {a}" for a in r["advertencias"]]
        L.append("")
    L += ["## Controles superados", ""] + [f"- ✔ {x}" for x in r.get("comprobaciones", [])]
    L += ["", "_La aprobación exige pasar TODOS los controles: cumplir el número de páginas no basta (GG-001)._"]
    ruta = Path(carpeta) / "INFORME_CONTROL_CALIDAD.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return ruta


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="GIORGIO GUÍAS: crear una guía")
    parser.add_argument("contenido", help="archivo .json de la carpeta contenidos/")
    parser.add_argument("--prueba", action="store_true", help="no guardar en el archivo de guías aprobadas")
    args = parser.parse_args()

    datos = json.loads(Path(args.contenido).read_text(encoding="utf-8"))
    encargo = Encargo(**datos["encargo"], fuente_contenido=str(Path(args.contenido).resolve()))
    sistema = configuracion.leer("sistema")
    almacen = None
    if args.prueba:  # modo prueba: archivo y memoria en copias temporales (lo real no cambia)
        temporal = Path(tempfile.mkdtemp())
        almacen = AlmacenLocal(temporal / "archivo")
        copia = temporal / "correcciones.json"
        if memoria.ARCHIVO_MEMORIA.is_file():
            shutil.copy2(memoria.ARCHIVO_MEMORIA, copia)
        memoria.ARCHIVO_MEMORIA = copia
        memoria.LECCIONES_MD = temporal / "LECCIONES_APROBADAS.md"

    exp = producir_guia(encargo, Archivo(almacen), Atenea(), Bauhaus(), Revisor(),
                        correcciones_maximas=sistema["revision"]["correcciones_maximas"])

    r = exp.revision
    informe = escribir_informe(exp)
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
    if informe:
        print(f"\nInforme completo: {informe}")
    print("\nBitácora de los agentes:")
    for m in exp.bitacora:
        print(f"  {m.de.upper()} → {m.para.upper()} ({m.tipo}): {m.texto}")
    return 0 if exp.estado == "archivado" else 1


if __name__ == "__main__":
    raise SystemExit(main())
