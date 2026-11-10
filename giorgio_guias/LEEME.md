# GIORGIO GUÍAS

Sistema de cuatro agentes que fabrica guías escolares (Word y PDF) para la
**Escuela Rebeca Matte Bello**, Renca.

> Estado: **Etapa 4 lista (GG-001 y versión 2).** Extensión flexible, secuencia de
> 90 minutos, diagramación automática medida página por página y control de tiempo
> y nivel de pensamiento. Falta la interfaz con botones.
>
> 👉 Mira **`ejemplos/version_2/`**: guía, solucionario e `INFORME_CONTROL_CALIDAD.md`.
> La guía piloto original sigue intacta en `ejemplos/`.

## Reglas aprobadas

Están en `config/reglas_aprobadas.toml` y ARCHIVO las registra solas en la memoria.

- **GG-001 — Extensión flexible** (aprobada el 10-11-2026): mínimo 4 páginas carta vertical,
  sin máximo rígido; la extensión depende del contenido, las actividades, las imágenes y los
  espacios de respuesta.

## Los cuatro agentes

| Agente  | Trabajo        | Archivo                          |
|---------|----------------|----------------------------------|
| ATENEA  | Pedagogía      | `giorgio/agentes/atenea.py`      |
| BAUHAUS | Diseño         | `giorgio/agentes/bauhaus.py`     |
| REVISOR | Calidad        | `giorgio/agentes/revisor.py`     |
| ARCHIVO | Memoria        | `giorgio/agentes/archivo.py`     |

Cómo conversan entre ellos: ver `docs/comunicacion_agentes.md`.

## Cómo se crea una guía (modo manual)

1. **Claude Code escribe el contenido** (el trabajo de ATENEA) en un archivo de la
   carpeta `contenidos/`. Ejemplo: `contenidos/2026-11_historia_6C_ambientes_naturales.json`.
2. Se ejecuta:
   ```
   python crear_guia.py contenidos/2026-11_historia_6C_ambientes_naturales.json
   ```
3. Los agentes trabajan solos: ARCHIVO revisa lo anterior → ATENEA carga el contenido →
   BAUHAUS diseña Word y PDF → REVISOR controla → ARCHIVO guarda la guía aprobada.
4. Los documentos quedan en `salida/` y la copia aprobada en `datos/archivo/`.

Para probar sin guardar en el archivo, agrega `--prueba` al final.

## Comandos para el profesor

| Quiero...                                | Escribo                                                  |
|------------------------------------------|----------------------------------------------------------|
| Guardar el logo (una sola vez)           | `python recursos.py logo ruta/al/logo.png`               |
| Saber qué imágenes faltan                | `python recursos.py pendientes`                          |
| Incorporar fotos dejadas en `recursos/entrada/` | `python recursos.py importar`                     |
| Agregar una foto con su fuente           | `python recursos.py agregar foto.jpg --id nombre --fuente "..." --licencia "..."` |
| Ver los OA verificados                   | `python curriculo.py lista`                              |
| Ver correcciones propuestas              | `python memoria.py lista`                                |
| Aprobar una corrección para el futuro    | `python memoria.py aprobar 3`                            |
| Dar una indicación permanente            | `python memoria.py agregar "Usar ejemplos de Renca"`     |

Tus archivos originales **nunca se mueven ni se sobrescriben**: el sistema guarda copias.

## Qué revisa REVISOR automáticamente

- **Contenido:** las 9 secciones y el objetivo, con cantidad suficiente de preguntas.
- **Claridad y dificultad:** instrucciones con verbo de acción y no muy largas; legibilidad
  de la lectura según el nivel (índice INFLESZ); oraciones largas y palabras difíciles;
  preguntas dobles; alternativas repetidas o que delatan la respuesta; pistas que contienen
  la respuesta; palabras absolutas en verdadero o falso.
- **Imágenes:** faltantes (detienen la entrega y se piden), provisorias, sin fuente,
  de baja resolución o sin contraste para blanco y negro; logo ausente.
- **Diagramación:** páginas casi vacías, títulos sueltos al final de página, actividades
  fuera de orden, imágenes que no llegaron al PDF, exceso de páginas.
- **Objetivos de aprendizaje:** solo "verificado" si coincide con el registro oficial;
  si no, "pendiente de confirmación".
- **Lecciones aprobadas:** aplica las reglas que el profesor aprobó (ej.: palabras prohibidas).
- Selección única: exactamente 4 alternativas y respuestas que no sean siempre la misma letra.
- Verdadero o falso: que haya algunas falsas, con su corrección.
- Sopa de letras: busca cada palabra él mismo; debe aparecer **exactamente una vez**.
- Crucigrama: lee cada palabra letra por letra.
- **Tiempo (GG-001):** cada actividad trae sus minutos; deben sumar 90 y coincidir con el
  trabajo estimado (lectura, preguntas, líneas). Sopa + crucigrama no más del 25 % de la clase.
- **Nivel de pensamiento:** no más del 50 % de preguntas de solo recordar; debe haber análisis
  y aplicación.
- **Diagramación (medida en el PDF):** páginas casi vacías, desbordes, letra menor a 10 pt,
  títulos sueltos, sopa partida, crucigrama separado de sus pistas, imágenes repartidas o
  pequeñas, instrucciones separadas de su recuadro. Mínimo 4 páginas, sin máximo.
- Que el tema no repita una guía ya archivada para ese curso.

## Qué hay en cada carpeta

```
giorgio_guias/
├── ejemplos/          ← guía de muestra ya hecha (PDF y Word)
├── contenidos/        ← textos de cada guía (los escribe Claude Code)
├── crear_guia.py      ← la orden para fabricar una guía
├── herramientas/      ← dibujos de prueba
├── recursos.py / memoria.py / curriculo.py ← comandos del profesor
├── config/            ← AJUSTES que puedes editar (escuela, formato, 5 guías semanales)
├── giorgio/           ← el programa
│   ├── agentes/       ← un archivo por agente
│   ├── almacenamiento/← dónde se guardan las guías (hoy: tu PC; luego: Google Drive)
│   ├── expediente.py  ← la "carpeta" que los agentes se pasan
│   └── orquestador.py ← el director que decide quién trabaja y cuándo
├── interfaz/          ← (próxima etapa) ventana con botones
├── recursos/logo/     ← pon aquí el logo de la escuela
├── recursos/imagenes/ ← fotos, mapas e ilustraciones
├── datos/archivo/     ← guías aprobadas (no se suben a internet)
├── salida/            ← Word y PDF terminados (no se suben a internet)
├── tests/             ← pruebas automáticas
└── docs/              ← explicaciones
```

## Cómo probarlo en tu computador (cuando quieras)

1. Instala **Python** (python.org) y **LibreOffice** (libreoffice.org). Ambos gratis.
2. Abre una terminal en esta carpeta y escribe:
   ```
   python -m pip install -r requirements.txt
   python comprobar_entorno.py
   python -m pytest
   ```
3. Si ves `Todo listo.` y `64 passed`, todo funciona.

## Reglas de seguridad

No publica nada, no envía correos, no entra a Kimche, no usa servicios pagados
y no guarda datos de estudiantes (ver `config/sistema.toml`).
