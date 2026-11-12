# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Versionamiento Semántico](https://semver.org/lang/es/).

## [No publicado]

## [0.0.2] - 2026-11-12

### Agregado
- Se agregó el reporte automático de fallos de instalación: `scripts/report_install_issue.py` redacta tokens, correos, usuario y rutas, y con autorización del usuario crea un issue con la etiqueta `install-failure` (o imprime un link pre-llenado si `gh` no está disponible).
- Se agregó la plantilla de issue `install-failure` y la sección "Si algo falla durante la instalación" en `AGENTS.md`.

### Cambiado
- Los instaladores `install.sh` e `install.ps1` ahora indican cómo reportar el fallo.

## [0.0.1] - 2026-11-12

### Agregado
- Se agregó el kit inicial de flujo de desarrollo de Gestión Bienestar: 9 agentes `dev-*`, jueces de Judgment Day, flujos `flow-*`, guías `secure-coding-*`, Sonar local, SDD, commits por unidad de trabajo y PRs encadenados.
- Se agregaron 26 aprendizajes de HUs y PRs en `skills/learnings/`.
- Se agregó el steering de stack, seguridad, estilo, arquitectura, changelog y observabilidad.
- Se agregaron las guías de flujo completo, SDD/ODD/RDD, Sonar local, aprendizajes de PR y onboarding.
- Se agregaron `install.sh`, `AGENTS.md` para autoinstalación desde un chat de Kiro Crew y `scripts/check-secrets.sh`.
- Se agregó soporte para Windows: instalador `install.ps1` y guía `docs/06-windows.md` con las diferencias de tokens, Docker, Java y rutas. Pendiente de validar en una máquina Windows real.
- Se agregó el archivo `LICENSE` (MIT) para el contenido propio del kit.

### Corregido
- Se corrigió `sonar_local_gate.py` para que no falle en Windows al buscar `/usr/libexec/java_home` y para que encuentre `sonar-scanner.bat`.

### Seguridad
- Se reemplazó el host interno de JFrog por un placeholder en el steering y se retiraron versiones históricas de skills (`.versions`) antes de publicar.
