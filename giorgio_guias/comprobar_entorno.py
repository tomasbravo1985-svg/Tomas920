"""Revisa si tu computador tiene todo lo necesario. Uso:  python comprobar_entorno.py"""
import importlib
import shutil
import sys

ok = True


def revisar(nombre, condicion, ayuda):
    global ok
    print(("  [OK]    " if condicion else "  [FALTA] ") + nombre + ("" if condicion else f"  -> {ayuda}"))
    ok = ok and condicion


print("GIORGIO GUÍAS — revisión del computador\n")
revisar(f"Python {sys.version.split()[0]} (se necesita 3.11 o más)", sys.version_info >= (3, 11),
        "Instala Python desde python.org")
for modulo, paquete in [("docx", "python-docx"), ("PIL", "Pillow"), ("pypdf", "pypdf"), ("pytest", "pytest")]:
    try:
        importlib.import_module(modulo)
        revisar(paquete, True, "")
    except ImportError:
        revisar(paquete, False, "python -m pip install -r requirements.txt")
revisar("LibreOffice (para crear PDF)", bool(shutil.which("soffice") or shutil.which("libreoffice")),
        "Descarga gratis desde libreoffice.org")
print("\nTodo listo." if ok else "\nFaltan cosas: sigue las indicaciones de arriba.")
