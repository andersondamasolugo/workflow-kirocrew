---
inclusion: auto
name: security-audit
description: Auditoría de seguridad completa del código existente. Usar cuando el usuario pida auditar, revisar o escanear la seguridad del proyecto, o después de completar una funcionalidad.
---

# Auditoría de seguridad (post-desarrollo)

Proceso para auditar código existente. Ejecutar cuando el usuario lo pida o al
terminar una funcionalidad completa.

## Fase 1: Inventario
1. Mapear superficies de ataque: endpoints HTTP, webhooks, colas, jobs, archivos subidos, integraciones externas.
2. Identificar dónde entran datos no confiables y dónde salen datos sensibles.
3. Listar dependencias y sus versiones (lockfiles).

## Fase 2: Escaneo
Ejecutar en este orden y registrar resultados:

1. **Secretos**: buscar patrones de credenciales en el repo (claves AWS `AKIA...`, tokens, `password=`, claves privadas `-----BEGIN`). Revisar también historial si es posible.
2. **Dependencias**: correr la herramienta del ecosistema (`npm audit` / `pip-audit` / `dotnet list package --vulnerable` / `govulncheck` / `mvn dependency-check`).
3. **Código**: revisar manualmente contra la checklist de `secure-coding.md`, priorizando: autenticación/autorización, consultas a BD, manejo de archivos, llamadas externas, criptografía y logging.
4. **Configuración**: CORS abiertos (`*` con credenciales), modo debug en producción, cabeceras de seguridad ausentes, TLS deshabilitado, permisos de contenedor/IAM excesivos.

## Fase 3: Informe de hallazgos
Presentar SIEMPRE en este formato de tabla, ordenado por severidad:

| # | Severidad | Categoría (OWASP/CWE) | Archivo:línea | Descripción del riesgo | Solución propuesta |
|---|-----------|----------------------|---------------|------------------------|--------------------|

Severidades:
- **Crítica**: explotable remotamente sin autenticación, o fuga de secretos/datos. Detener todo hasta resolver.
- **Alta**: explotable con condiciones comunes (usuario autenticado, XSS almacenado).
- **Media**: requiere condiciones específicas o defensa en profundidad ausente.
- **Baja**: hardening y mejores prácticas.

Cada hallazgo debe explicar el riesgo en lenguaje de negocio (qué podría pasar, no
solo el término técnico) y proponer una solución concreta con el cambio de código.

## Fase 4: Aprobación y remediación
Al terminar el informe, pregunta al usuario qué hallazgos aprueba corregir y sigue
el flujo de `remediation-workflow.md`. NUNCA corrijas sin aprobación.
