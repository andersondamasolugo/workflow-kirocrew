"""
Workflow: flow-fullstack-dispatch  ·  CARRIL B (multi-agente)

Flujo FULLSTACK ejecutable de forma INDEPENDIENTE (sin PO). Contract-first paralelo:
  Ola 0 (serial): fija el CONTRATO de la API (documento + tipos) — única fuente de verdad.
  Ola 1 (paralelo): backend ‖ frontend se implementan a la vez contra ese contrato.
  Ola 2: gate transversal (standards ‖ security) con loop, build/tests, e integración.

Relación con master-dispatch: el master corre el PO y despacha aquí; este workflow es el
flujo fullstack aislado, lanzable solo con repo+scope. Helpers COPIADOS a propósito (el
sandbox prohíbe import entre workflows). Fuente de verdad: flow-fullstack/SKILL.md.

args: repo (str, oblig) · scope (str, oblig) · design_system ("tienda"|"bolivar-ui", opcional) ·
      figma_node (str, opcional).
"""

MAX_ITERS = 3

META = {
    "name": "flow-fullstack-dispatch",
    "description": "Flujo FULLSTACK aislado contract-first: contrato -> backend‖frontend -> gate -> build/tests -> integración.",
    "phases": ["contrato", "implement", "gate", "verify", "integracion"],
}


def _failed(result) -> bool:
    return result is None or "VERDICT: PASS" not in str(result)


def _front_agent(ctx):
    ds = (ctx.args.get("design_system") or "tienda").lower()
    return "dev-front-bolivar-ui" if ds == "bolivar-ui" else "dev-front-tienda"


async def _run_fullstack(ctx, repo, scope):
    """FULLSTACK contract-first PARALELO (metodología estándar).
    Solo IMPLEMENT corre en paralelo (una llamada por lado) para no anidar ctx.parallel;
    el gate va después, una sola vez, sobre el diff combinado."""
    front = _front_agent(ctx)
    base = (
        f"Contexto y criterios (NO amplíes alcance):\n{scope}\n\n"
        f"Sigue flow-* y clean code, sin 'any', consultas/args parametrizados. NO commit/push."
    )

    # --- Ola 0: contrato (serial) ---
    ctx.phase("FULLSTACK · Ola 0 contrato (serial)")
    contract_prompt = (
        f"{base}\n\nTAREA (Ola 0): define el CONTRATO de la API entre frontend y backend como artefacto "
        f"compartido (documento + tipos/interface): endpoints, request/response, estados y errores. Es la ÚNICA "
        f"fuente de verdad que ambos lados consumirán. Solo el contrato; no implementes el resto todavía."
    )
    ctx.log(f"[FULLSTACK-contrato] PROMPT ENVIADO:\n{contract_prompt}")
    contract = await ctx.agent(contract_prompt, agent="dev-backend", cwd=repo, label="FULLSTACK-contrato")
    ctx.log(f"[FULLSTACK-contrato] RESPUESTA:\n{contract}")
    base += f"\n\nCONTRATO YA DEFINIDO (Ola 0) — respétalo EXACTAMENTE, no lo cambies:\n{contract}"

    # --- Ola 1: backend ‖ frontend (paralelo) ---
    ctx.phase("FULLSTACK · Ola 1 backend ‖ frontend (paralelo)")
    node = ctx.args.get("figma_node")
    figma_line = (f"\n\nReferencia visual: nodo Figma `{node}` (verificación imagen-vs-imagen en la fase de verificación)." if node else "")
    back_prompt = (
        f"{base}\n\nTAREA (BACKEND): implementa el servicio/endpoint contra el contrato siguiendo flow-backend "
        f"(stack aprobado, tipado, validación, consultas parametrizadas, API First)."
    )
    front_prompt = (
        f"{base}\n\nTAREA (FRONTEND): implementa la UI que consume el contrato siguiendo las fases de "
        f"`flow-frontend/SKILL.md`, design system del proyecto al 100%, y verifica con el BUILD REAL "
        f"del proyecto (el comando que su SKILL/README define).{figma_line}"
    )
    ctx.log(f"[FULLSTACK-backend] PROMPT ENVIADO:\n{back_prompt}")
    ctx.log(f"[FULLSTACK-frontend] PROMPT ENVIADO:\n{front_prompt}")
    back_res, front_res = await ctx.parallel([
        lambda: ctx.agent(back_prompt, agent="dev-backend", cwd=repo, label="FULLSTACK-backend"),
        lambda: ctx.agent(front_prompt, agent=front, cwd=repo, label="FULLSTACK-frontend"),
    ])
    ctx.log(f"[FULLSTACK-backend] RESPUESTA:\n{back_res}")
    ctx.log(f"[FULLSTACK-frontend] RESPUESTA:\n{front_res}")

    # --- Ola 2: gate transversal (standards ‖ security) con loop ---
    correction = ""
    passed = False
    for iteration in range(1, MAX_ITERS + 1):
        ctx.phase(f"FULLSTACK · gate {iteration}")
        audit = (
            "Audita SOLO el diff actual (git diff) de ambos lados. Última línea exactamente "
            "'VERDICT: PASS' o 'VERDICT: FAIL'."
        )
        standards, security = await ctx.parallel([
            lambda it=iteration: ctx.agent(audit, agent="dev-standards", cwd=repo, label=f"FULLSTACK-std#{it}"),
            lambda it=iteration: ctx.agent(audit, agent="dev-security", cwd=repo, label=f"FULLSTACK-sec#{it}"),
        ])
        ctx.log(f"[FULLSTACK-std#{iteration}] RESPUESTA:\n{standards}")
        ctx.log(f"[FULLSTACK-sec#{iteration}] RESPUESTA:\n{security}")
        if not _failed(standards) and not _failed(security):
            passed = True
            break
        correction = (
            f"HALLAZGOS ESTÁNDARES:\n{standards if _failed(standards) else 'PASS'}\n\n"
            f"HALLAZGOS SEGURIDAD:\n{security if _failed(security) else 'PASS'}"
        )
        fix_prompt = f"{base}\n\nCORRIGE estos hallazgos (backend y/o frontend), sin ampliar alcance:\n{correction}"
        ctx.log(f"[FULLSTACK-fix#{iteration}] PROMPT ENVIADO:\n{fix_prompt}")
        fix = await ctx.agent(fix_prompt, agent=front, cwd=repo, label=f"FULLSTACK-fix#{iteration}")
        ctx.log(f"[FULLSTACK-fix#{iteration}] RESPUESTA:\n{fix}")
    if not passed:
        return False, f"FULLSTACK: gate no superado tras {MAX_ITERS} iteraciones.\n{correction}"

    # --- verificación build/tests ---
    ctx.phase("FULLSTACK · verificación (build/tests ambos lados)")
    verify = await ctx.agent(
        "Corre el build real y los tests afectados de AMBOS lados (backend y frontend). Si hay figma_node, "
        "incluye la verificación visual imagen-vs-imagen. Pega la salida real.",
        agent=front, cwd=repo, label="FULLSTACK-verify",
    )
    ctx.log(f"[FULLSTACK-verify] RESPUESTA:\n{verify}")

    # --- integración: ambos lados concuerdan con el contrato ---
    ctx.phase("FULLSTACK · integración")
    integ = await ctx.agent(
        "Verifica que UI ↔ servicio concuerdan EXACTAMENTE con el contrato de la Ola 0 (endpoints, "
        "request/response, errores, estados). Reporta discrepancias. Pega el resumen.",
        agent=front, cwd=repo, label="FULLSTACK-integration",
    )
    ctx.log(f"[FULLSTACK-integration] RESPUESTA:\n{integ}")
    return True, (
        f"FULLSTACK contract-first paralelo PASS (contrato Ola 0 + backend‖frontend en paralelo).\n"
        f"Verificación:\n{verify}\nIntegración:\n{integ}"
    )


async def workflow(ctx):
    repo = ctx.args.get("repo")
    scope = ctx.args.get("scope")
    if not repo or not scope:
        return "BLOCKED: falta 'repo' y/o 'scope' (este flujo recibe un scope ya clasificado; usa master-dispatch si necesitas el PO gate)."
    ctx.log(f"[flow-fullstack] repo={repo} · scope={scope}")
    ok, summary = await _run_fullstack(ctx, repo, scope)
    estado = "✅ completado" if ok else "⛔ detenido (escala a decisión humana)"
    return f"{estado} — flow-fullstack.\n\nScope: {scope}\n\n{summary}\n\n(Sin commit ni push.)"
