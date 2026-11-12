"""
Workflow: flow-data-migration-dispatch  ·  CARRIL B (multi-agente)

Flujo DATA-MIGRATION ejecutable de forma INDEPENDIENTE (sin PO). Migración versionada,
compatible hacia atrás (expand/contract), idempotente, con up + down/rollback; audita
standards‖security, valida en test env, con loop de corrección.

Relación con master-dispatch: el master corre el PO y despacha aquí; este es el flujo de
migración aislado, lanzable solo con repo+scope. Helper _gate_loop COPIADO a propósito (el
sandbox prohíbe import entre workflows). Fuente de verdad: flow-data-migration/SKILL.md.

args: repo (str, oblig) · scope (str, oblig).
"""

MAX_ITERS = 3

META = {
    "name": "flow-data-migration-dispatch",
    "description": "Flujo DATA-MIGRATION aislado: migración versionada expand/contract + rollback + auditoría + validación en test env, sobre un scope ya clasificado.",
    "phases": ["implement", "audit", "verify"],
}


def _failed(result) -> bool:
    return result is None or "VERDICT: PASS" not in str(result)


async def _gate_loop(ctx, *, agent, repo, task, verify_prompt, label):
    """Implementa con un agente, audita el diff (standards ‖ security) y corre build/tests.
    Loop de corrección hasta MAX_ITERS. Devuelve (ok, resumen)."""
    correction = ""
    for iteration in range(1, MAX_ITERS + 1):
        ctx.phase(f"{label} · implement {iteration}")
        prompt = task
        if correction:
            prompt += f"\n\nCORRECCIÓN (no amplíes alcance):\n{correction}"
        ctx.log(f"[{label}-impl#{iteration}] PROMPT ENVIADO:\n{prompt}")
        impl = await ctx.agent(prompt, agent=agent, cwd=repo, label=f"{label}-impl#{iteration}")
        ctx.log(f"[{label}-impl#{iteration}] RESPUESTA:\n{impl}")

        ctx.phase(f"{label} · auditoría {iteration}")
        audit = (
            "Audita SOLO el diff actual (git diff). Última línea exactamente "
            "'VERDICT: PASS' o 'VERDICT: FAIL'."
        )
        ctx.log(f"[{label}-audit#{iteration}] PROMPT ENVIADO (a dev-standards y dev-security):\n{audit}")
        standards, security = await ctx.parallel([
            lambda it=iteration: ctx.agent(audit, agent="dev-standards", cwd=repo, label=f"{label}-std#{it}"),
            lambda it=iteration: ctx.agent(audit, agent="dev-security", cwd=repo, label=f"{label}-sec#{it}"),
        ])
        ctx.log(f"[{label}-std#{iteration}] RESPUESTA:\n{standards}")
        ctx.log(f"[{label}-sec#{iteration}] RESPUESTA:\n{security}")
        if not _failed(standards) and not _failed(security):
            verify = None
            if verify_prompt:
                ctx.phase(f"{label} · verificación (build/tests)")
                ctx.log(f"[{label}-verify] PROMPT ENVIADO:\n{verify_prompt}")
                verify = await ctx.agent(verify_prompt, agent=agent, cwd=repo, label=f"{label}-verify")
                ctx.log(f"[{label}-verify] RESPUESTA:\n{verify}")
            return True, (
                f"{label}: estándares PASS, seguridad PASS." + (f"\n{verify}" if verify else "")
            )
        correction = (
            f"HALLAZGOS ESTÁNDARES:\n{standards if _failed(standards) else 'PASS'}\n\n"
            f"HALLAZGOS SEGURIDAD:\n{security if _failed(security) else 'PASS'}"
        )
    return False, f"{label}: gate no superado tras {MAX_ITERS} iteraciones.\n{correction}"


async def _run_data_migration(ctx, repo, scope):
    return await _gate_loop(
        ctx, agent="dev-database", repo=repo,
        task=f"Migración versionada, compatible hacia atrás (expand/contract), idempotente, con "
             f"up + down/rollback. NUNCA DROP destructivo sin respaldo. NO commit/push.\n\n{scope}",
        verify_prompt="Valida en test env: up, rollback restaura, EXPLAIN sobre consultas afectadas, "
                      "código compila con el esquema nuevo. Pega la evidencia.",
        label="MIGRACIÓN",
    )


async def workflow(ctx):
    repo = ctx.args.get("repo")
    scope = ctx.args.get("scope")
    if not repo or not scope:
        return "BLOCKED: falta 'repo' y/o 'scope' (este flujo recibe un scope ya clasificado; usa master-dispatch si necesitas el PO gate)."
    ctx.log(f"[flow-data-migration] repo={repo} · scope={scope}")
    ok, summary = await _run_data_migration(ctx, repo, scope)
    estado = "✅ completado" if ok else "⛔ detenido (escala a decisión humana)"
    return f"{estado} — flow-data-migration.\n\nScope: {scope}\n\n{summary}\n\n(Sin commit ni push.)"
