# Trabajar por workspace (recomendado, opcional)

Un **workspace** es una carpeta que agrupa los repositorios de un proyecto (por ejemplo base de datos, backend y frontend de una misma épica). Es el equivalente a abrir una carpeta multi-repositorio (`.code-workspace`) en el IDE: abres la carpeta una vez y el agente ve todos los repositorios juntos, con las mismas reglas.

**No es obligatorio.** El kit funciona igual abriendo un chat dentro de un solo repositorio. Se recomienda cuando manejas varios repositorios o varias HU a la vez, porque:

- Las reglas del proyecto se escriben una vez (`<workspace>/.kiro/steering/`) y aplican a todos los chats que parten de esa carpeta, sin copiarlas en cada repositorio.
- El agente conoce la lista de repositorios y el orden de trabajo (base de datos, backend, frontend).
- Una HU que toca varios repositorios se trabaja en un solo chat, con una sola rama por repositorio.
- Se evita mezclar proyectos: cada workspace tiene su propio contexto.

## Cómo se carga en Kiro Crew

Según la documentación de Kiro Crew, un chat tiene un **directorio de proyecto**. De ese directorio se leen `<proyecto>/.kiro/steering/**/*.md` y el `AGENTS.md` (si existe), y se aplican solo a los chats cuyo directorio de proyecto es esa carpeta. Por eso el workspace funciona como un proyecto más: el archivo `gb-workspace.md` solo se carga en los chats de ese workspace.

Para que el chat use el workspace como proyecto:

1. Abre el chat en una carpeta de la barra lateral cuyo directorio de proyecto sea el workspace, o
2. Pide a Kiro que cambie el proyecto del chat a esa ruta (usa la herramienta `set_project`).

> Los nombres exactos de los botones del dashboard no se verificaron para esta guía. Si no encuentras la opción, usa la segunda vía.

## Crear un workspace

macOS / Linux:

```bash
scripts/new-workspace.sh ~/workplace/gestion-bienestar
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\new-workspace.ps1 -Path "$HOME\workplace\gestion-bienestar"
```

Crea la carpeta con:

| Archivo | Para qué sirve |
|---------|----------------|
| `.kiro/steering/gb-workspace.md` | Reglas del workspace que se cargan en cada chat de esa carpeta |
| `repos.txt` | Lista de repositorios del proyecto (una línea: `<url-git> [carpeta]`) |
| `<nombre>.code-workspace` | Archivo multi-carpeta para abrir el mismo conjunto en el IDE |

Opciones: `--dry-run` / `-DryRun` muestra qué haría, `--clone` / `-Clone` clona los repositorios de `repos.txt` que no estén, y `--force` / `-Force` regenera el steering y el `.code-workspace`. `repos.txt` nunca se sobrescribe.

Flujo típico:

1. Crea el workspace.
2. Completa `repos.txt` con las URL de tus repositorios.
3. Ejecuta el mismo comando con `--clone` (o clona a mano dentro de la carpeta).
4. Abre un chat con la carpeta como proyecto y pide la HU por su clave Jira.

## Recomendaciones

- **Ubicación:** crea el workspace bajo `~/workplace/` o `~/workspace/`. Kiro Crew solo permite lanzar subagentes con `cwd` bajo las raíces configuradas en `subagent_cwd_allowed_roots`. En una máquina se observó que solo se aceptan carpetas que son hijas directas de esas raíces: si tus repositorios quedan a dos niveles, el subagente se rechaza y debes trabajar en la sesión principal. Revisa ese valor en tu configuración.
- **Un workspace por proyecto o épica**, no uno global con todos los repositorios de la empresa.
- **La raíz no es un repositorio.** Cada repositorio mantiene su `.git`; no inicialices git en la raíz del workspace.
- **Trabajo en paralelo:** usa `git worktree` dentro del workspace (`<repo>-<HU>`) en lugar de cambiar de rama con trabajo sin commitear.
- **Reglas del proyecto:** agrégalas en `<workspace>/.kiro/steering/`. Las reglas generales del equipo siguen viniendo del kit instalado en `~/.kiro/`.
- **Nada de secretos en el workspace.** `env.local`, tokens y credenciales siguen fuera de cualquier archivo versionado.
- Si cambia la lista de repositorios, edita `repos.txt` y regenera el `.code-workspace` con `--force`.

## Qué no cubre

- No se probó el flujo completo dentro de Kiro Crew desde un chat nuevo ni en Windows. El script de macOS/Linux se probó en una carpeta temporal (creación, `--dry-run`, `--clone` con un repositorio local, idempotencia). El script de PowerShell no se pudo ejecutar en esta máquina.
- El kit no obliga a usar workspaces: `AGENTS.md` solo lo recomienda y pregunta una vez.
