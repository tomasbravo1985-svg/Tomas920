# Inventario de recursos pendientes — GIORGIO GUÍAS

Actualizado: 10-11-2026 · Guía afectada: Historia 6.º C, guía 1 (versión 2)

| # | Recurso | Estado | ¿Lo puedo obtener solo? | Qué necesito de ti |
|---|---|---|---|---|
| 1 | **Logo institucional** | ✅ **RECIBIDO** (10-11-2026) | — | Nada. Quedó guardado una vez en `recursos/logo/` y se usará automáticamente desde la próxima versión. |
| 2 | **Documento curricular oficial** (Historia 6.º básico, para confirmar el OA 12) | ⏳ Pendiente | ❌ **No por ahora.** curriculumnacional.cl ya está autorizado en el entorno, pero el sitio no responde a conexiones desde servidores externos (probado el 10-11-2026). | El **PDF del Programa de Estudio o de las Bases Curriculares** de Historia, Geografía y Ciencias Sociales 6.º básico, descargado desde tu computador. |
| 3 | Fotografía: **desierto de Atacama** | ⏳ Provisoria (dibujo) | ⚠️ **Sí, si autorizas Wikimedia Commons** (fotos con licencia libre). Hoy está bloqueado. | Tu autorización para Wikimedia, **o** la foto. |
| 4 | Fotografía: **valle de la zona central** | ⏳ Provisoria (dibujo) | ⚠️ Igual que la anterior | Igual que la anterior |
| 5 | Fotografía: **bosque lluvioso del sur** | ⏳ Provisoria (dibujo) | ⚠️ Igual que la anterior | Igual que la anterior |
| 6 | Fotografía: **glaciar o paisaje antártico** | ⏳ Provisoria (dibujo) | ⚠️ Igual que la anterior | Igual que la anterior |

## Detalle

### 1. Logo institucional — recibido
- Se recibió una imagen PNG de 3796 × 4000 píxeles con **fondo transparente**. Para imprimir se
  usa sobre fondo blanco, en escala de grises.
- Se guardó **una copia** de 1200 píxeles de ancho, suficiente para imprimirlo nítido a 2,6 cm.
  El archivo original no se modificó.
- En blanco y negro, el azul del escudo queda casi negro y las letras blancas se leen bien.
  La imagen original es algo borrosa porque viene ampliada; si existe una versión de mejor
  calidad, se puede reemplazar con `python recursos.py logo archivo.png` (el logo anterior se conserva).
- **La versión 2 no se modificó.** El logo aparecerá desde la próxima versión que se genere.

### 2. Documento curricular oficial
- Sitio probado: `www.curriculumnacional.cl`. El entorno lo permite, pero el servidor del sitio
  no contesta. Lo más probable es que bloquee conexiones de servidores que no están en Chile.
- **Opción recomendada:** descarga el PDF desde tu computador y súbelo a
  `giorgio_guias/recursos/entrada/` (o adjúntalo en el chat). Con él registro el OA exacto
  con su número de página: `python curriculo.py agregar ...`.
- Mientras tanto, el OA 12 sigue **PENDIENTE DE CONFIRMACIÓN** y no se imprime en la guía del estudiante.

### 3 a 6. Fotografías geográficas
- **Fuente pública sugerida:** Wikimedia Commons. Sus fotos tienen licencias libres (CC BY,
  CC BY-SA o dominio público) que **exigen citar al autor**; el sistema ya imprime la fuente bajo cada imagen.
- **Para que yo las obtenga solo:** hay que autorizar en el entorno estos dos sitios:
  `commons.wikimedia.org` (búsqueda y datos de licencia) y `upload.wikimedia.org` (descarga de la foto).
  Hoy están bloqueados (probado el 10-11-2026).
- **Si prefieres entregarlas tú:** déjalas en `recursos/entrada/` con estos nombres exactos y
  ejecuta `python recursos.py importar`:
  - `paisaje_desierto.jpg`
  - `paisaje_mediterraneo.jpg`
  - `paisaje_lluvioso.jpg`
  - `paisaje_polar.jpg`
- **Requisitos:** al menos 1200 píxeles de ancho, nítidas y con buen contraste (se imprimen en
  blanco y negro). Anota de dónde salió cada foto.
- El detalle de cada foto (qué debe mostrar y dónde buscarla) está en `recursos/entrada/PEDIDO_DE_IMAGENES.md`.

## Resumen

| Puedo obtenerlo automáticamente | Necesito que tú lo entregues o lo autorices |
|---|---|
| Fotografías: **sí**, desde Wikimedia Commons, **si autorizas** los 2 sitios | **Documento curricular**: el sitio oficial no responde desde aquí; necesito el PDF |
| — | Logo: **ya recibido** |
