---
inclusion: fileMatch
fileMatchPattern: ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.java", "**/*.cs", "**/*.go", "**/*.sql"]
---

# Codificación segura (prevención — aplicar mientras se escribe código)

Checklist basada en OWASP Top 10 y CWE. Todo código generado debe cumplirla.

## 1. Validación de entrada (A03 Injection)
- Toda entrada externa (HTTP, archivos, colas, CLI, BD) se valida ANTES de usarse: tipo, longitud, rango, formato, lista blanca.
- SQL: solo consultas parametrizadas u ORM; concatenación de strings prohibida.
- Comandos del SO: evitar `shell=True`/`exec` con entrada de usuario; usar APIs con argumentos separados.
- Rutas de archivo: normalizar y verificar contra directorio base (path traversal).
- Deserialización: nunca deserializar formatos binarios nativos (pickle, BinaryFormatter) con datos no confiables.

## 2. Autenticación y sesiones (A07)
- Contraseñas con hash adaptativo: bcrypt/argon2/PBKDF2 — jamás MD5/SHA1/claro.
- Tokens: expiración corta, verificación de firma y de `aud`/`iss` en JWT; nunca `alg: none`.
- Cookies de sesión: `HttpOnly`, `Secure`, `SameSite`.
- Mensajes de error de login genéricos (no revelar si el usuario existe).
- Límite de intentos (rate limiting) en endpoints de autenticación.

## 3. Autorización (A01 Broken Access Control)
- Verificar autorización en el SERVIDOR en cada endpoint, no solo ocultar botones en UI.
- Comprobar propiedad del recurso (`el pedido pertenece al usuario`) — prevenir IDOR.
- Denegar por defecto; roles/permisos centralizados, no `if` dispersos.

## 4. Datos sensibles y secretos (A02)
- Secretos NUNCA en el código ni en el repositorio: variables de entorno o gestor de secretos (Vault, AWS Secrets Manager).
- TLS para todo tránsito; no desactivar verificación de certificados.
- Cifrado estándar (AES-GCM); nunca criptografía casera ni ECB.
- No loguear contraseñas, tokens, PII ni números de tarjeta; enmascarar en logs.

## 5. Salida y frontend (A03 XSS)
- Escapar/encodificar salida según contexto (HTML, atributo, JS, URL).
- Frameworks modernos: no usar `dangerouslySetInnerHTML`/`innerHTML`/`v-html` con datos de usuario sin sanitizar.
- Cabeceras: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`.
- CSRF: tokens anti-CSRF en operaciones de cambio de estado con cookies de sesión.

## 6. Dependencias (A06)
- Antes de agregar una dependencia: verificar mantenimiento activo y ausencia de CVEs conocidos.
- Lockfile obligatorio; nombres exactos (typosquatting).
- Sugerir escaneo en CI: `npm audit`, `pip-audit`, `dotnet list package --vulnerable`, `govulncheck`, OWASP Dependency-Check.

## 7. Manejo de errores y logging (A09)
- Errores al cliente: mensaje genérico + ID de correlación; detalles técnicos y stack trace SOLO al log del servidor.
- Loguear eventos de seguridad: logins fallidos, cambios de permisos, accesos denegados.

## 8. Archivos y recursos
- Subidas de archivos: validar tipo real (magic bytes), tamaño máximo, nombre regenerado, almacenar fuera del webroot.
- SSRF: validar/limitar URLs solicitadas por el servidor (lista blanca de hosts).
- Timeouts y límites en toda llamada externa.

## Comportamiento del agente
- Si el código que estás a punto de generar violaría un punto de esta lista, genera la versión segura directamente.
- Si detectas una violación en código EXISTENTE mientras trabajas en otra cosa, no lo cambies: registra el hallazgo y repórtalo según `remediation-workflow.md`.
