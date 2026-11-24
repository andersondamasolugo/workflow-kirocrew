# Instrucción: pase de HU a master con rama aislada y commit único

Para promover una HU `<HU>` a master sin arrastrar trabajo de otros compañeros,
NO cortes el tag desde la punta de stage (eso mete todo el release). En su lugar:

## Qué hacer
1. **Corta una rama LIMPIA desde `master`** (no desde un tag, no desde stage).
2. **Consolida TODO el desarrollo de la HU en UN SOLO commit** sobre esa rama.
3. **El desarrollador la promueve manualmente** por los ambientes (develop → stage → master),
   porque es su HU y conoce el alcance.

Así master recibe solo la HU, con historial limpio (1 commit), sin SHAs sueltos ni
commits de otros, y sin depender del corte de release del equipo.

## Comandos (reemplaza <HU>, <repo> y los SHAs)

```bash
git fetch origin

# 1) Rama limpia desde master (NO desde tag ni stage)
git checkout -b <HU>-to-master origin/master

# 2) Traer SOLO los commits de la HU (los que están en stage/develop y no en master).
#    Listalos primero, en orden cronológico:
git log --reverse --format="%H %s" --no-merges origin/master..origin/stage | grep "<HU>"
#    Cherry-pick de esos SHAs, en ese orden:
git cherry-pick <sha1> <sha2> ... <shaN>

# 3) Consolidar los N commits en UNO solo (mismo contenido, 1 commit):
git reset --soft origin/master
git commit -m "<HU>: <descripción corta del desarrollo> (consolidado)"

# 4) Confirmar que el diff es SOLO de la HU, nada ajeno:
git diff --name-only origin/master

# 5) Compilar + tests en local sobre la rama aislada antes de subir.

# 6) Push (rama propia, sin review previo -> force-with-lease SHA-pinned):
git push -u origin <HU>-to-master
```

## Luego el desarrollador promueve manualmente
Con la rama lista (`<HU>-to-master`, 1 commit desde master), el dev abre los PRs
por ambiente a su ritmo: develop → stage → master, verificando CI en cada uno.

## Reglas clave
- La rama **viene de master**, no de un tag ni de stage.
- **1 solo commit** con todo el desarrollo de la HU.
- **Nada de otros compañeros**: verifica con `git diff --name-only origin/master` que solo
  aparezcan archivos de la HU.
- Antes de pushear un fix a un PR ya abierto: `gh pr view <N> --json state,mergedAt`.
  OPEN = misma rama; MERGED = rama fresca + PR nuevo (si no, el commit queda huérfano).