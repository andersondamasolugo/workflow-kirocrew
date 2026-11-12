"""
Workflow: flow-docs-dispatch  ·  CARRIL B (multi-agente)

Flujo de DOCUMENTACIÓN ejecutable de forma INDEPENDIENTE (sin PO). README/CHANGELOG/OpenAPI/
ADRs/doc comments según estándar corporativo (changelog español, README por operación), sin
cambio de comportamiento en runtime, y verifica que la doc coincide con el código actual.

Relación con master-dispatch: el master corre el PO y despacha aquí; este es el flujo de docs
aislado, lanzable solo con repo+scope. Helper COPIADO a propósito (el sandbox prohíbe import
entre workflows). Fuente de verdad: flow-docs/SKILL.md.

args: repo (str, oblig) · scope (str, oblig).
"""

META = {
    "name": "flow-docs-dispatch",
    "description": "Flujo de DOCUMENTACIÓN aislado: escribir doc corporativa + sync check con el código, sin cambio de runtime, sobre un scope ya clasificado.",
    "phases": ["write", "sync-check"],
}


async def _run_docs(ctx, repo, scope):
    ctx.phase("Docs · escribir")
    write = await ctx.agent(
        f"DOCUMENTACIÓN (flow-docs) estándar corporativo (changelog español, README por "
        f"operación, OpenAPI). Sin cambio de runtime, sin secretos.\n\n{scope}",
        agent="dev-backend", cwd=repo, label="write-docs",
    )
    ctx.phase("Docs · sync check")
    sync = await ctx.agent(
        "Verifica que la doc coincide con el código actual (endpoints/params/ejemplos), sin "
        "referencias obsoletas.",
        agent="dev-backend", cwd=repo, label="sync-check",
    )
    return True, f"Escritura:\n{write}\nSync:\n{sync}"


async def workflow(ctx):
    repo = ctx.args.get("repo")
    scope = ctx.args.get("scope")
    if not repo or not scope:
        return "BLOCKED: falta 'repo' y/o 'scope' (este flujo recibe un scope ya clasificado; usa master-dispatch si necesitas el PO gate)."
    ctx.log(f"[flow-docs] repo={repo} · scope={scope}")
    ok, summary = await _run_docs(ctx, repo, scope)
    estado = "✅ completado" if ok else "⛔ detenido (escala a decisión humana)"
    return f"{estado} — flow-docs.\n\nScope: {scope}\n\n{summary}\n\n(Sin commit ni push.)"
