---
inclusion: always
name: gb-workspace
description: Reglas del workspace __WORKSPACE_NAME__ (carpeta que agrupa los repositorios del proyecto). Se carga solo en los chats cuyo directorio de proyecto es esta carpeta.
---

# Workspace __WORKSPACE_NAME__

Esta carpeta es un workspace de Kiro Crew: agrupa varios repositorios del proyecto. Cada subcarpeta con `.git` es un repositorio independiente. La raíz del workspace **no** es un repositorio.

## Reglas

- Antes de editar, identifica el repositorio y la rama: `git -C <repo> status -sb`.
- Trabaja solo dentro del repositorio de la HU. No modifiques otros repositorios sin que el usuario lo pida.
- Un commit y un PR por repositorio, con el mismo nombre de rama de la HU en cada uno (`feature/<HU>`).
- Si el cambio toca varios repositorios, el orden es: base de datos, backend, frontend (ver `flow-fullstack`).
- Los archivos locales (`env.local`, `sonar-local.properties`, `.scannerwork-local/`) no se versionan: se excluyen con `.git/info/exclude` de cada repositorio.
- Para trabajar dos HU a la vez usa `git worktree` dentro del workspace (`<repo>-<HU>`). No cambies de rama en un repositorio con trabajo sin commitear.
- Lanza subagentes con `cwd` en la carpeta del repositorio o del worktree solo si Kiro Crew lo acepta; si rechaza la ruta, trabaja en la sesión principal.
- La lista de repositorios del proyecto está en `repos.txt`.

## Reglas propias del proyecto

Agrega aquí, o en otros archivos de esta carpeta `.kiro/steering/`, las reglas que solo aplican a este proyecto. Las reglas generales del equipo vienen del kit instalado en `~/.kiro/steering/`.
