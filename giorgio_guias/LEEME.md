# GIORGIO GUÍAS

Sistema de cuatro agentes que fabrica guías escolares (Word y PDF) para la
**Escuela Rebeca Matte Bello**, Renca.

> Estado: **Etapa 2 lista (modo manual).** Los cuatro agentes funcionan y crean
> una guía completa en Word y PDF, con su solucionario. Falta la interfaz con botones.
>
> 👉 Mira el resultado en la carpeta **`ejemplos/`** (guía de Historia 6.º C).

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

## Qué revisa REVISOR automáticamente

- Que estén las 9 secciones y el objetivo, con cantidad suficiente de preguntas.
- Selección única: exactamente 4 alternativas y respuestas que no sean siempre la misma letra.
- Verdadero o falso: que haya algunas falsas, con su corrección.
- Sopa de letras: busca cada palabra él mismo; debe aparecer **exactamente una vez**.
- Crucigrama: lee cada palabra letra por letra.
- Tamaño carta vertical, mínimo 4 caras y ninguna página casi vacía.
- Que el tema no repita una guía ya archivada para ese curso.

## Qué hay en cada carpeta

```
giorgio_guias/
├── ejemplos/          ← guía de muestra ya hecha (PDF y Word)
├── contenidos/        ← textos de cada guía (los escribe Claude Code)
├── crear_guia.py      ← la orden para fabricar una guía
├── herramientas/      ← dibujos de prueba
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
3. Si ves `Todo listo.` y `39 passed`, todo funciona.

## Reglas de seguridad

No publica nada, no envía correos, no entra a Kimche, no usa servicios pagados
y no guarda datos de estudiantes (ver `config/sistema.toml`).
