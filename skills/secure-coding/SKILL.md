---
name: secure-coding
description: >-
  Reglas OWASP Top 10:2025 de codificación segura (generales, todos los lenguajes). Úsala al escribir o revisar código ANTES de llevar un commit para detectar fallas de control de acceso, inyección, criptografía, auth, logging y manejo de errores. La reparación de hallazgos la hace el agente especializado del stack (dev-backend / dev-front-*), orquestada por flow-security-gate.
always: false
triggers: secure coding, codificacion segura, owasp, revisar seguridad codigo, auditar owasp, security review general
---

# Secure Coding — OWASP Top 10:2025 (general)

## Cómo aplicar estas reglas

Eres un ingeniero de seguridad de aplicaciones. Revisa el código provisto en
`$ARGUMENTS` contra las reglas OWASP embebidas abajo y reporta hallazgos
concretos: categoría OWASP, ubicación, evidencia y remediación. Si `$ARGUMENTS`
no trae código, pide el archivo o fragmento a revisar.

Disparadores típicos mientras codificas:
- Escribir un endpoint o controlador → A01 (control de acceso / IDOR), A07 (autenticación).
- Construir queries o comandos → A05 (inyección: SQL/NoSQL/command/XSS).
- Manejar secretos, tokens o passwords → A04 (criptografía), A09 (logging seguro).
- Configurar el servicio → A02 (misconfiguration), A03 (cadena de suministro).
- Manejar errores y excepciones → A10 (condiciones excepcionales / fail-open).

> **Orquestación (KiroCrew).** Esta skill es la **base de conocimiento** read-only que consume
> el gate `flow-security-gate` antes de cada commit. El gate detecta y clasifica; la REPARACIÓN
> de cada hallazgo la ejecuta el agente especializado del stack (`dev-backend` para Java/Spring,
> `dev-front-tienda`/`dev-front-bolivar-ui` para Angular). El commit NO se hace hasta que no
> queden hallazgos Critical/High (ver `flow-security-gate`).

---

# Reglas de Auditoría de Seguridad — OWASP Top 10:2025

Aplican a TODOS los lenguajes. Evalúa cada categoría y reporta solo hallazgos concretos con evidencia en el código.

Fuente: [OWASP Top 10:2025](https://owasp.org/www-project-top-ten/)

---

## A01:2025 — Broken Access Control

Buscar patrones donde el control de acceso falla o está ausente:

- Endpoints sin validación de autenticación/autorización
- Acceso directo a objetos sin verificar propiedad (IDOR): IDs en URLs/params sin validar que el usuario tenga permiso
- Falta de validación de roles/permisos en operaciones sensibles (CRUD, admin)
- Elevación de privilegios: endpoints admin accesibles sin rol adecuado
- Manipulación de tokens/cookies para cambiar identidad o rol
- CORS mal configurado: `Access-Control-Allow-Origin: *` en APIs con datos sensibles
- Falta de rate limiting en endpoints de autenticación
- SSRF: el servidor hace requests a URLs proporcionadas por el usuario sin validación
- Path traversal: acceso a archivos fuera del directorio permitido (`../`, `..\\`)
- Falta de control de acceso en métodos HTTP (PUT/DELETE accesibles sin autorización)

### Contexto: Microservicios privados detrás de API Gateway

Muchos microservicios en la organización son privados y solo accesibles a través de un API Gateway (AWS API Gateway + ALB + ECS Fargate). Aunque el API Gateway maneja autenticación/autorización a nivel de infraestructura, los hallazgos de falta de autenticación en el código siguen siendo válidos por defensa en profundidad (Zero Trust). Sin embargo, la remediación debe ser contextualizada:

**Remediación para microservicios privados detrás de API Gateway:**
1. El API Gateway debe propagar el JWT validado al microservicio (header `Authorization`).
2. El microservicio debe implementar un filtro/middleware que **valide la firma del JWT** recibido (no autenticar desde cero, solo verificar que el token es legítimo y no fue manipulado).
3. Usar decoradores/anotaciones de autorización con roles/scopes extraídos del JWT para control granular por endpoint.
4. Configurar CORS con orígenes explícitos vía variable de entorno (nunca `*`), o eliminar el middleware CORS si el servicio solo recibe tráfico interno del ALB.

Esto asegura que incluso si alguien bypasea el API Gateway (acceso directo al ALB desde la VPC, misconfiguration, o cambio de topología futuro), el microservicio rechaza requests sin JWT válido.

**IMPORTANTE para la remediación**: Cuando reportes falta de autenticación/autorización en endpoints, incluye SIEMPRE esta nota contextual en la remediación:
> "Si este microservicio es privado y está detrás de un API Gateway, la remediación mínima es: (1) validar la firma del JWT propagado por el API Gateway, (2) aplicar autorización por roles/scopes del JWT en cada endpoint, (3) configurar CORS con orígenes explícitos o eliminarlo si es puramente interno."

**Excepción — autenticación transversal ya implementada (NO reportar):** Si el microservicio YA implementa un filtro/middleware GLOBAL que valida el token/header y RECHAZA (401) las requests no autenticadas en TODAS las rutas, la autenticación está PRESENTE y NO debes reportar "falta de autenticación" por endpoint. Ejemplos de este patrón:
- Spring: un `OncePerRequestFilter`/`Filter` (normalmente `@Component` con `@Order(...)`) que retorna 401 cuando falta el header/token esperado.
- Node.js: un middleware de auth montado app-wide (`app.use(authMiddleware)`).
- Angular: un `HttpInterceptor` o `CanActivate` guard que exige token válido.

Antes de reportar, verifica: (a) que el filtro/middleware cubra las rutas del endpoint, y (b) su flag de activación y su valor en el perfil de producción (p. ej. `security.enforce-gateway-auth: true` en `application-prod.yml`). Solo reporta un hallazgo si el mecanismo está AUSENTE o explícitamente DESACTIVADO en producción. No reportes "missing authentication" por-endpoint solo porque el controlador no tenga un `@PreAuthorize`/chequeo inline: la auth puede vivir en el filtro transversal.

## A02:2025 — Security Misconfiguration

Buscar configuraciones inseguras:

- Debug/desarrollo habilitado en producción (`DEBUG=True`, `devtools`, stack traces expuestos)
- Headers de seguridad faltantes: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`
- Configuraciones por defecto no cambiadas (puertos, credenciales, paths)
- Listado de directorios habilitado
- Mensajes de error que exponen información interna (stack traces, queries SQL, paths del servidor)
- Permisos excesivos en servicios cloud (IAM policies con `*`)
- Servicios innecesarios habilitados o puertos abiertos
- Versiones de software/frameworks desactualizadas con CVEs conocidos
- Configuración TLS/SSL débil (protocolos antiguos, cipher suites inseguras)

### Antes de reportar una "misconfiguration en producción" — resolver activación real (NO reportar si está inactivo)

Antes de reportar debug/logging/dev-tooling "en producción", verifica que el código esté realmente ACTIVO en el entorno productivo:
- **Gated por perfil**: si la clase/bean está anotada con un perfil que EXCLUYE producción (p. ej. Spring `@Profile({"dev","stage"})`), NO se carga en prod → NO es un hallazgo.
- **Nivel de log efectivo**: considera el nivel de log de producción (p. ej. `application-prod.yml` `logging.level.*`). Si el logging de body/datos solo ocurre en un nivel que NO está habilitado en prod (p. ej. el código loguea el body en `TRACE` y prod está en `INFO`), NO es un hallazgo.
- **Config de build**: para source maps u opciones de build, resuelve la configuración de producción (p. ej. `angular.json` `configurations.production` con `sourceMap: false`) antes de reportar.

## A03:2025 — Software Supply Chain Failures

Buscar riesgos en la cadena de suministro de software:

- Dependencias sin versión fija (rangos abiertos: `>=`, `*`, `latest`, `^`)
- Falta de archivo de lock (package-lock.json, poetry.lock, Gemfile.lock)
- Dependencias con vulnerabilidades conocidas (verificar nombres y versiones)
- Falta de verificación de integridad (checksums, signatures)
- Pipelines CI/CD sin validación de artefactos
- Uso de registros de paquetes no oficiales o mirrors no verificados
- Dependencias abandonadas o sin mantenimiento activo
- Scripts de pre/post install en dependencias que ejecutan código arbitrario

## A04:2025 — Cryptographic Failures

Buscar uso incorrecto o ausente de criptografía:

- Datos sensibles transmitidos en texto plano (HTTP, sin TLS)
- Algoritmos criptográficos débiles o deprecados: MD5, SHA1 para hashing de passwords, DES, RC4
- Passwords almacenados sin hashing o con hash débil (sin salt, sin bcrypt/scrypt/argon2)
- Claves criptográficas hardcodeadas en el código fuente
- Generación de números aleatorios insegura (`Math.random()`, `random.random()` para tokens de seguridad)
- Certificados SSL/TLS auto-firmados o verificación deshabilitada (`verify=False`, `rejectUnauthorized: false`)
- Datos sensibles en logs (PII, tokens, passwords, números de tarjeta)
- Falta de cifrado en datos sensibles en reposo (bases de datos, archivos)
- IVs estáticos o reutilizados en cifrado simétrico

## A05:2025 — Injection

Buscar vectores de inyección:

- **SQL Injection**: concatenación de strings en queries SQL, falta de prepared statements/parameterized queries
- **NoSQL Injection**: inputs del usuario directamente en queries MongoDB/DynamoDB
- **Command Injection**: inputs del usuario en `os.system()`, `subprocess`, `exec()`, `Runtime.exec()`
- **LDAP Injection**: inputs sin sanitizar en queries LDAP
- **XSS (Cross-Site Scripting)**: inputs del usuario renderizados sin escape en HTML/JS
  - Uso de `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `[innerHTML]` sin sanitización
  - Falta de Content-Security-Policy
  - Datos del usuario en atributos de eventos (`onclick`, `onerror`)
- **Template Injection**: inputs del usuario en templates del servidor (SSTI)
- **XPath/XML Injection**: inputs sin sanitizar en queries XPath o parseo XML (XXE)
- **Header Injection**: inputs del usuario en headers HTTP (CRLF injection)
- **Expression Language Injection**: inputs en expresiones EL/SpEL/OGNL

## A06:2025 — Insecure Design

Buscar defectos de diseño de seguridad:

- Falta de validación de negocio (ej: precios negativos, cantidades imposibles)
- Flujos de autenticación sin protección contra fuerza bruta
- Recuperación de contraseña insegura (preguntas de seguridad, tokens predecibles)
- Falta de separación de privilegios en operaciones críticas
- Ausencia de límites de tasa (rate limiting) en APIs públicas
- Falta de validación de entrada en el servidor (solo validación client-side)
- Diseño que permite enumeración de usuarios (respuestas diferentes para usuario existente vs no existente)
- Falta de mecanismo de bloqueo de cuenta tras intentos fallidos

## A07:2025 — Authentication Failures

Buscar debilidades en autenticación:

- Credenciales por defecto o débiles permitidas
- Almacenamiento inseguro de credenciales (texto plano, encoding reversible)
- Tokens de sesión en URLs (query parameters)
- Sesiones que no expiran o con tiempos excesivos
- Tokens JWT sin validación de firma, sin expiración, o con algoritmo `none`
- Falta de MFA en operaciones sensibles
- Regeneración de session ID ausente después de login
- Cookies de sesión sin flags `HttpOnly`, `Secure`, `SameSite`
- Falta de protección CSRF en formularios que modifican estado

## A08:2025 — Software or Data Integrity Failures

Buscar fallas de integridad:

- Deserialización insegura de datos no confiables (Java ObjectInputStream, Python pickle, PHP unserialize)
- Falta de verificación de firma en actualizaciones de software
- Pipelines CI/CD sin controles de integridad
- Uso de CDNs sin Subresource Integrity (SRI)
- Auto-update sin verificación de firma
- Datos críticos modificables por el cliente sin validación server-side

## A09:2025 — Logging & Alerting Failures

Buscar deficiencias en logging y monitoreo:

- Eventos de seguridad no logueados (login fallido, acceso denegado, cambios de permisos)
- Logs que contienen datos sensibles (passwords, tokens, PII)
- Falta de logging en operaciones críticas (transacciones financieras, cambios de configuración)
- Logs solo locales sin envío a sistema centralizado
- Falta de alertas para eventos de seguridad
- Logs sin suficiente contexto (falta de timestamp, user ID, IP, correlation ID)
- Logs manipulables por el usuario (log injection)

## A10:2025 — Mishandling of Exceptional Conditions

Buscar manejo inadecuado de condiciones excepcionales:

- Excepciones que exponen información interna al usuario (stack traces, paths, queries)
- Fail-open: el sistema permite acceso cuando ocurre un error en la validación
- Falta de manejo de errores en operaciones críticas (pagos, autenticación)
- Recursos no liberados en caso de error (conexiones, file handles, locks)
- Race conditions en operaciones concurrentes (TOCTOU)
- Manejo inconsistente de errores (algunos capturados, otros no)
- Excepciones genéricas que ocultan errores específicos
