---
name: auto/build-readonly-oracle-mcp-macos
description: Construir un MCP server propio de solo-lectura a Oracle en macOS Apple Silicon, resolviendo thin vs thick mode y el verificador 10g
triggers: MCP Oracle, python-oracledb, thin mode falla, verificador 10g, Instant Client ARM64, conexion Oracle macOS, DPY-3015, SID vs service name
source: auto
session_key: dashboard:chat-18-1793113971
created_at: 2026-10-27T18:25:44+00:00
---

## When to use
Crear un MCP server (o cualquier cliente Python) que conecte a una base Oracle desde macOS Apple Silicon, cuando el usuario solo tiene credenciales y el equivalente de sqlplus. Aplica a cualquier instancia Oracle nueva; el patron del server de solo-lectura y el fallback thin->thick se repiten base a base.

## Steps
1. **Confirma conectividad y parametros ANTES de instalar nada.** Prueba red con `nc -vz -G 5 <host> <port>` (IPs privadas 10.x exigen VPN). Aclara SID vs service name: la cadena sqlplus `//host:port/NOMBRE` usa service name, pero si el usuario dice 'SID X', construye el DSN con `oracledb.makedsn(host, port, sid=X)` — NO con service name.
2. **Resuelve el Python.** El SDK `mcp` exige Python >=3.10; el python3 del sistema macOS suele ser 3.9.x. Busca uno moderno: `for p in python3.13 python3.12 python3.11; do command -v $p && $p --version; done` y usa Homebrew python3.12 si existe.
3. **Instala deps aisladas con --target (no venv).** `python3.12 -m venv` falla por ensurepip en algunos macOS; en su lugar `python3.12 -m pip install --target <dir>/libs oracledb==2.5.1 'mcp>=1.9,<2'`. OJO: `mcp` 2.x renombra/mueve FastMCP y `mcp` 1.2.0 trae un pydantic incompatible (error eval_type_backport); fija `mcp>=1.9,<2`. Verifica con `PYTHONPATH=<dir>/libs python3.12 -c 'import oracledb; from mcp.server.fastmcp import FastMCP'` (no imprimas `mcp.__version__`, no existe el atributo).
4. **Escribe el server de solo-lectura.** FastMCP con 3 tools (ping, describe_table, query). Guard obligatorio: la query debe empezar por SELECT/WITH, rechazar `;` multiples y DML/DDL. Credenciales SOLO por variables de entorno (ORA_USER/PASSWORD/HOST/PORT/SID/MAX_ROWS), nunca hardcodeadas. Pon la etiqueta/nombre desde una env var (ORA_LABEL) para que el MISMO codigo sirva a varias conexiones. Limite de filas por defecto.
5. **Prueba thin mode primero con un ping real** exportando las env vars en el proceso (no en disco). Si falla con un error de verificador de contraseña (10g / `0x939`, tipico de Oracle 11g con `sec_case_sensitive_logon=FALSE`), thin mode NO puede: necesitas thick mode.
6. **Thick mode = Oracle Instant Client.** No uses taps de Homebrew de terceros (exigen `brew trust`). Descarga el DMG oficial `instantclient-basiclite-macos-arm64.dmg` de download.oracle.com, montalo con `hdiutil attach`, copia las dylib al dir del MCP, `hdiutil detach`. macOS pone las dylib en cuarentena: `chmod -R u+w <ic_dir>` y luego `xattr -dr com.apple.quarantine <ic_dir>`. En el server añade `oracledb.init_oracle_client(lib_dir=<ic_dir>)`.
7. **Valida las 3 tools end-to-end**: ping OK, describe de una tabla real, un SELECT. Para probar el guard de solo-lectura usa casos negativos UPDATE y multi-sentencia `SELECT 1; SELECT 2` — NUNCA incluyas texto 'DROP TABLE' literal en la linea de shell (la safety policy lo bloquea aunque sea un caso de prueba).
8. **Registra en mcp.json** (bloque nuevo junto a los existentes, sin tocarlos), command=run.sh con PYTHONPATH de libs y python3.12, credenciales como `env`. Valida el JSON con la herramienta de lectura/parse, NO con `python3 -c` que importe el producto.
9. **El restart lo hace el usuario.** `kirocrew restart` esta bloqueado por self-protection (el agente no puede reiniciar su supervisor). Pide al usuario correrlo en su Terminal; luego confirma con un ping del tool_id.

## Gotchas
- Dos servers que exponen tools con el MISMO nombre (ej. dos Oracle con `oracle_ping`): el nombre pelado resuelve al ultimo cargado. Carga por tool_id completo (`oracle-X::oracle_ping`) justo antes de llamar para forzar la base correcta.
- 'vuelve a configurar' cuando ya hay una conexion andando = AGREGAR otra, no borrar la existente (destructivo). Generaliza el server y duplica el bloque en mcp.json cambiando env vars.
- No lances colonia de subagentes para esto: es trabajo secuencial de un solo hilo (crear un archivo + registrar), la paralelizacion solo suma overhead.
- Advierte al usuario si pego credenciales vivas en el chat (quedan en el transcript); redactalas en tus respuestas y recomienda rotarlas.
- `file_send` no acepta .zip (solo audio/video/imagen/PDF); si empaquetas el MCP para otro, dejalo en una ruta y avisa. Excluye del zip `.venv`, `__pycache__`, `.pyc`, `.env` y cualquier credencial; documenta en un README que el receptor ajuste la ruta de `command` y corra el `xattr` de Gatekeeper.
- Antes de armar un SELECT contra una tabla, lee su definicion en el repo de esquema para no adivinar columnas.
