"""
Workflow: flow-test-dispatch  ·  CARRIL B (multi-agente)

Flujo de PRUEBAS ejecutable de forma INDEPENDIENTE (sin PO). Escribe/repara pruebas
Given/When/Then, mockea dependencias externas, y corre la suite afectada con cobertura (≥80%).
Un bug real de producción se REPORTA, no se enmascara.

Relación con master-dispatch: el master corre el PO y despacha aquí; este es el flujo de
tests aislado, lanzable solo con repo+scope. Helper COPIADO a propósito (el sandbox prohíbe
importar entre workflows). Fuente de verdad: flow-test/SKILL.md.

args: repo (str, oblig) · scope (str, oblig) · design_system ("tienda"|"bolivar-ui", opcional).
"""

META = {
    "name": "flow-test-dispatch",
    "description": "Flujo de PRUEBAS aislado: escribir tests Given/When/Then + cobertura ≥80%, sobre un scope ya clasificado.",
    "phases": ["write", "coverage"],
}


def _front_agent(ctx):
    ds = (ctx.args.get("design_system") or "tienda").lower()
    return "dev-front-bolivar-ui" if ds == "bolivar-ui" else "dev-front-tienda"


async def _run_test(ctx, repo, scope):
    front = _front_agent(ctx)
    ctx.phase("Tests · escribir")
    write = await ctx.agent(
        f"Trabajo de PRUEBAS (flow-test): Given/When/Then, mockea dependencias externas, solo "
        f"archivos de test. Un bug real de producción se REPORTA, no se enmascara.\n\n{scope}",
        agent=front, cwd=repo, label="write-tests",
    )
    ctx.phase("Tests · cobertura")
    cov = await ctx.agent(
        "Corre la suite afectada con cobertura (≥80%). Pega la salida real y reporta bugs de "
        "producción detectados sin corregir.",
        agent=front, cwd=repo, label="coverage",
    )
    return True, f"Escritura:\n{write}\nCobertura:\n{cov}"


async def workflow(ctx):
    repo = ctx.args.get("repo")
    scope = ctx.args.get("scope")
    if not repo or not scope:
        return "BLOCKED: falta 'repo' y/o 'scope' (este flujo recibe un scope ya clasificado; usa master-dispatch si necesitas el PO gate)."
    ctx.log(f"[flow-test] repo={repo} · scope={scope}")
    ok, summary = await _run_test(ctx, repo, scope)
    estado = "✅ completado" if ok else "⛔ detenido (escala a decisión humana)"
    return f"{estado} — flow-test.\n\nScope: {scope}\n\n{summary}\n\n(Sin commit ni push.)"
