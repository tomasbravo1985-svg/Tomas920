"""EL EXPEDIENTE: la "carpeta" que los agentes se van pasando de mano en mano.

Imagina una carpeta física que recorre la sala de profesores:
- ARCHIVO anota qué guías se hicieron antes.
- ATENEA escribe el contenido pedagógico.
- BAUHAUS lo convierte en Word y PDF.
- REVISOR lo revisa y deja observaciones.
- ARCHIVO guarda la versión aprobada.

Cada agente lee la carpeta, agrega su parte y la entrega al siguiente.
Además, cada uno deja una nota en la "bitácora" para saber qué pasó.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date

# Estados posibles de un expediente, en el orden normal del trabajo.
ESTADOS = (
    "nuevo",
    "con_historial",       # ARCHIVO ya consultó lo hecho antes
    "planificado",         # ATENEA ya escribió el contenido
    "disenado",            # BAUHAUS ya creó Word y PDF
    "con_observaciones",   # REVISOR pidió correcciones
    "aprobado",            # REVISOR aprobó
    "archivado",           # ARCHIVO guardó la guía final
    "requiere_profesor",   # Se agotaron los intentos: decide el profesor
)

# Tipos de mensajes que se pueden dejar en la bitácora.
TIPOS_MENSAJE = ("entrega", "solicitud_correccion", "aviso")


@dataclass
class Mensaje:
    de: str
    para: str
    tipo: str
    texto: str


@dataclass
class Encargo:
    """Lo que pide el profesor: qué guía hay que hacer."""
    asignatura: str
    cursos: list[str]
    numero: int = 1
    tema: str = ""                 # opcional: si se deja vacío, ATENEA propone uno
    fecha: str = field(default_factory=lambda: date.today().isoformat())
    duracion_minutos: int = 90
    fuente_contenido: str = ""     # modo manual: archivo de contenidos/ escrito por Claude Code


@dataclass
class Expediente:
    encargo: Encargo
    estado: str = "nuevo"
    historial_previo: list[dict] = field(default_factory=list)  # lo llena ARCHIVO
    lecciones: list[dict] = field(default_factory=list)         # lo llena ARCHIVO: correcciones aprobadas
    contenido: dict = field(default_factory=dict)               # lo llena ATENEA
    diseno: dict = field(default_factory=dict)                  # lo llena BAUHAUS: sopa y crucigrama
    archivos: dict = field(default_factory=dict)                # lo llena BAUHAUS: {"docx": ..., "pdf": ...}
    revision: dict = field(default_factory=dict)                # lo llena REVISOR
    intentos_correccion: int = 0
    bitacora: list[Mensaje] = field(default_factory=list)

    def anotar(self, de: str, para: str, tipo: str, texto: str) -> None:
        if tipo not in TIPOS_MENSAJE:
            raise ValueError(f"Tipo de mensaje desconocido: {tipo}")
        self.bitacora.append(Mensaje(de, para, tipo, texto))

    def cambiar_estado(self, nuevo: str) -> None:
        if nuevo not in ESTADOS:
            raise ValueError(f"Estado desconocido: {nuevo}")
        self.estado = nuevo

    # --- Guardar y leer como texto JSON (para el archivo y para Google Drive) ---
    def a_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def desde_json(cls, texto: str) -> "Expediente":
        datos = json.loads(texto)
        datos["encargo"] = Encargo(**datos["encargo"])
        datos["bitacora"] = [Mensaje(**m) for m in datos["bitacora"]]
        return cls(**datos)
