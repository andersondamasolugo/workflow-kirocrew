---
name: secure-coding-frontend
description: >-
  Reglas OWASP Top 10:2025 de codificación segura para Frontend (Angular / React / Vue). Úsala al escribir o revisar componentes, templates, auth client-side, manejo de errores o config ANTES de hacer commit. Incluye reglas comunes + específicas del framework. La reparación la hace el agente dev-front-tienda / dev-front-bolivar-ui, orquestada por flow-security-gate.
always: false
triggers: secure coding frontend, owasp frontend, seguridad angular, seguridad react, revisar seguridad frontend, security review frontend, auditar owasp frontend
---

# Secure Coding — Frontend (Angular / React / Vue) (OWASP Top 10:2025)

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

> **Orquestación (KiroCrew).** Base de conocimiento read-only que consume `flow-security-gate`
> antes de cada commit en repos Angular/React. El gate detecta/clasifica; la REPARACIÓN de cada
> hallazgo la ejecuta `dev-front-tienda` (`td-*`/PrimeNG) o `dev-front-bolivar-ui` (`sb-ui-*`).
> El commit NO se hace hasta resolver Critical/High.

---

## Reglas OWASP comunes (A01–A10)

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

---

## Reglas OWASP específicas — Frontend (Angular / React / Vue)

# Reglas de Seguridad OWASP — Frontend (Angular, React, Vue)

Patrones específicos de vulnerabilidades en aplicaciones frontend SPA.
Aplica cuando el repositorio contiene código de frontend junto al backend (micromonolito).

## A01 — Broken Access Control (Frontend)

- Rutas/páginas protegidas solo con guards del lado cliente sin validación en el backend
- Información sensible (roles, permisos, IDs internos) expuesta en el state del frontend (Redux, NgRx, Pinia)
- Tokens de acceso almacenados en `localStorage` (accesible via XSS)
- Lógica de autorización implementada solo en el frontend (ocultar botones/menús sin validar en API)
- Rutas de admin accesibles cambiando la URL manualmente sin verificación server-side
- CORS: frontend haciendo requests a APIs sin restricción de origen

### Angular específico
- `CanActivate` guards que solo verifican un flag local sin validar token con el backend
- Rutas lazy-loaded sin `CanLoad` guard
- `AuthGuard` que redirige pero no previene carga del módulo

### React específico
- `PrivateRoute` / `ProtectedRoute` que solo verifica state local
- Rutas en React Router sin wrapper de autenticación
- Context/Redux con datos de permisos que el usuario puede modificar via DevTools

### Vue específico
- `beforeEach` navigation guard sin validación de token
- Rutas sin `meta.requiresAuth` o sin guard global

## A02 — Security Misconfiguration (Frontend)

- Source maps habilitados en producción (`devtool: 'source-map'` en webpack/vite)
- `console.log()` con datos sensibles en producción
- Variables de entorno con secrets expuestas en el bundle (todo lo que empieza con `NEXT_PUBLIC_`, `VITE_`, `REACT_APP_` es público)
- API keys de servicios terceros hardcodeadas en el código frontend
- `robots.txt` o `sitemap.xml` exponiendo rutas internas
- Headers de seguridad no configurados en el servidor que sirve el SPA:
  - `Content-Security-Policy` ausente
  - `X-Frame-Options` ausente (clickjacking)
  - `X-Content-Type-Options` ausente
  - `Strict-Transport-Security` ausente

### Angular específico
- `angular.json` con `optimization: false` o `sourceMap: true` en configuración de producción
- `environment.prod.ts` con URLs de desarrollo o flags de debug
- `budgets` no configurados (permite bundles excesivamente grandes que pueden incluir código innecesario)

### React específico
- `next.config.js` con `reactStrictMode: false`
- `.env.local` con variables `NEXT_PUBLIC_` que contienen secrets
- Build de desarrollo desplegado en producción (`process.env.NODE_ENV !== 'production'`)

### Vue específico
- `vue.config.js` con `productionSourceMap: true`
- `vite.config.ts` sin configuración de CSP

## A04 — Cryptographic Failures (Frontend)

- Datos sensibles almacenados en `localStorage` o `sessionStorage` sin cifrar
- Tokens JWT decodificados y mostrados en la UI (expone claims)
- Passwords o datos de tarjeta almacenados temporalmente en variables del componente
- Uso de `btoa()`/`atob()` como "cifrado" (es solo Base64 encoding)
- Conexiones a APIs via HTTP en vez de HTTPS
- Certificados SSL ignorados en configuración de proxy de desarrollo que llega a producción

## A05 — Injection (Frontend)

### XSS (Cross-Site Scripting) — Principal riesgo en frontend

- **Angular**: Uso de `[innerHTML]` con datos del usuario sin sanitización via `DomSanitizer`
- **Angular**: `bypassSecurityTrustHtml()`, `bypassSecurityTrustScript()`, `bypassSecurityTrustUrl()` con input no confiable
- **Angular**: Interpolación en `style` o `href` con datos del usuario
- **React**: `dangerouslySetInnerHTML` con datos del usuario sin sanitizar (DOMPurify)
- **React**: `href={userInput}` sin validar protocolo (permite `javascript:`)
- **React**: `eval()` o `Function()` con datos del usuario
- **Vue**: `v-html` con datos del usuario sin sanitización
- **Vue**: Templates dinámicos compilados con input del usuario

### Otros vectores de inyección
- URLs construidas con concatenación de strings del usuario sin encoding
- `window.location.href = userInput` sin validación
- `document.write()` con datos dinámicos
- `postMessage()` sin validar `origin` en el receptor
- `iframe` con `src` dinámico sin validación de URL
- Regex construidos con input del usuario (ReDoS)

## A06 — Insecure Design (Frontend)

- Validación de formularios solo en el frontend sin validación equivalente en el backend
- Lógica de negocio crítica implementada en JavaScript del cliente (precios, descuentos, permisos)
- Rate limiting solo en el frontend (debounce/throttle sin protección server-side)
- Flujos de pago o transacciones donde el monto se envía desde el frontend sin validación server-side
- Formularios de upload sin restricción de tipo/tamaño en el frontend Y en el backend
- Auto-complete habilitado en campos de password o datos sensibles

## A07 — Authentication Failures (Frontend)

- Tokens almacenados en `localStorage` (vulnerable a XSS) en vez de `httpOnly` cookies
- Refresh tokens expuestos en el frontend
- Sesión que no expira en el frontend (falta de idle timeout)
- Falta de logout que invalide el token en el backend (solo borra localStorage)
- Formularios de login sin protección CSRF
- "Remember me" que almacena credenciales en el cliente
- Auto-login con tokens en query parameters de la URL (visible en logs, historial, referrer)

### Angular específico
- `HttpInterceptor` que adjunta token sin verificar expiración
- Falta de interceptor para manejar 401 y refrescar token

### React específico
- Token almacenado en React Context que se pierde en refresh (indica mal manejo de sesión)
- Axios interceptor sin manejo de token refresh

## A08 — Software or Data Integrity (Frontend)

- Scripts de CDN sin `integrity` attribute (Subresource Integrity — SRI)
- `<script>` tags con `src` dinámico
- `eval()` de código recibido del servidor
- Service Workers que cachean respuestas sin validación
- Dependencias npm con `postinstall` scripts no auditados
- Falta de `package-lock.json` o `yarn.lock` en el repositorio

## A09 — Logging & Alerting (Frontend)

- Errores de JavaScript no capturados (falta de error boundary en React, `ErrorHandler` en Angular)
- `console.log()` con datos sensibles (tokens, PII, passwords)
- Falta de envío de errores del frontend a un servicio de monitoreo (Sentry, DataDog, etc.)
- Errores de red/API silenciados sin logging
- Falta de tracking de eventos de seguridad en el frontend (login fallido, sesión expirada)

## A10 — Exceptional Conditions (Frontend)

- Promises sin `.catch()` o `try/catch` en async/await
- Componentes que crashean sin error boundary (React) o `ErrorHandler` (Angular)
- Falta de manejo de errores HTTP (404, 500, timeout) — UI se queda en estado inconsistente
- Formularios que permiten submit múltiple sin protección (double-click)
- Estado de la aplicación corrupto después de un error no manejado
- Falta de fallback UI cuando una API falla
