# GIORGIO GUÍAS

Sistema de cuatro agentes que fabrica guías escolares (Word y PDF) para la
**Escuela Rebeca Matte Bello**, Renca.

> Estado: **Etapa 1 lista (estructura).** Los agentes existen como "esqueletos":
> ya saben cómo comunicarse, pero todavía no escriben ni diseñan guías.

## Los cuatro agentes

| Agente  | Trabajo        | Archivo                          |
|---------|----------------|----------------------------------|
| ATENEA  | Pedagogía      | `giorgio/agentes/atenea.py`      |
| BAUHAUS | Diseño         | `giorgio/agentes/bauhaus.py`     |
| REVISOR | Calidad        | `giorgio/agentes/revisor.py`     |
| ARCHIVO | Memoria        | `giorgio/agentes/archivo.py`     |

Cómo conversan entre ellos: ver `docs/comunicacion_agentes.md`.

## Qué hay en cada carpeta

```
giorgio_guias/
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
3. Si ves `Todo listo.` y `12 passed`, todo funciona.

## Reglas de seguridad

No publica nada, no envía correos, no entra a Kimche, no usa servicios pagados
y no guarda datos de estudiantes (ver `config/sistema.toml`).
