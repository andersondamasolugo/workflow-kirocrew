---
inclusion: auto
name: remediation-workflow
description: Flujo de aprobación y corrección de hallazgos de seguridad. Usar al reportar vulnerabilidades encontradas o al aplicar correcciones de seguridad aprobadas por el usuario.
---

# Flujo de remediación con aprobación

Este flujo garantiza que el usuario mantiene el control: el agente detecta, explica
y propone; el usuario aprueba; el agente ajusta.

## Paso 1: Reportar (sin tocar código)
Por cada hallazgo presenta:

```
[SEC-001] SQL Injection — CRÍTICA
Archivo: src/repositories/user_repo.py:42
Problema: la consulta concatena `username` directamente en el SQL.
Riesgo: un atacante puede leer o borrar toda la base de datos.
Solución propuesta: reemplazar por consulta parametrizada.
Cambio estimado: 1 archivo, ~3 líneas. Sin impacto funcional.
```

## Paso 2: Solicitar aprobación
Ofrecer opciones explícitas:
- "Aprobar todos" — corrige todos los hallazgos propuestos.
- "Aprobar SEC-001, SEC-003" — corrige solo los indicados.
- "Explicar SEC-002" — profundiza antes de decidir.
- "Posponer" — registra los hallazgos en `SECURITY-BACKLOG.md` del workspace.

## Paso 3: Corregir (solo lo aprobado)
- Un hallazgo = un cambio atómico. Mostrar diff de cada corrección.
- La corrección no debe cambiar comportamiento funcional; si es inevitable, advertirlo ANTES de aplicar.
- Si existe suite de tests, ejecutarla tras cada corrección; si una corrección requiere test nuevo (regresión de seguridad), crearlo.

## Paso 4: Verificar y cerrar
- Re-ejecutar la validación puntual sobre el archivo corregido (¿la vulnerabilidad desapareció? ¿no se introdujo otra?).
- Resumir: hallazgos corregidos, pospuestos y descartados por el usuario.
- Actualizar `SECURITY-BACKLOG.md`: mover corregidos a la sección "Resueltos" con fecha.

## Reglas
- Nunca mezclar correcciones de seguridad con refactors o features en el mismo cambio.
- Nunca eliminar una advertencia de seguridad "para que compile" (p. ej. suprimir warnings del analizador) — eso es un hallazgo en sí mismo.
- Si un hallazgo crítico queda pospuesto, recordarlo al inicio de la siguiente sesión de trabajo.
