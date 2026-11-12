---
name: auto/verify-hu-data-dependencies-oracle-readonly
description: Verificar contra la DB real (read-only) si las tablas/parámetros que una HU asume ya existen, antes de planificar capas DB/BE/FE
triggers: HU asume tabla, verificar si existe en DB, oracle read-only MCP, parametro parametrizable, reusar lo existente, antes de crear DDL, esquema correcto
source: auto
session_key: dashboard:chat-17-1793113493
created_at: 2026-10-27T17:39:48+00:00
---

## When to use
Una HU (o análisis de flow-po) asume que ciertas tablas, columnas, parámetros o integraciones 'ya existen' o 'se reusan de otro flujo'. Antes de asignar trabajo a dev-database/dev-backend o de proponer DDL nuevo, confirmar contra la DB viva qué existe realmente. Aplica a cualquier backend con MCP Oracle read-only (tools oracle_ping / oracle_describe_table / oracle_query) o equivalente.

## Steps
1. **Confirma a qué esquema/usuario estás conectado ANTES de concluir nada.** Un MCP etiquetado con el nombre de una base puede conectar con otro usuario. Corre `SELECT USER FROM dual` y `SELECT username FROM all_users` (o lista owners con `SELECT DISTINCT owner FROM all_tables`). Si el owner esperado no aparece, estás en la instancia/credencial equivocada — no interpretes 'describe vacío' como 'no existe'; interprétalo como 'no visible desde aquí' y pide/cambia la conexión correcta.
2. **Ping primero** (`oracle_ping`) para descartar VPN/red caída.
3. **Lee la definición del repo de esquema antes de armar SELECTs** para no adivinar nombres de columnas. Si los .sql están en Latin-1/ISO-8859-1, léelos con `iconv -f ISO-8859-1 -t UTF-8 archivo.sql` en vez del lector normal (evita corromper UTF-8). Para columnas vivas, prefiere `oracle_describe_table` contra la DB en vez de parsear el .sql.
4. **Busca cada pieza asumida con el diccionario, no solo por nombre exacto.** Para 'tabla X': `SELECT table_name FROM all_tables WHERE table_name LIKE '%PATRON%'`. Para 'columna que marca Y': `SELECT table_name, column_name FROM all_tab_columns WHERE column_name LIKE '%PATRON%'`. Esto revela si el concepto vive como tabla catálogo, como columna/flag, o no existe.
5. **Distingue flag-de-transacción vs atributo-de-catálogo.** Un flag en una tabla de detalle/solicitud (ej. marca si UNA solicitud fue X) no es lo mismo que un atributo del catálogo maestro (si la entidad ES X). No los confundas como fuente de verdad reusable.
6. **Para 'parámetro parametrizable': localiza el catálogo clave-valor real** (suele ser una tabla tipo `*_PARAMETROS` con COD/NOM/VAL + una clasificación/categoría). OJO: una tabla llamada `PARAMETROS` a secas suele ser solo user/password de conexión, NO el catálogo de negocio. Verifica si el parámetro concreto ya existe con un SELECT por su clasificación; si el mecanismo existe pero el valor no, el trabajo es un INSERT (DML bajo), no DDL.
7. **Antes de proponer agregar algo, mira si un indicador existente ya sirve — con datos de poblamiento.** Trae una muestra (`FETCH FIRST 25 ROWS ONLY`) y cuenta cuántas filas tienen cada indicador candidato poblado (`SELECT COUNT(*) ... WHERE col = 1`). Un indicador que existe pero significa otro concepto, o que está en 0 de facto, NO sirve como reuso.
8. **Cierra con veredicto por pieza**: ✅ existe (reusar) / ⚠️ mecanismo existe pero falta el dato (DML) / ❌ no existe (requiere DDL o decisión de negocio). Mapea cada veredicto al ajuste de capas DB/BE/FE y agentes.

## Gotchas
- 'describe vacío' casi siempre = esquema/usuario equivocado, no ausencia. Verifica `SELECT USER` siempre antes de afirmar 'no existe'.
- No modifiques el repo de DB ni corras DML/DDL durante la verificación: es solo lectura.
- Decisión técnica (columna vs tabla nueva) la puedes recomendar tú; qué valores/códigos poblar suele ser decisión de negocio — sepáralas explícitamente.
- Replica el patrón que la tabla ya usa (ej. otra columna indicador) en vez de inventar estructura nueva.
- Los COUNT de poblamiento evitan recomendar reusar una columna que en la práctica nadie llenó.
