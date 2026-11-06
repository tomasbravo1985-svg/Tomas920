# Bitácora Viva — app instalable (PWA)

Esta carpeta es el sitio que se publica en internet. Al abrirlo, se puede instalar como app en iPhone, Android, Windows, Mac y Chromebook. Al entrar, abre la Bitácora Viva de siempre (Apps Script) con la cuenta del colegio o como visitante.

- No cambia la app, los datos, la hoja de registro ni el enlace /exec.
- No contiene claves, tokens ni contraseñas. Solo trae las dos direcciones públicas de la app, en `config.js`.

## Paso 1 · Comprar el dominio (una vez al año)

1. Entra a **nic.cl** y busca `escuelaqueregenera.cl`. Si está libre, inscríbelo a tu nombre o al de la institución. Cuesta cerca de **$9.940 + IVA al año**; confirma la tarifa vigente en nic.cl.
2. Recomendación: usa **`app.escuelaqueregenera.cl`** para la app y deja `escuelaqueregenera.cl` libre para un sitio web de la iniciativa en el futuro.

## Paso 2 · Publicar esta carpeta en GitHub Pages (gratis, con HTTPS)

1. En **github.com**, crea un repositorio **público** llamado `bitacora-viva`.
2. Toca **Add file → Upload files** y arrastra **todo el contenido** de esta carpeta, no la carpeta misma. Luego toca **Commit changes**.
3. Ve a **Settings → Pages → Branch: main / (root) → Save**.
4. En un minuto, la app queda en `https://TU-USUARIO.github.io/bitacora-viva/`. Ya se puede probar e instalar.

## Paso 3 · Conectar el dominio

1. En nic.cl, en la zona DNS del dominio, crea un registro **CNAME**: nombre `app`, destino `TU-USUARIO.github.io`.
2. En GitHub, ve a **Settings → Pages → Custom domain**, escribe `app.escuelaqueregenera.cl` y guarda. GitHub crea solo el archivo `CNAME`.
3. Cuando aparezca disponible, marca **Enforce HTTPS**. Puede tardar unas horas.

> Instala la app **después** de conectar el dominio. Si se instala con la dirección de github.io y luego cambia, hay que reinstalarla.

## Actualizar

- Para cambiar los enlaces de la app, edita `config.js`.
- Para cambiar cualquier otro archivo, sube el archivo nuevo y cambia el texto `VERSION` en `sw.js`, por ejemplo `'2026-11-20.1'`. Las apps instaladas mostrarán **«Hay una versión nueva — Actualizar»**. No se pierde el avance de nadie, porque está en la app del colegio o en el dispositivo.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `index.html`, `lanzador.css`, `lanzador.js` | Portada con «Entrar con mi cuenta del colegio» y «Entrar como visitante» |
| `config.js` | Las dos direcciones públicas de la app |
| `manifest.webmanifest` | Nombre, colores, íconos y accesos directos de la app instalada |
| `sw.js` | Service worker: carga rápida, portada sin conexión y aviso de versión nueva |
| `icons/` | Íconos 192 y 512, adaptables (Android), Apple y favicon |
| `splash/` | Pantallas de inicio para iPhone y iPad |
| `instalar.html` | Guía de instalación para iPhone, Android y computador |
| `_headers` | Ajustes de caché si algún día se usa Netlify o Cloudflare (GitHub Pages lo ignora) |
