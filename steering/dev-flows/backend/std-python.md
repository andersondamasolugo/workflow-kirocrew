---
inclusion: fileMatch
fileMatchPattern: ["**/*.py", "pyproject.toml", "requirements*.txt"]
---

# Reglas Python (PEP 8 + prácticas profesionales)

## Estilo y formato
- Cumplir PEP 8. Formatear con `black` (o `ruff format`); lint con `ruff`.
- Nombres: `snake_case` funciones/variables, `PascalCase` clases, `UPPER_SNAKE` constantes, `_prefijo` para privados.
- Imports en tres bloques: stdlib, terceros, locales. Nunca `from x import *`.
- f-strings para interpolación; nunca concatenación con `+`.

## Tipado
- Type hints obligatorios en firmas públicas: `def get_user(user_id: int) -> User | None:`.
- Validar datos externos con `pydantic` o `dataclasses` + validación explícita.
- Ejecutar `mypy` (o `pyright`) en modo estricto en CI.

## Errores y recursos
- Excepciones específicas: capturar `ValueError`, nunca `except:` desnudo ni `except Exception: pass`.
- Crear excepciones de dominio propias (`class OrderNotFoundError(Exception)`).
- Context managers (`with`) para archivos, conexiones y locks.
- Logging con el módulo `logging` (o `structlog`), nunca `print` en producción. No loguear datos sensibles.

## Patrones recomendados
- Composición sobre herencia; herencia solo para jerarquías reales.
- Inyección de dependencias por constructor; evitar singletons y estado global.
- Repositorio para acceso a datos; servicios para lógica de negocio.
- Generadores/iteradores para colecciones grandes en lugar de listas en memoria.
- `dataclasses` o `pydantic.BaseModel` para DTOs; evitar dicts sin esquema entre capas.

## Anti-patrones prohibidos
- Argumentos mutables por defecto (`def f(items=[])`).
- Lógica en `__init__.py`.
- Modificar `sys.path` en runtime.
- Variables globales mutables entre módulos.

## Proyecto y dependencias
- `pyproject.toml` como única fuente de configuración; entornos virtuales siempre (`venv`, `uv` o `poetry`).
- Versiones fijadas (lockfile) para builds reproducibles.
- Estructura: `src/<paquete>/` para código, `tests/` espejo de `src/`.

## Asincronía y web moderna
- `async/await` de punta a punta en frameworks asíncronos (FastAPI, aiohttp): nunca llamadas bloqueantes (requests, time.sleep) dentro de corrutinas — usar `httpx.AsyncClient`, `asyncio.sleep`.
- FastAPI: modelos `pydantic` para request/response, dependencias con `Depends`, routers por dominio.
- Django: lógica en servicios/managers, no en vistas; consultas con `select_related`/`prefetch_related` para evitar N+1.
- Tooling moderno recomendado: `uv` para entornos/dependencias, `ruff` (lint + format) como estándar único.

## Testing
- `pytest` con fixtures; parametrizar casos con `@pytest.mark.parametrize`.
- Mockear solo bordes (red, disco, reloj); no mockear lógica propia.
- Cobertura mínima orientativa: 80% en lógica de negocio.
