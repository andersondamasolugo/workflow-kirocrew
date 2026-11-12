# Prompt reutilizable — Implementar HU tipo "CRUD" completa (DB + BE + FE)

> Patrón derivado de la feature **"Parametrización de Diagnósticos CIE genéricos"** (módulo ARL,
> repos `san-andres-autorizaciones-ms` + `san-andres-autorizaciones-frontend` + `*-oracle-db`).
> Copia este archivo en un chat NUEVO (sin contexto previo) y reemplaza los `<...>` por los datos
> de tu HU. Si no conoces un dato, pídele al agente que lo lea de la HU/el molde antes de asumir.

---

## Datos de la HU (rellenar)

- **Clave HU** = `<ej. GD929-2765>`
- **`<ENTIDAD>`** = `<nombre del concepto de negocio, ej. "Código CUPS">`
- **Tabla Oracle** = `<GB_...>`  ·  **Secuencia** = `SEQ_<GB_...>`
- **Ruta FE** = `<ej. /arl/cups>`  ·  **Context-path BE** = `<ej. /api/v1/cups>`
- **Columnas de negocio** = `<lista: código, descripción, estado A/I, fecha efectiva, ...>`
- **Molde a replicar** = `<feature/tabla similar ya existente, ej. CIE genéricos / GB_PROGRAMA_CIE10>`

---

## Prompt (copiar a partir de aquí)

Soy de Seguros Bolívar. Tengo la HU `<CLAVE-HU>` que solo dice "CRUD de `<ENTIDAD>`" sin criterios
de aceptación claros. Quiero que la implementes **completa en las tres capas (Base de datos Oracle →
Backend Spring Boot → Frontend Angular)**, replicando **exactamente** el patrón de la feature
"Parametrización de Diagnósticos CIE genéricos" (módulo ARL).

**Reglas de trabajo (no negociables):**
- Explora primero el código real y un molde existente similar en el repo; **replica su patrón, no
  inventes uno nuevo**.
- Stack aprobado: Oracle (repo `*-oracle-db`, PR por DOFI), Spring Boot + JPA, Angular standalone
  con design system `sb-ui-*`.
- Verifica el build con la config real (`tsconfig.app.json` en FE; compilar + tests en BE). **No
  commitees sin mostrarme el delta y esperar mi OK.**
- Tests Given/When/Then, ≥80% cobertura de código propio, mock de todo backend.
- Gate OWASP sobre el diff: sin Critical/High. **Ataca la raíz, no el síntoma; no sobre-diseñes.**

### Entidad y alcance
- **`<ENTIDAD>`** = `<nombre>`
- **Tabla Oracle** = `<GB_...>` · **Ruta FE** = `<ruta>` · **Context-path BE** = `<path>`
- **Columnas** = `<lista>`

---

### CAPA 1 — Base de datos (repo `<...-oracle-db>`, PR por DOFI)

**AC-DB1 — Objetos nuevos replicando el molde** (`<tabla molde>`):
- Tabla `<GB_ENTIDAD>` con PK, columnas de negocio y **auditoría** (USR_CREACION, FEC_CREACION,
  USR_MODIFICACION, FEC_MODIFICACION).
- **Secuencia** `SEQ_<GB_ENTIDAD>` (MINVALUE 1, INCREMENT 1, CACHE 20).
- **Sinónimo público** de la tabla **y** de la secuencia (`CREATE PUBLIC SYNONYM`) — crítico: el
  microservicio se conecta con un usuario de aplicación y accede por sinónimo; sin él da `ORA-00942`.
- **Grants** replicando los del molde: SELECT/INSERT/UPDATE/DELETE a los roles de escritura, SELECT a
  los de lectura, SELECT de la secuencia a los roles de escritura.
- Un archivo por objeto en su carpeta de tipo (Secuencias/, Grants/, Tablas/); actualizar el
  ROLLBACK. Orden: Secuencia → Tabla → Índices → Sinónimos+Grants.

### CAPA 2 — Backend (microservicio Spring Boot)

**AC-BE1 — Entidad + repositorio JPA:** entidad `@Entity` mapeando `<GB_ENTIDAD>` con columnas exactas
y `@MappedSuperclass` de auditoría si el molde lo usa. Repositorio con `findAll(Pageable)`,
`findByStatus`, `findBy<Clave>`.

**AC-BE2 — Endpoints REST** bajo `<context-path>`:
- `GET` lista paginada (`Pageable`, soporta `?sort=`, filtro opcional por estado, cap de tamaño de
  página).
- `POST` crear/reactivar (si el par clave ya existe inactivo, reactiva en vez de insertar).
- `PATCH /{id}` **soft-delete** (estado A→I), nunca borrado físico.
- `POST /masivo` carga masiva por lotes (`REQUIRES_NEW` por lote, tope de filas).

**AC-BE3 — Validación y errores:** validación de negocio (formato, longitud, existencia); errores de
negocio con categoría/código; genéricos al cliente, detalle solo interno. DTOs, nunca exponer la
entidad cruda.

### CAPA 3 — Frontend (micro-front Angular `sb-ui`, 3 tabs)

Pantalla con título y **3 tabs** (patrón `sb-ui-tabs`):

**AC-FE1 — Tab Carga masiva:**
- "Descargar plantilla CSV" (cabeceras exactas separadas por `;` + fila de ejemplo, generado en
  cliente).
- Drag & drop + input que solo acepta `.csv`; rechaza otros con notificación.
- **Prevalidación client-side**: resumen (total/válidas/errores) + tabla de errores (fila, columna,
  valor, detalle); si hay ≥1 error, "Subir" deshabilitado (todo-o-nada).
- Subida por URL prefirmada S3; al terminar salta a Resultados.

**AC-FE2 — Tab Resultados:** tabla paginada de trazas (ID, fecha, nombre, estado, total/ok/fallidas,
descargar). Estado PROCESSING muestra `—` en conteos y oculta la descarga hasta terminar.

**AC-FE3 — Tab Gestión:**
- Tabla `sb-ui-table` con columnas de `<ENTIDAD>` + Acciones (editar/remover).
- Crear y Editar por modal (clave/identidad en solo lectura al editar).
- **Ordenamiento por columna** (header clicable, ícono ▲▼, ciclo asc→desc, aplica a todo el conjunto;
  columnas join/auditoría no ordenables).
- **Buscador global**: input que filtra por código, descripción y campos de texto (insensible a
  mayúsculas), en memoria, reset a página 0. Reemplaza cualquier select de filtro suelto.
- **Descargar CSV**: baja todos los registros (respetando buscador + orden) en el **mismo formato de
  la carga masiva** (re-subible). Fecha `DD/MM/YYYY` sin desfase de zona. **Anti-CSV-injection**:
  prefijar `'` a celdas que empiecen con `= + - @ tab CR`. BOM UTF-8 para acentos en Excel.
- **Confirmación obligatoria al eliminar**: todo borrado abre modal de confirmación
  (`app-modal-basic-confirmation`) y pasa por un **único** modal, desde la tabla **y** desde el botón
  "Remover" del modal de edición.

**AC-FE4 — No-funcionales:** componentes `standalone` + `OnPush` + señales, tipado estricto (sin
`any`), auditoría en el modelo aunque la columna se oculte en la grilla.

### Trampas aprendidas (evítalas)
- `app-modal-basic-confirmation` se controla con **`[customModalConfirm]="{ title, visible }"`**
  (objeto), NO con `[visible]`/`[title]` sueltos (no abre en runtime aunque compile y pase en jsdom).
- Abrir un `sb-ui-modal` justo tras cerrar otro: **diferir la apertura al siguiente tick
  (`setTimeout`)** o los dos modales se pisan y "no hace nada".
- Fechas ISO `yyyy-MM-dd`: parsear por partes, no `new Date('...')` (desfase GMT-5 retrocede el día).
- Que un PR de DB esté mergeado **no** significa que los objetos existan en el ambiente: el DDL se
  ejecuta aparte (pipeline/DBA). Verifícalo (`oracle_query` sobre `all_objects`/`all_synonyms`).
- La tabla de Gestión puede ser **server-side** (paginada) o **client-side** (cargar todo y filtrar
  en memoria, como el molde `programas-cie`): elige según el volumen del dataset.

### Orden de entrega
DB primero → BE después → FE al final. Sube todo primero a `develop` para probar en DEV antes de
stage/master. PR de DB por DOFI; BE y FE por el flujo normal GitHub (develop → stage → master).
