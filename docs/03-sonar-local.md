# Sonar local: medir antes del commit

Objetivo: no subir al PR algo que SonarCloud va a rechazar. El gate local imita el **New Code** de SonarCloud (solo evalúa las líneas cambiadas).

> Es una aproximación, no el gate real: el perfil local es "Sonar way", no el de la organización, y SonarCloud puede tener exclusiones de servidor que no están en el repo. SonarCloud en CI sigue siendo el gate final.

## 1. Requisitos (una sola vez por máquina)

| Pieza | Cómo |
|-------|------|
| Docker Desktop | Instalado y abierto |
| Servidor SonarQube Community | `docker run -d --name sonarqube -p 9000:9000 sonarqube:community` y entrar a http://localhost:9000 (admin inicial: cambiar la contraseña al primer ingreso) |
| SonarScanner CLI | Descargar el zip de tu plataforma, descomprimir en `~/tools/` y agregar `bin/` al `PATH` |
| Java 17 | Temurin 17. En macOS: `export JAVA_HOME=$(/usr/libexec/java_home -v 17)` |
| Token de usuario | En SonarQube: *My Account → Security → User Token* (prefijo `squ_`). Un *Analysis Token* (`sqa_`/`sqp_`) **no sirve**: da 403 en hotspots |
| Python 3 | Para correr los scripts |

Guardar el token en el llavero, **nunca** en un archivo del repo:

```bash
# macOS
security add-generic-password -a "$USER" -s sonar-local-token -w
# (te pide el valor por prompt; pegalo ahí)
```

Alternativa: variable de entorno `SONAR_TOKEN` (el script la lee primero).

## 2. Configuración por repo

```bash
python3 dev-flows/scripts/sonar_local_setup.py <ruta-del-repo>
```

Genera `sonar-local.properties` junto a cada `sonar-project.properties`, copiando las exclusiones del equipo pero apuntando a `localhost:9000` y a un working dir separado (`.scannerwork-local`). Se excluye en `.git/info/exclude` (**no** en `.gitignore`), así no se versiona ni ensucia el repo compartido.

Se pierde con clon nuevo, worktree o `git clean -fdx`: volver a correr el setup.

## 3. Correr el gate

Orden correcto: **commitear primero** (el gate compara `origin/<base>...HEAD`, no lee el working tree sucio), luego el gate, luego push.

```bash
docker start sonarqube        # si está caído, el gate responde SKIPPED

# Frontend (raíz del repo)
python3 dev-flows/scripts/sonar_local_gate.py <repo-fe> --base origin/develop

# Backend: primero tests + jacoco del módulo, luego un gate por módulo *-ms tocado
./gradlew test jacocoTestReport
python3 dev-flows/scripts/sonar_local_gate.py <repo-be>/<modulo> --base origin/develop
```

Veredicto (última línea):

| Resultado | Significado | Acción |
|-----------|-------------|--------|
| `SONAR-LOCAL: CLEAN` | Pasa | Seguir |
| `SONAR-LOCAL: BLOCKED` | Bug/vulnerabilidad nuevo, BLOCKER/CRITICAL, hotspot sin revisar, cobertura de líneas nuevas < 80 % o duplicación > 3 % (la línea `reason:` dice cuál) | Arreglar a la raíz, recompilar, re-correr. Máx. 3 iteraciones |
| `SONAR-LOCAL: SKIPPED` | Server, token, config o scan fallaron | Caer a revisión Sonar por lectura |

Pegar siempre los links `dashboard:` e `issues:` en el PR/chat.

## 4. Problemas conocidos

- `Cannot run program "security": posix_spawn failed` (macOS): el JRE embebido del scanner no puede lanzar `security`. Fix: `use_embedded_jre=false` en `bin/sonar-scanner` y `JAVA_HOME` a un JDK 17. Ver `skills/learnings/sonar-scanner-macos-jre-spawn-fix`.
- `Permission denied` / `Could not find 'java'` tras descomprimir: `chmod +x bin/* jre/bin/*`.
- Hotspots `403 Insufficient privileges`: usar User Token (`squ_`).
- `npm run test:coverage` "No tests found": no pasar comentarios `# ...` inline en zsh.
- `SKIPPED: empty diff`: la rama ya está en la base; usar `--base HEAD~N`.
- Duplicados falsos de `dist/` o `coverage/` en FE: existen local y no en el CI.
- El `python3` del sistema puede ser 3.9; los scripts ya usan `from __future__ import annotations`.

## 5. Duplicación y diseño

Si Sonar marca duplicación entre componentes de **features distintas**, no los unifiques en una base compartida solo para bajar el porcentaje: acopla dos features por su UI y es peor que la duplicación. Extraer solo helpers puros sin estado (fechas, builders de notificación) y, como mucho, una clase base acotada al bloque idéntico de bajo acoplamiento. Ver `skills/learnings/sonar-new-code-duplication-locate-and-fix`.

## 6. Revisión de .html en Angular

Un elemento no interactivo (`label`, `div`, `span`) con `(click)` necesita su evento de teclado equivalente (`(keydown)`/`(keyup)`), o Sonar lo marca como **Bug** y tumba el rating de Reliability. Revisarlo también en las plantillas, no solo en `.ts`.

## Skills relacionadas

`sonar-local-gate`, `flow-security-gate`, `learnings/sonar-local-docker-gate-setup`, `learnings/sonar-local-gate-staged-pre-commit`.
