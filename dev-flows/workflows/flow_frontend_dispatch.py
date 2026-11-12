"""
Workflow: flow-frontend-dispatch  ·  CARRIL B (multi-agente)

Flujo SOLO-FRONTEND ejecutable de forma INDEPENDIENTE (sin pasar por el PO).
Recibe un `scope` YA clasificado y ejecuta las fases de flow-frontend: implement ->
verificación visual (si hay figma_node) -> auditoría standards‖security -> build/tests,
con loop de corrección. Opcional: fan-out paralelo de secciones.

Relación con master-dispatch: el master corre el PO gate, clasifica el tipo y despacha;
este workflow es el flujo frontend aislado, lanzable solo con repo+scope. Los helpers
(_gate_loop, _visual_prompt, ...) están COPIADOS aquí a propósito: el sandbox de workflows
prohíbe `import` entre módulos y `ctx.workflow` no está cableado, así que cada flujo es
autónomo. Fuente de verdad de las fases: flow-frontend/SKILL.md.

args: repo (str, oblig) · scope (str, oblig — requerimiento ya clasificado) ·
      design_system ("tienda"|"bolivar-ui", opcional) ·
      figma_node / figma_mobile_node (str, opcional — activan la verificación visual bloqueante) ·
      parallel_sections / prereq / assemble (opcional — fan-out paralelo de secciones).
"""

MAX_ITERS = 3

META = {
    "name": "flow-frontend-dispatch",
    "description": "Flujo SOLO-FRONTEND aislado: implement + visual + auditoría + build/tests, sobre un scope ya clasificado.",
    "phases": ["implement", "visual", "audit", "verify"],
}


def _failed(result) -> bool:
    return result is None or "VERDICT: PASS" not in str(result)


def _visual_status(result) -> str:
    """Clasifica el veredicto del nodo de verificación visual: PASS / PASS_WITH_NOTES / FAIL / BLOCKED.
    Ausencia de veredicto explícito = FAIL (a ojo NO cuenta)."""
    text = str(result) if result is not None else ""
    if "VERDICT: VISUAL PASS_WITH_NOTES" in text:
        return "PASS_WITH_NOTES"
    if "VERDICT: VISUAL PASS" in text:
        return "PASS"
    if "VERDICT: VISUAL BLOCKED" in text:
        return "BLOCKED"
    return "FAIL"


def _front_agent(ctx):
    ds = (ctx.args.get("design_system") or "tienda").lower()
    return "dev-front-bolivar-ui" if ds == "bolivar-ui" else "dev-front-tienda"


def _visual_prompt(ctx, repo):
    """Prompt del nodo de verificación visual imagen-vs-imagen contra Figma.
    DELEGA en la fase Visual de flow-frontend y en la capacidad web-verify (motor de
    navegación + pixel_diff del agente). Agnóstico de framework/proyecto.
    Devuelve None si no hay figma_node."""
    node = ctx.args.get("figma_node")
    if not node:
        return None
    mobile = ctx.args.get("figma_mobile_node")
    mobile_line = f" También el layout MÓVIL con el nodo `{mobile}` (viewport angosto)." if mobile else ""
    return (
        "Ejecuta la FASE VISUAL de `flow-frontend` (OBLIGATORIA y BLOQUEANTE) usando la capacidad "
        "`web-verify` del agente. Sigue su SKILL.md al pie de la letra; el detalle operativo "
        "(contrato autosuficiente del runner, umbral de aprobación, veredictos) vive ahí, no aquí.\n"
        f"- Baseline: extrae el nodo Figma `{node}` (get_screenshot / get_design_context) a "
        "$KIROCREW_SCRATCH.\n"
        "- Render FRESCO: levanta el dev server del proyecto (el comando/host que su SKILL/README "
        "define; NO asumas ninguno) y déjalo en loopback; emite el marcador "
        "'<!-- kirocrew:preview url=\"http://localhost:PORT\" -->'. Recaptura en ESTA iteración "
        "(no reutilices capturas viejas).\n"
        "- Deja el front en la pantalla objetivo con el MOTOR de navegación del agente "
        "(web-verify/scripts/run-visual-nav.mjs), pasándole el mapa del proyecto con `--map` y la "
        "`<SCREEN_KEY>` cuyo figmaNode es `{node}`; el motor navega como usuario real (respeta "
        "guards/stepper). NUNCA goto directo. Si falta la automatización de la pantalla, créala en "
        "el screens.map.json del proyecto siguiendo el contrato del SKILL, y reintenta.\n"
        "- Compara imagen-vs-imagen con `pixel_diff.py` (match% + changed_pixels% + heatmap) sobre "
        "el RECORTE del componente (mismo encuadre que el nodo). Revisa contenido, iconografía, "
        "tipografía, color (tokens del DS, no default), alineación, borde/radius, spacing y patrón "
        f"de layout.{mobile_line}\n"
        "- Embebe ambas imágenes con ![desc](/ruta/abs.png) y enumera las diferencias (MENOR / "
        "BLOQUEANTE).\n"
        "Última línea EXACTAMENTE una de: 'VERDICT: VISUAL PASS' · 'VERDICT: VISUAL PASS_WITH_NOTES' "
        "(≥ umbral, con desviaciones menores informadas; no bloquea) · 'VERDICT: VISUAL FAIL' · "
        "'VERDICT: VISUAL BLOCKED'. Nunca PASS a ojo ni sin las dos imágenes."
    )


async def _gate_loop(ctx, *, agent, repo, task, verify_prompt, label, visual_verify=None, pre_implemented=False):
    """Implementa con un agente. Si visual_verify está presente, corre PRIMERO un nodo de
    verificación visual BLOQUEANTE contra Figma: FAIL reintenta implement, BLOCKED detiene.
    Solo con VISUAL PASS audita el diff (standards ‖ security) y build/tests. Loop hasta MAX_ITERS.
    pre_implemented=True: la implementación YA ocurrió (fan-out); la 1ª iteración salta implement."""
    correction = ""
    visual_notes = ""
    for iteration in range(1, MAX_ITERS + 1):
        if pre_implemented and iteration == 1:
            ctx.log(f"[{label}-impl#1] PRE-IMPLEMENTADO por fan-out paralelo; se salta el nodo implement y se entra al gate.")
        else:
            ctx.phase(f"{label} · implement {iteration}")
            prompt = task
            if correction:
                prompt += f"\n\nCORRECCIÓN (no amplíes alcance):\n{correction}"
            ctx.log(f"[{label}-impl#{iteration}] PROMPT ENVIADO:\n{prompt}")
            impl = await ctx.agent(prompt, agent=agent, cwd=repo, label=f"{label}-impl#{iteration}")
            ctx.log(f"[{label}-impl#{iteration}] RESPUESTA:\n{impl}")

        if visual_verify:
            ctx.phase(f"{label} · verificación visual (Figma) {iteration}")
            ctx.log(f"[{label}-visual#{iteration}] PROMPT ENVIADO:\n{visual_verify}")
            visual = await ctx.agent(
                visual_verify, agent=agent, cwd=repo, label=f"{label}-visual#{iteration}",
            )
            ctx.log(f"[{label}-visual#{iteration}] RESPUESTA:\n{visual}")
            status = _visual_status(visual)
            if status == "BLOCKED":
                return False, (
                    f"{label}: VERIFICACIÓN VISUAL BLOCKED — no se pudo confrontar el render "
                    f"contra Figma (render/backend no disponible). No hay entrega sin verificación "
                    f"visual.\n{visual}"
                )
            if status == "FAIL":
                correction = (
                    f"VERIFICACIÓN VISUAL FAIL — el render NO coincide con el Figma. "
                    f"Corrige las desviaciones enumeradas (contenido/iconos/layout/tokens/"
                    f"spacing/tipografía/patrón móvil) sin ampliar alcance:\n{visual}"
                )
                continue
            if status == "PASS_WITH_NOTES":
                visual_notes = visual

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
            if visual_notes:
                visual_note = (
                    "\nVISUAL PASS_WITH_NOTES (≥85%, APROBADO con desviaciones menores informadas):\n"
                    f"{visual_notes}"
                )
            elif visual_verify:
                visual_note = "\nVISUAL PASS (verificado antes del resto del gate)."
            else:
                visual_note = ""
            return True, (
                f"{label}: estándares PASS, seguridad PASS." + visual_note
                + (f"\n{verify}" if verify else "")
            )
        correction = (
            f"HALLAZGOS ESTÁNDARES:\n{standards if _failed(standards) else 'PASS'}\n\n"
            f"HALLAZGOS SEGURIDAD:\n{security if _failed(security) else 'PASS'}"
        )
    return False, f"{label}: gate no superado tras {MAX_ITERS} iteraciones.\n{correction}"


async def _run_frontend(ctx, repo, scope):
    front = _front_agent(ctx)
    node = ctx.args.get("figma_node")
    figma_line = (
        f"\n\nReferencia visual OBLIGATORIA: nodo Figma `{node}`. El resultado se confrontará "
        f"imagen-vs-imagen contra ese nodo en la fase de verificación visual (gate bloqueante)."
        if node else ""
    )

    sections = ctx.args.get("parallel_sections")
    if sections:
        base = (
            f"Contexto del requerimiento (NO amplíes alcance):\n{scope}\n\n"
            f"Sigue las fases de `flow-frontend/SKILL.md` y el steering del PROYECTO: design system "
            f"al 100% con los tokens del DS del proyecto y fallback (NUNCA crear variables nuevas), "
            f"convenciones del framework del proyecto, accesibilidad de teclado, data-qa-id. "
            f"NO commit/push."
        )
        prereq = ctx.args.get("prereq")
        if prereq:
            ctx.phase(f"FRONTEND · prerequisito ({prereq.get('label','prereq')})")
            pr_prompt = f"{base}\n\nTAREA (prerequisito, créalo primero con su contrato input/output definido):\n{prereq['prompt']}"
            ctx.log(f"[FRONTEND-prereq] PROMPT ENVIADO:\n{pr_prompt}")
            pr_res = await ctx.agent(pr_prompt, agent=front, cwd=repo, label="FRONTEND-prereq")
            ctx.log(f"[FRONTEND-prereq] RESPUESTA:\n{pr_res}")
            base += f"\n\nPREREQUISITO YA IMPLEMENTADO (consúmelo, no lo recrees):\n{pr_res}"

        ctx.phase(f"FRONTEND · fan-out {len(sections)} secciones en paralelo")
        tasks = []
        for sec in sections:
            sec_prompt = f"{base}\n\nTAREA (implementa SOLO esta sección, no toques las otras):\n{sec['prompt']}"
            ctx.log(f"[FRONTEND-{sec['label']}] PROMPT ENVIADO:\n{sec_prompt}")
            tasks.append(lambda p=sec_prompt, lb=sec['label']: ctx.agent(p, agent=front, cwd=repo, label=f"FRONTEND-{lb}"))
        results = await ctx.parallel(tasks)
        for sec, res in zip(sections, results):
            ctx.log(f"[FRONTEND-{sec['label']}] RESPUESTA:\n{res}")

        assemble = ctx.args.get("assemble")
        if assemble:
            ctx.phase("FRONTEND · ensamblado de la página")
            asm_prompt = (
                f"{base}\n\nSECCIONES YA IMPLEMENTADAS (intégralas, no las recrees):\n"
                + "\n\n".join(f"[{s['label']}]\n{r}" for s, r in zip(sections, results))
                + f"\n\nTAREA DE ENSAMBLADO:\n{assemble['prompt']}"
            )
            ctx.log(f"[FRONTEND-assemble] PROMPT ENVIADO:\n{asm_prompt}")
            asm_res = await ctx.agent(asm_prompt, agent=front, cwd=repo, label="FRONTEND-assemble")
            ctx.log(f"[FRONTEND-assemble] RESPUESTA:\n{asm_res}")

        return await _gate_loop(
            ctx, agent=front, repo=repo,
            task=f"Implementa (frontend) siguiendo las fases de `flow-frontend/SKILL.md`; verifica con "
                 f"el BUILD REAL del proyecto (el comando que su SKILL/README define; NO asumas ng/vite). "
                 f"NO commit/push.\n\nRequerimiento: {scope}{figma_line}",
            verify_prompt="Corre los tests afectados con el runner de tests del proyecto (el que su SKILL/README define) con cobertura. Pega el resultado.",
            label="FRONTEND",
            visual_verify=_visual_prompt(ctx, repo),
            pre_implemented=True,
        )

    return await _gate_loop(
        ctx, agent=front, repo=repo,
        task=f"Implementa (frontend) siguiendo las fases de `flow-frontend/SKILL.md`; verifica con "
             f"el BUILD REAL del proyecto (el comando que su SKILL/README define; NO asumas ng/vite). "
             f"NO commit/push.\n\nRequerimiento: {scope}{figma_line}",
        verify_prompt="Corre los tests afectados con el runner de tests del proyecto (el que su SKILL/README define) con cobertura. Pega el resultado.",
        label="FRONTEND",
        visual_verify=_visual_prompt(ctx, repo),
    )


async def workflow(ctx):
    repo = ctx.args.get("repo")
    scope = ctx.args.get("scope")
    if not repo or not scope:
        return "BLOCKED: falta 'repo' y/o 'scope' (este flujo recibe un scope ya clasificado; usa master-dispatch si necesitas el PO gate)."
    ctx.log(f"[flow-frontend] repo={repo} · scope={scope}")
    ok, summary = await _run_frontend(ctx, repo, scope)
    estado = "✅ completado" if ok else "⛔ detenido (escala a decisión humana)"
    return f"{estado} — flow-frontend.\n\nScope: {scope}\n\n{summary}\n\n(Sin commit ni push.)"
