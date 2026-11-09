# Objetivos de Aprendizaje verificados

`oa_verificados.json` contiene **solo** OA copiados desde una fuente oficial del
Currículum Nacional (Bases Curriculares / Programas de Estudio del Mineduc,
curriculumnacional.cl). Cada OA guarda su fuente y la fecha de verificación.

- ATENEA **no inventa** números de OA. Si un OA no está aquí, la guía lo marca
  como **"pendiente de confirmación"**.
- Para agregar un OA (desde un documento oficial):
  ```
  python curriculo.py agregar --asignatura "Historia, Geografía y Ciencias Sociales" --nivel 6 --codigo "OA 12" --texto "..." --fuente "Bases Curriculares 2012, Mineduc, p. X"
  ```
- El Proyecto de Regeneración es un proyecto de la escuela, no una asignatura del
  currículum nacional: se marca como "institucional" y puede vincularse a OA de
  otras asignaturas solo si están verificados.
