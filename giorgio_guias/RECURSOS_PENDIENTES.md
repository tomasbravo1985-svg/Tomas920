# Inventario de recursos pendientes — GIORGIO GUÍAS

Actualizado: 11-11-2026 (todos los recursos recibidos) · Guía afectada: Historia 6.º C, guía 1 (versión 2)

| # | Recurso | Estado | ¿Lo puedo obtener solo? | Qué necesito de ti |
|---|---|---|---|---|
| 1 | **Logo institucional** | ✅ **RECIBIDO** (10-11-2026) | — | Nada. Quedó guardado una vez en `recursos/logo/` y se usará automáticamente desde la próxima versión. |
| 2 | **Documento curricular oficial** (Historia 6.º básico) | ✅ **RECIBIDO** (11-11-2026, vía Google Drive) | — | Nada. Se registraron los OA 1 a 24 de Historia 6.º con su página. |
| 3 | Fotografía: **desierto de Atacama** | ✅ **OBTENIDA** (Wikimedia Commons, ESO, CC BY 4.0) | ✅ Sí (autorizado el 10-11-2026) | Nada. Revisar si te parece adecuada. |
| 4 | Fotografía: **valle de la zona central** | ✅ **OBTENIDA** (Beatrice Murch, CC BY-SA 2.0) | ✅ Sí | Nada. |
| 5 | Fotografía: **bosque lluvioso del sur** | ✅ **OBTENIDA** (LBM1948, CC BY-SA 4.0) | ✅ Sí | Nada. |
| 6 | Fotografía: **glaciar / paisaje polar** | ✅ **OBTENIDA** (Diego Delso, CC BY-SA 3.0) | ✅ Sí | Nada. |

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

### 2. Documento curricular oficial — recibido
- Documento: *Bases Curriculares Primero a Sexto Básico*, Ministerio de Educación
  (Decretos Supremos de Educación N.º 433 y 439 de 2012). Archivo `articles-22394_bases.pdf`,
  414 páginas, entregado por el profesor vía Google Drive el 11-11-2026.
- Se registraron **24 OA de Historia, Geografía y Ciencias Sociales 6.º básico** (pp. 176-178),
  copiados palabra por palabra, en `config/curriculo/oa_verificados.json`. El documento fuente
  quedó anotado en `config/curriculo/fuentes.json`, con su huella digital.
- **OA 12 VERIFICADO** (p. 177, eje Geografía). Su texto oficial termina en "*…para vivir y
  desarrollarse*". La versión 3 de la guía usa este texto exacto.
- Pendiente para más adelante: registrar los OA de **Tecnología 6.º** (están en este mismo documento).

### 3 a 6. Fotografías geográficas — obtenidas
- Autorizaste Wikimedia Commons el 10-11-2026. Se agregaron al entorno `commons.wikimedia.org`
  y `upload.wikimedia.org`.
- Las 4 fotos se eligieron mirándolas, de 1920 px de ancho, y se revisó cómo quedan en
  **blanco y negro**: todas son nítidas y con buen contraste.
- Solo licencias libres que permiten adaptar (se convierten a gris): **CC BY y CC BY-SA**.
  El autor y la licencia quedan en `recursos/catalogo.json` y en `recursos/CREDITOS_IMAGENES.md`.
  BAUHAUS imprime el crédito bajo cada imagen.
- Primero se probó una panorámica de 360° del desierto, pero tenía el suelo deformado y se
  reemplazó. La anterior se conserva como copia; no se borró nada.
- Los 4 dibujos provisorios siguen guardados en `recursos/imagenes/*.png`.
- **Ojo para la versión 3:** el solucionario de la imagen A dice "cactus", y la foto real del
  desierto no tiene cactus. Muestra cerros áridos y rocas sin vegetación. Hay que ajustar esa
  respuesta esperada.
- Herramienta reutilizable para futuras guías: `python herramientas/wikimedia.py <id> "File:Nombre.jpg"`.
- **Nota técnica:** Wikimedia limita las consultas desde servidores compartidos (error 429).
  La herramienta espera y reintenta sola, sin insistir en exceso.

## Resumen

| Recurso | Estado |
|---|---|
| Logo | ✅ Recibido |
| 4 fotografías | ✅ Obtenidas desde Wikimedia Commons, con créditos |
| Documento curricular | ✅ Recibido; OA 12 verificado |
