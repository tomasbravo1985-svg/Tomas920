"""BAUHAUS — DISEÑO.

Recibe: exp.contenido (de ATENEA).
Entrega: exp.archivos = {"docx": ruta, "pdf": ruta} y las cuadrículas generadas.

Responsabilidades:
- Aplicar el formato institucional (config/escuela.toml y config/formato_guia.toml).
- Tamaño carta, vertical, mínimo 4 caras, espacios amplios para escribir.
- Generar sopas de letras y crucigramas CON su solución.
- Imágenes en escala de grises aptas para impresión.
- Exportar Word (python-docx) y PDF (LibreOffice, gratuito).
"""
from .base import Agente


class Bauhaus(Agente):
    nombre = "bauhaus"
