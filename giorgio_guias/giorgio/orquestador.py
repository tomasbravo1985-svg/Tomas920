"""EL ORQUESTADOR: el "director de orquesta" que dice quién trabaja y cuándo.

Recorrido de una guía:

    ARCHIVO.consultar  ->  ATENEA  ->  BAUHAUS  ->  REVISOR
                                ^           ^          |
                                |           |          | ¿aprobada?
                                +-----------+----------+  no: corrige quien corresponda
                                                       |
                                                       v  sí
                                                ARCHIVO.guardar

Si después de varias correcciones la guía sigue con problemas,
se detiene y marca "requiere_profesor" (nunca entrega algo malo en silencio).
"""
from __future__ import annotations

from .expediente import Encargo, Expediente


def producir_guia(encargo: Encargo, archivo, atenea, bauhaus, revisor,
                  correcciones_maximas: int = 2) -> Expediente:
    exp = Expediente(encargo=encargo)

    exp = archivo.consultar(exp)   # 1. ¿Qué se hizo antes? (para no repetir)
    exp = atenea.trabajar(exp)     # 2. Contenido pedagógico

    while True:
        exp = bauhaus.trabajar(exp)    # 3. Diseño + Word + PDF
        exp = revisor.trabajar(exp)    # 4. Control de calidad

        if exp.revision.get("aprobada"):
            exp.cambiar_estado("aprobado")
            return archivo.guardar(exp)  # 5. Guardar la versión aprobada

        # Cada observación indica quién debe corregirla.
        responsables = {o["responsable"] for o in exp.revision.get("observaciones", [])}
        # Si nadie de los agentes puede arreglarlo (ej.: falta una foto), no tiene sentido insistir.
        se_puede_corregir = responsables & {"atenea", "bauhaus"}
        if exp.intentos_correccion >= correcciones_maximas or not se_puede_corregir:
            exp.cambiar_estado("requiere_profesor")
            exp.anotar("orquestador", "profesor", "aviso",
                       "La guía no pasó la revisión. Revisa las observaciones.")
            if hasattr(archivo, "registrar_intento"):
                archivo.registrar_intento(exp)   # ARCHIVO anota los problemas para aprender
            return exp

        exp.intentos_correccion += 1
        exp.cambiar_estado("con_observaciones")
        if "atenea" in responsables:
            exp = atenea.trabajar(exp)   # ATENEA corrige el contenido
        # BAUHAUS siempre vuelve a diseñar al inicio de la siguiente vuelta.
