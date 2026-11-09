# Cómo se comunican los cuatro agentes

## La idea en una frase

Los agentes **no hablan directamente entre ellos**. Se pasan una misma
**carpeta** (el *expediente*), y un **director** (el *orquestador*) decide a
quién le toca.

## El recorrido de una guía

```
 Profesor pide una guía (encargo)
            │
            ▼
 1. ARCHIVO consulta ──► "En 6.º C ya se vio X e Y"
            │
            ▼
 2. ATENEA planifica ──► objetivo, lectura, preguntas, palabras, respuestas
            │
            ▼
 3. BAUHAUS diseña ◄──────────────┐  ──► Word + PDF, sopa de letras, crucigrama
            │                     │
            ▼                     │
 4. REVISOR revisa                │
       ¿Está bien?                │
        │      └── NO ──► corrige ATENEA (contenido) y/o BAUHAUS (diseño)
        │ SÍ                      (máximo 2 vueltas; si no, avisa al profesor)
        ▼
 5. ARCHIVO guarda la guía aprobada (curso / asignatura / fecha)
```

## Qué contiene el expediente

| Parte              | Quién la escribe | Qué guarda                                  |
|--------------------|------------------|---------------------------------------------|
| `encargo`          | Profesor         | asignatura, cursos, tema, fecha, 90 min     |
| `historial_previo` | ARCHIVO          | guías anteriores, para no repetir           |
| `contenido`        | ATENEA           | todas las secciones de la guía + respuestas |
| `archivos`         | BAUHAUS          | rutas del Word y del PDF                    |
| `revision`         | REVISOR          | aprobada sí/no + lista de observaciones     |
| `bitacora`         | Todos            | notitas: quién entregó qué a quién          |
| `estado`           | Todos            | en qué paso va la guía                      |

## Cómo pide correcciones el REVISOR

Cada observación dice **quién** debe arreglarla:

```json
{"responsable": "bauhaus", "seccion": "crucigrama", "problema": "La palabra MAPUCHE no cabe"}
```

Si el responsable es `atenea`, ella reescribe el contenido. BAUHAUS siempre
vuelve a diseñar después. Así nadie trabaja de más.

## Por qué así

- **Sencillo:** un solo camino, fácil de seguir y de probar.
- **Seguro:** si la guía no pasa la revisión, no se entrega en silencio.
- **Ampliable:** el expediente se guarda como texto (JSON); el día que se
  conecte Google Drive, solo cambia el almacén, no los agentes.

Las pruebas de `tests/test_comunicacion.py` comprueban este recorrido.
