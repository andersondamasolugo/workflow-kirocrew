---
name: auto/pass-isolated-fix-to-master-via-sha-validator
description: Pasar un fix aislado a master por un validador de control de cambios (tipo DOFI) que valida tag/commit por SHA literal y genealogía
triggers: El tag no se pudo encontrar en el registro de commits, DOFI pull request failed, control de cambios con errores, tag a master rechazado, fix aislado a master, cherry-pick rechazado validador, tag anotado vs ligero
source: auto
session_key: dashboard:chat-13-1792725810
created_at: 2026-10-23T17:15:18+00:00
---

## When to use
Un validador de control de cambios (robot que corre al abrir PR a master, tipo DOFI) rechaza el pase con mensajes como "El tag no se pudo encontrar en el registro de commits de las ramas" o "El head no se pudo encontrar... se haya modificado la rama original creada desde el tag". Quieres llevar SOLO un fix aislado (no el corte completo de stage) a master y que el validador lo acepte.

## Regla que impone este tipo de validador
Valida por **SHA LITERAL y genealogía**, NO por contenido byte-idéntico. Exige DOS condiciones simultáneas:
1. El tag debe ser **LIGERO** (el ref apunta directo al SHA del commit), NO anotado. Un tag anotado (`git tag -a`) crea un objeto-tag intermedio con SHA propio que no es un commit; el validador resuelve el tag a ese SHA, no lo halla en el registro de commits y rechaza.
2. El SHA del commit del tag debe existir **literalmente** en el registro de commits de develop Y stage (no basta mismo contenido; un cherry-pick tiene SHA nuevo distinto).

## Steps
1. **Diagnostica cuál condición falla.** Tras `git fetch origin --tags -q`:
   - Tipo de tag: `git ls-remote origin 'refs/tags/vX*'`. Un tag ligero devuelve UNA línea (ref=commit). Uno anotado devuelve DOS (ref=objeto-tag + línea `^{}`=commit). Compara con un tag que SÍ pasó.
   - SHA en ambientes previos: NO confíes en `git merge-base --is-ancestor` (da falso positivo porque considera contenido/árbol). Usa SHA literal: `git rev-list origin/stage | grep -q "^<sha40>$"` y lo mismo para develop. Haz `git fetch origin` antes y consulta el HEAD autoritativo con `git ls-remote origin refs/heads/stage` porque el `origin/stage` local puede estar desactualizado.
2. **Si el SHA aislado no está en develop/stage:** fusiona la MISMA rama `vX-to-master` (mismo commit/SHA) por PR a develop y luego a stage. Eso inyecta el SHA literal en ambos ambientes sin re-cherry-pickear. Verifica de nuevo con `git rev-list ... | grep`.
3. **Si el tag es anotado:** recréalo ligero sobre el mismo commit:
   - `git tag -d vX`
   - `git tag vX <commit-sha>`  (SIN `-a`)
   - `git push origin :refs/tags/vX`  (borra remoto)
   - `git push origin refs/tags/vX`  (push ligero)
   El commit no cambia; solo el tipo de objeto del ref. Pushear cada comando por separado si la política bloquea encadenar.
4. **Verifica** con `git ls-remote origin 'refs/tags/vX*'` que quede UNA sola línea igual que el tag que pasó.
5. **Relanza el validador** en el PR a master.

## Receta limpia para la próxima (evita las vueltas)
cherry-pick del fix desde master en rama `vX-to-master` → PR a develop → PR a stage (mete el SHA literal en ambos) → crear tag **LIGERO** sobre ese mismo commit → PR a master. Así se consigue aislamiento (solo el fix) Y genealogía válida a la vez.

## Gotchas
- `git merge-base --is-ancestor` MIENTE para este validador: dice que un commit "está" por contenido aunque su SHA literal no exista en la rama. Siempre verifica con `git rev-list | grep` del SHA de 40 chars.
- El mensaje dice literalmente "el **tag** no se pudo encontrar": si el SHA del commit ya está en develop/stage y aun así falla, el problema es el TIPO de tag (anotado), no la genealogía. Lee el mensaje al pie de la letra.
- Errores secundarios como "Errores con la carpeta .github" suelen ser síntoma del fallo de genealogía/tag, no un problema real del `.github` (verifica con `git diff --stat` que el diff del `.github` sea vacío).
- Borrar/re-pushear un tag toca un ref del repo compartido: no es destructivo de código pero pide confirmación del usuario antes.
- Un cherry-pick aislado y un corte completo de stage son mutuamente excluyentes en una sola rama SOLO si no pasas el SHA por develop/stage primero; el paso 2 resuelve esa aparente contradicción.
