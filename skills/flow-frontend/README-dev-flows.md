# Dev Flows — sistema nativo de KiroCrew (multi-flujo por tipo de desarrollo)

Sistema para **garantizar flujos E2E de desarrollo con mínima intervención**, construido
solo con primitivas nativas de KiroCrew (steering + skills + hooks). No usa MAFS, ni
`run.sh`, ni agentes permanentes.

## Piezas

| Pieza | Archivo | Rol |
|-------|---------|-----|
| Router | `~/.kiro/steering/dev-flow-router.md` (`inclusion: always`) | Clasifica el tipo de desarrollo y carga el flujo |
| Flujo frontend | `~/.kiro/crew/skills/flow-frontend/SKILL.md` | implementar → build → tests → verificación visual |
| Flujo backend | `~/.kiro/crew/skills/flow-backend/SKILL.md` | implementar → compilar → tests → contrato |
| Flujo fullstack | `~/.kiro/crew/skills/flow-fullstack/SKILL.md` | backend → frontend → integración |
| Flujo docs | `~/.kiro/crew/skills/flow-docs/SKILL.md` | README/changelog/OpenAPI en sync |
| Flujo PR | `~/.kiro/crew/skills/kirocrew-dev/prepare-pr/SKILL.md` | commit → PR → babysitting CI |
| Hook audit | `<proyecto>/.kiro/hooks/audit-on-edit.kiro.hook` (`fileEdited`) | audita standards+seguridad al escribir |
| Hook validate | `<proyecto>/.kiro/hooks/validate-on-stop.kiro.hook` (`agentStop`) | valida E2E al terminar, por tipo |

## Cómo se inician (3 formas)

1. **Automático por evento (mínima intervención):**
   - Al escribir → `audit-on-edit` audita cada archivo.
   - Al terminar → `validate-on-stop` detecta el tipo y corre la validación E2E.
2. **Automático por clasificación:** el router (`always`) clasifica tu petición y carga
   el flujo correcto sin que lo nombres.
3. **Manual:** "run flow-frontend", "document this" (dispara por `triggers`).

## Cómo se personaliza (siempre = editar un archivo)

| Cambiar… | Editar… |
|---|---|
| Fases de un flujo | el `SKILL.md` del flujo |
| Comando de build/test o umbral de cobertura | el `SKILL.md` o el `.kiro.hook` |
| Cuándo dispara la validación | el `when` del `.kiro.hook` (`patterns`, tipo de evento) |
| Qué reglas se validan | steering / powers (`code-standards-bolivar`, `code-security-bolivar`) |
| Cómo se clasifica el tipo | la tabla de `dev-flow-router.md` |
| Autónomo vs asistido | el `prompt` del hook ("corrige inline" vs "reporta y espera") |
| Un flujo nuevo | nuevo `flow-*/SKILL.md` + una fila en el router |

## Comportamiento actual
- **Autónomo**: los hooks corrigen violaciones claras inline; los hallazgos de criterio
  (posible falso positivo o cambio de comportamiento) se reportan, no se fuerzan.
- `build-check-on-stop.kiro.hook` quedó **deshabilitado** (lo reemplaza `validate-on-stop`).
- `run-fix-tests.kiro.hook` sigue activo (tests+cobertura al editar `.ts/.spec.ts`).

## Reglas no negociables (todos los flujos)
Nunca commit/push sin autorización · build con la config real (`tsconfig.app.json`) ·
standards+seguridad validados · verificación visual imagen-vs-imagen (sin evidencia no hay
PASS) · design system al 100% · leer steering del proyecto + powers antes de escribir.

## Distribución al equipo
Todo es versionable. Router y skills en `~/.kiro/`; hooks en `<proyecto>/.kiro/hooks/`.
Commitear a un repo de config y clonar, o publicar vía el agente `kiro-agent-manager`.
