---
inclusion: fileMatch
fileMatchPattern: ["**/*.sql", "**/migrations/**", "**/db/**"]
---

# Reglas SQL (diseño, consultas y migraciones)

## Estilo
- Palabras clave en MAYÚSCULAS (`SELECT`, `FROM`, `WHERE`); identificadores en `snake_case`.
- Nombres de tablas en plural (`orders`), columnas descriptivas (`created_at`, no `date1`).
- Nunca `SELECT *` en código de aplicación: listar columnas explícitamente.
- Alias significativos (`orders o`, `customers c`) y JOINs explícitos (`INNER JOIN ... ON`), nunca comas en el FROM.

## Diseño de esquema
- Toda tabla con clave primaria (preferir `BIGINT IDENTITY`/`BIGSERIAL` o UUID según necesidad de distribución).
- `created_at`/`updated_at` (`TIMESTAMPTZ`) en tablas de negocio.
- Claves foráneas declaradas SIEMPRE, con `ON DELETE` explícito y consciente.
- Normalizar a 3FN por defecto; desnormalizar solo con una razón de rendimiento medida y documentada.
- Tipos correctos: dinero en `NUMERIC(19,4)` (jamás FLOAT), booleanos en `BOOLEAN`, fechas en tipos de fecha, no VARCHAR.
- `NOT NULL` por defecto; NULL solo cuando la ausencia tiene significado de negocio.

## Consultas y rendimiento
- Índices para: claves foráneas, columnas de filtros frecuentes y de ordenamiento. No indexar "todo".
- Consultas sargables: no envolver columnas indexadas en funciones (`WHERE fecha >= X`, no `WHERE YEAR(fecha) = X`).
- Paginación con keyset (`WHERE id > ?`) para tablas grandes; `OFFSET` solo en datasets pequeños.
- `EXISTS` sobre `IN (subquery)` para verificaciones de existencia.
- Revisar plan de ejecución (`EXPLAIN`) para toda consulta nueva sobre tablas grandes.
- Evitar N+1: resolver con JOINs o cargas por lote desde la aplicación.

## Seguridad
- SIEMPRE consultas parametrizadas; la concatenación de strings con entrada de usuario está prohibida (SQL injection).
- Principio de mínimo privilegio: la app no se conecta como superusuario/sa.
- No guardar datos sensibles en claro (contraseñas con hash fuerte; PII cifrada si lo exige la norma).

## Migraciones
- Toda modificación de esquema vía migración versionada (Flyway, Liquibase, Alembic, EF Migrations, goose).
- Migraciones inmutables una vez aplicadas en ambientes compartidos: los cambios van en una nueva migración.
- Compatible hacia atrás durante despliegues: agregar columna → desplegar código → eliminar columna vieja en migración posterior.
- Nunca `DROP` destructivo sin respaldo verificado y plan de rollback.

## Transacciones
- Transacciones cortas: abrir tarde, cerrar temprano; nada de llamadas de red dentro de una transacción.
- Nivel de aislamiento explícito cuando importa; manejar deadlocks con reintento idempotente.
