"""Comprueba que los agentes se pasan el expediente en el orden correcto.

Usamos agentes "de mentira" (simulados) porque los reales aún no están construidos.
"""
from giorgio.expediente import Encargo, Expediente
from giorgio.orquestador import producir_guia


class ArchivoFalso:
    def __init__(self):
        self.guardados = []

    def consultar(self, exp):
        exp.historial_previo = [{"tema": "Tema ya visto"}]
        exp.cambiar_estado("con_historial")
        exp.anotar("archivo", "atenea", "entrega", "Historial enviado")
        return exp

    def guardar(self, exp):
        self.guardados.append(exp)
        exp.cambiar_estado("archivado")
        return exp


class AteneaFalsa:
    def __init__(self):
        self.veces = 0

    def trabajar(self, exp):
        self.veces += 1
        exp.contenido = {"tema": "Tema nuevo", "version": self.veces}
        exp.cambiar_estado("planificado")
        exp.anotar("atenea", "bauhaus", "entrega", "Contenido listo")
        return exp


class BauhausFalso:
    def __init__(self):
        self.veces = 0

    def trabajar(self, exp):
        self.veces += 1
        exp.archivos = {"docx": "guia.docx", "pdf": "guia.pdf"}
        exp.cambiar_estado("disenado")
        exp.anotar("bauhaus", "revisor", "entrega", "Documento listo")
        return exp


class RevisorFalso:
    """Rechaza las primeras `rechazos` revisiones, culpando a `culpable`."""

    def __init__(self, rechazos=0, culpable="atenea"):
        self.rechazos = rechazos
        self.culpable = culpable

    def trabajar(self, exp):
        if self.rechazos > 0:
            self.rechazos -= 1
            exp.revision = {"aprobada": False, "observaciones": [
                {"responsable": self.culpable, "seccion": "crucigrama", "problema": "x"}]}
            exp.anotar("revisor", self.culpable, "solicitud_correccion", "Corregir")
        else:
            exp.revision = {"aprobada": True, "observaciones": []}
        return exp


def _encargo():
    return Encargo(asignatura="Historia", cursos=["6.º C"])


def test_camino_feliz_aprobada_a_la_primera():
    archivo, atenea, bauhaus = ArchivoFalso(), AteneaFalsa(), BauhausFalso()
    exp = producir_guia(_encargo(), archivo, atenea, bauhaus, RevisorFalso())
    assert exp.estado == "archivado"
    assert archivo.guardados == [exp]
    assert exp.historial_previo  # ATENEA recibió el historial
    remitentes = [m.de for m in exp.bitacora]
    assert remitentes == ["archivo", "atenea", "bauhaus"]


def test_revisor_pide_correccion_a_atenea():
    atenea, bauhaus = AteneaFalsa(), BauhausFalso()
    exp = producir_guia(_encargo(), ArchivoFalso(), atenea, bauhaus,
                        RevisorFalso(rechazos=1, culpable="atenea"))
    assert exp.estado == "archivado"
    assert atenea.veces == 2 and bauhaus.veces == 2
    assert exp.intentos_correccion == 1


def test_revisor_pide_correccion_solo_a_bauhaus():
    atenea, bauhaus = AteneaFalsa(), BauhausFalso()
    exp = producir_guia(_encargo(), ArchivoFalso(), atenea, bauhaus,
                        RevisorFalso(rechazos=1, culpable="bauhaus"))
    assert exp.estado == "archivado"
    assert atenea.veces == 1 and bauhaus.veces == 2


def test_si_no_se_arregla_avisa_al_profesor_y_no_archiva():
    archivo = ArchivoFalso()
    exp = producir_guia(_encargo(), archivo, AteneaFalsa(), BauhausFalso(),
                        RevisorFalso(rechazos=99), correcciones_maximas=2)
    assert exp.estado == "requiere_profesor"
    assert archivo.guardados == []
    assert exp.bitacora[-1].para == "profesor"


def test_expediente_se_puede_guardar_y_recuperar():
    exp = Expediente(encargo=_encargo())
    exp.anotar("atenea", "bauhaus", "entrega", "Hola")
    copia = Expediente.desde_json(exp.a_json())
    assert copia == exp
