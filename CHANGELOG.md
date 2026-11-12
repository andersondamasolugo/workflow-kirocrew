# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Versionamiento Semántico](https://semver.org/lang/es/).

## [No publicado]

### Agregado
- Se agregó soporte para Windows: instalador `install.ps1` y guía `docs/06-windows.md` con las diferencias de tokens, Docker, Java y rutas.
- Se agregó el archivo `LICENSE` (MIT) para el contenido propio del kit.
- Se agregó este `CHANGELOG.md`.

### Corregido
- Se corrigió `sonar_local_gate.py` para que no falle en Windows al buscar `/usr/libexec/java_home` y para que encuentre `sonar-scanner.bat`.

## [1.0.0] - 2026-11-12

### Agregado
- Se agregó el kit inicial de flujo de desarrollo de Gestión Bienestar: 9 agentes `dev-*`, jueces de Judgment Day, flujos `flow-*`, guías `secure-coding-*`, Sonar local, SDD, commits por unidad de trabajo y PRs encadenados.
- Se agregaron 26 aprendizajes de HUs y PRs en `skills/learnings/`.
- Se agregó el steering de stack, seguridad, estilo, arquitectura, changelog y observabilidad.
- Se agregaron las guías de flujo completo, SDD/ODD/RDD, Sonar local, aprendizajes de PR y onboarding.
- Se agregaron `install.sh`, `AGENTS.md` para autoinstalación desde un chat de Kiro Crew y `scripts/check-secrets.sh`.
