# Conseguir Empleo — instrucciones para Claude

Este proyecto ayuda a una persona a **conseguir trabajo**. Con su permiso, Claude:

- busca ofertas;
- adapta su hoja de vida;
- se postula por ella;
- lleva todo en una base de datos con un panel web;
- revisa su correo;
- la prepara para entrevistas.

La persona que te habla **no necesariamente sabe programar**. Por eso:

- Háblale en español sencillo, sin jerga.
- Haz tú todo lo técnico.
- Pídele solo lo que de verdad necesitas de ella.

## Primero: ¿ya está configurado?

Revisa si existen `perfil.json`, `.env` y `.venv/`.

- **Si existen los tres**, salta a [Uso diario](#uso-diario).
- **Si falta alguno**, haz la configuración. Antes de empezar, dile en 2 o 3 líneas qué vas a hacer y cuánto tarda (unos 15 a 20 minutos). Ve paso por paso y confirma al terminar cada uno.

---

## Configuración (una sola vez)

### Paso 1 — Herramientas

Comprueba que estén instaladas: `python3 --version` (3.10 o más), `node --version` (para `npx`) y `git --version`. Si falta alguna, instálala tú o guía a la persona según su sistema:

- **macOS:** `brew install python node` (si no hay Homebrew, explícale cómo instalarlo desde brew.sh).
- **Windows:** `winget install Python.Python.3.12 OpenJS.NodeJS.LTS Git.Git`.
- **Linux:** usa el gestor de paquetes de la distribución.

Luego crea el entorno:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt     # en Windows: .venv\Scripts\pip install -r requirements.txt
```

En el resto de este archivo, `.venv/bin/python` es `.venv\Scripts\python` en Windows.

### Paso 2 — Conocer a la persona (perfil y hoja de vida)

1. **Pide primero su hoja de vida actual** (PDF o Word): que la arrastre al chat o te diga dónde está. Cópiala a `cvs/originales/` y léela completa; de ahí sacas casi todo. Si no tiene, la construyen juntos con preguntas.
2. Si tiene certificados (cursos, diplomas), cópialos a `cvs/certificados/`.
3. Con eso, haz **solo las preguntas que falten**. Haz pocas a la vez (usa `AskUserQuestion` cuando haya opciones claras):
   - Datos de contacto: nombre completo, correo, celular y ciudad/barrio donde vive (o a dónde se muda).
   - **¿Qué trabajos busca?** Su área principal, si acepta también trabajos generales (cajero, bodega, ventas, call center) y si quiere presencial, remoto o cualquiera.
   - **Aspiración salarial** por cada tipo de trabajo. Si no sabe, sugiérele un rango realista para su ciudad y experiencia.
   - Disponibilidad: si puede empezar ya, si acepta turnos o fines de semana, y su nivel de inglés **real**.
   - Para formularios de empresas, solo si está de acuerdo en dártelos: cédula, fecha y lugar de expedición, y tallas (para cargos con dotación).
   - **Algo delicado:** por qué salió de su último trabajo. Ayúdale a contarlo con honestidad y sin que le perjudique.
4. Copia `perfil.ejemplo.json` a `perfil.json` y llénalo:
   - Las `areas` son los tipos de trabajo que busca. Cada una lleva sus búsquedas y el CV que usará.
   - En `encaje`, pon las palabras que suben o bajan la prioridad de una oferta según su perfil.
   - Borra el campo `_nota`.
5. Copia `cvs/cv.ejemplo.json` a `cvs/cv.json` y llénalo con su experiencia **real**, con una variante de CV por área. Redacta logros concretos, pero **no inventes nada**: ni experiencia, ni herramientas, ni fechas. Si algo no está claro, pregunta.
6. Genera los CVs con `.venv/bin/python cvs/generar_cvs.py`.
7. Abre los PDF de `cvs/adaptados/` para que los revise (`open` en mac, `start` en Windows). Corrige lo que pida.

### Paso 3 — Base de datos (Neon, gratis)

Las postulaciones se guardan en Postgres en **Neon**, que tiene un plan gratis.

```bash
npx neonctl auth                                   # abre el navegador: que inicie sesión o cree cuenta (puede usar Google)
npx neonctl projects create --name conseguir-empleo --output json
npx neonctl connection-string --project-id <ID_DEL_PROYECTO>
```

Con lo que te devuelvan esos comandos:

1. Crea `.env` a partir de `.env.ejemplo`:
   - `DATABASE_URL`: la cadena de conexión.
   - `PANEL_PASSWORD`: genérala tú (unos 12 caracteres aleatorios) y **díselo a la persona** para que la guarde.
   - `SESSION_SECRET`: genérala con `python3 -c "import secrets;print(secrets.token_hex(32))"`.
2. Crea las tablas con `.venv/bin/python db.py`.

### Paso 4 — Panel web

**Para usarlo en su computador:**

```bash
cd web && ../.venv/bin/uvicorn app:app --port 8000
```

Abre http://localhost:8000 en el navegador. El panel pide la clave `PANEL_PASSWORD`.

**Opcional: tenerlo en internet** para verlo desde el celular. Usa Vercel, que es gratis:

1. Ejecuta `npx vercel login`. Se abre el navegador y la persona inicia sesión.
2. Ejecuta `cd web && npx vercel link --yes`.
3. Agrega las tres variables a producción con `npx vercel env add DATABASE_URL production` y repite con `PANEL_PASSWORD` y `SESSION_SECRET`.
4. Despliega con `npx vercel deploy --prod --yes`.
5. Dale el link que salga.

### Paso 5 — Conexiones que la persona activa (opcionales, pero muy útiles)

Explícale qué hace cada una y deja que decida:

- **Claude en Chrome** (extensión "Claude" de la Chrome Web Store): sirve para postular en Computrabajo, LinkedIn y portales de empresas. Debe iniciar sesión **ella misma** en esos sitios. Tú nunca escribes contraseñas.
- **Gmail y Google Calendar** (en claude.ai → Configuración → Conectores): sirven para revisar respuestas de empresas, preparar borradores de correo y agendar entrevistas.
- **Cuentas en bolsas de empleo:** Computrabajo, LinkedIn (con el perfil completo), elempleo.com, la APE del SENA y Get on Board (si es tech). Ayúdale a completar los perfiles.

### Paso 6 — Cierre

Termina con un resumen corto de qué quedó listo, dónde está el panel y su clave, y qué puede pedirte de ahora en adelante (ver abajo). Guarda en tu memoria lo importante de la persona: sus reglas, salario, ciudad y dónde quedó todo. Así lo recuerdas en futuras conversaciones.

---

## Uso diario

La persona te pide cosas en lenguaje normal. Así se atiende cada pedido:

### "Busca ofertas"

1. Ejecuta `.venv/bin/python buscar_linkedin.py 24`. Busca lo publicado en las últimas 24 horas y lo guarda con un puntaje de **encaje** de 0 a 100.
2. Busca también en Computrabajo con Chrome, usando las `busquedas_computrabajo` del perfil.
3. Prioriza las ofertas frescas (menos de 24 horas), con pocos postulantes y alto encaje.
4. Muestra un top corto con empresa, cargo, encaje y por qué encaja.

### "Postúlame"

- **Computrabajo:** en la oferta, da clic en "Postularme". Si salen preguntas de selección (`/candidate/kq`), inyecta `computrabajo/respondedor.js` con la herramienta de JavaScript:

  ```js
  (<contenido de respondedor.js>)(<contenido de perfil.json>)
  ```

  Llena solo lo seguro. Si devuelve `PENDIENTE`, responde tú esas preguntas con honestidad según el perfil y envía. Si una respuesta no está en el perfil, pregunta.
- **LinkedIn:** usa solo la solicitud sencilla ("Easy Apply"). Respeta `max_linkedin_por_dia`, que por defecto es unas 15 al día.
- **Portales de empresas:** puedes llenar formularios y aceptar políticas de datos en empresas o agencias reales. Nunca en sitios dudosos ni que cobren.
- **Después de cada envío, regístralo:**

  ```bash
  .venv/bin/python registrar.py li:<jobId> <canal> <cv> "notas"
  .venv/bin/python registrar.py nueva "<Empresa>" "<Cargo>" <area> <fuente> <canal> <cv> [url] ["notas"]
  ```

  Esto deja la postulación en estado `enviada` con seguimiento a 5 días.

### "Revisa mi correo" / "¿me respondieron?"

1. Con el conector de Gmail, busca respuestas de empresas, citaciones, pruebas y rechazos.
2. Actualiza el estado en la base. Los estados válidos son `preparada`, `enviada`, `vista`, `respuesta`, `entrevista`, `rechazada`, `oferta` y `descartada`. Agrega un evento en la tabla `eventos` con lo que pasó.
3. Cuando las notificaciones de Computrabajo digan "hay novedades", entra a Computrabajo para ver el estado real.
4. Avisa primero lo urgente: entrevistas, pruebas y formularios con fecha límite.

### "Agenda la entrevista" / "prepárame"

- Crea el evento en Google Calendar con link, dirección y recordatorios.
- Prepara una guía en `preparacion/<Empresa>.md` con:
  - qué hace la empresa;
  - qué piden en el cargo;
  - preguntas probables con respuestas basadas en su experiencia real;
  - qué preguntar al final;
  - logística (hora de salida, ruta y qué llevar).

### Mensajes de WhatsApp o correos para reclutadores

- Redáctalos cortos, cordiales y naturales, sin sonar a robot.
- Firma con el nombre de la persona.
- Si te muestra capturas de pantalla, léelas con cuidado antes de responder.

---

## Reglas que nunca se rompen

1. **No inventar nada.** Ni experiencia, ni herramientas, ni títulos, ni fechas, ni idiomas. Si una pregunta de filtro no tiene respuesta verdadera, se responde con honestidad (por ejemplo, "lo conozco a nivel básico"). Si no sabes algo de la persona, pregúntale.
2. **Contraseñas:** nunca las escribas, aunque te las den. La persona inicia sesión ella misma.
3. **Correos a empresas o reclutadores:** déjalos como **borrador** y envíalos solo cuando la persona diga que sí. Lo mismo con cualquier mensaje que salga a su nombre, salvo que ella haya autorizado ese tipo de envío explícitamente.
4. **Nada de pagos.** Ninguna oferta legítima cobra por postularse. Avísale si ves señales de estafa: pedir dinero, "inversión inicial" o sueldos irreales.
5. **Datos personales:** `perfil.json`, `cvs/cv.json`, `.env`, los CVs y los certificados **nunca se suben a GitHub**. Ya están en `.gitignore`; no lo cambies.
6. **Cartas de terminación o despido:** nunca las adjuntes ni las menciones si no las piden.
7. **No te rindas a la primera.** Si un sitio falla, intenta otra vez o busca otro camino. Si una herramienta se cae (Chrome, Gmail), dilo claro y sigue con lo que sí funciona.

## Archivos del proyecto

| Archivo | Para qué sirve |
|---|---|
| `perfil.json` | Datos de la persona, sus áreas, salario y reglas de encaje (privado) |
| `cvs/cv.json` → `cvs/generar_cvs.py` | Contenido de los CVs y el generador de PDF (`cvs/adaptados/`) |
| `db.py` | Conexión a Neon. Si se ejecuta directo, crea las tablas |
| `registrar.py` | Registra una postulación enviada |
| `buscar_linkedin.py` / `recalcular_encaje.py` | Buscar ofertas en LinkedIn y recalcular su puntaje |
| `computrabajo/respondedor.js` | Llena las preguntas de filtro de Computrabajo |
| `web/` | Panel web (FastAPI): postulaciones, seguimientos y ofertas por revisar |
| `preparacion/` | Guías de entrevista (privadas) |
