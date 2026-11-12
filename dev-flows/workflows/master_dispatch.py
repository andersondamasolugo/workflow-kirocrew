"""
Workflow: master-dispatch  ·  CARRIL B (multi-agente, requiere RAM >= spawn_min_memory_gb)

Pipeline maestro end-to-end: arranca en el PO, analiza la HU de Jira, clasifica el tipo y
ejecuta las fases del tipo correspondiente EN ESTE MISMO workflow (nodos inline).

Por qué inline y NO ctx.workflow: el runtime de este host NO cablea ctx.workflow
('not available in this runtime, no wired port') — verificado con workflow_run+workflow_status.
La superficie ctx real es: agent, agent_results, args, budget, log, now, nudge, owner_dm,
parallel, phase, pipeline. Así que el despacho por anidación de sub-workflows NO es posible
aquí; el maestro replica las fases del tipo elegido usando ctx.agent / ctx.parallel.

Fuente de verdad de las fases: flow-po/SKILL.md + flow-<tipo>/SKILL.md. Fallback: ./README.md
(Carril A si RAM < spawn_min_memory_gb). Este maestro es el punto de entrada PO->dispatch.

FLUJOS SEPARADOS (ejecutables solos, sin PO): cada tipo tiene además su propio workflow
autónomo en este mismo directorio — flow_frontend_dispatch.py, flow_backend_dispatch.py,
flow_fullstack_dispatch.py, flow_hotfix_dispatch.py, flow_data_migration_dispatch.py,
flow_test_dispatch.py, flow_docs_dispatch.py. Reciben `repo` + `scope` (ya clasificado) y
corren SOLO su tipo. Úsalos cuando el tipo ya está decidido y no necesitas el PO gate. Este
maestro NO delega en ellos (ctx.workflow no está cableado en este runtime): replica las
mismas fases inline vía DISPATCH. Por eso los helpers (_gate_loop, _visual_prompt, ...) están
DUPLICADOS entre el maestro y cada flujo separado — es la misma restricción de sandbox que
impide `import` entre workflows. Si tocas un helper aquí, refléjalo en los flujos que lo copian.

⚠️ DEUDA CONOCIDA (prompts-espejo): el runtime de este host NO cablea `ctx.workflow`, así que
este workflow NO puede delegar la ejecución a un sub-workflow del skill; los nodos DELEGAN por
prompt ("Sigue las fases de flow-<tipo>/SKILL.md ..."). Mantén esos prompts DELGADOS: deben
apuntar al SKILL.md, no re-codificar sus fases. Si cambias un SKILL.md que altere el CONTRATO
(veredictos, orden de gates, umbral), revisa que los prompts aquí sigan apuntando bien.

AGNÓSTICO DE PROYECTO: este maestro NO nombra framework/proyecto. El build/serve/test y el
design system los define el PROYECTO (su SKILL/README/steering) + el agente `dev-front-*`
correcto; la verificación visual usa el MOTOR del agente (web-verify/scripts/run-visual-nav.mjs)
con el mapa del proyecto vía `--map`. No hay strings de ng/vite/tsconfig/jest/td-* aquí.

Grafo:
    PO gate (dev-po, @jira, schema) -> {verdict, flow_type, scope}
        BLOQUEADO -> detente (decisión humana)
        APROBADO  -> ejecuta inline las fases de flow_type (gate transversal + loop donde aplica)

args: repo (str, oblig) · UNO de: jira_key (str) o requirement (str, texto) ·
      design_system ("tienda"|"bolivar-ui") ·
      criteria_confirmed (str, opcional — Modo B: criterios ya confirmados por el humano,
      salta la PROPUESTA y va directo a evaluar/APROBAR) ·
      figma_node (str, opcional — nodo Figma de referencia p.ej. "4242-14110"; si está presente
      en un flujo frontend, la verificación visual imagen-vs-imagen es OBLIGATORIA y BLOQUEANTE) ·
      figma_mobile_node (str, opcional — nodo Figma del layout móvil, p.ej. "4061-22024")

VERIFICACIÓN VISUAL (gate duro): cuando el tipo es frontend/fullstack y hay figma_node, tras
estándares+seguridad PASS corre un nodo de verificación visual que DEBE extraer el screenshot
del nodo Figma (baseline), capturar el render y compararlos imagen-vs-imagen. Debe terminar en
'VERDICT: VISUAL PASS' para dar el frontend por hecho. 'VISUAL FAIL' reinicia el loop de
corrección; 'VISUAL BLOCKED' (no se puede levantar el render) DETIENE la entrega — nunca PASS a ojo.
"""

MAX_ITERS = 3

META = {
    "name": "master-dispatch",
    "description": "Pipeline maestro: PO analiza la HU de Jira, clasifica el tipo y ejecuta sus fases inline.",
    "phases": ["po-gate", "implement", "audit", "gate-loop", "verify", "deliver"],
}

PO_SCHEMA = {
    "type": "object",
    "properties": {
        # PROPUESTA: solo Modo B (texto sin HU) — el PO deriva criterios y espera confirmación humana.
        "verdict": {"type": "string", "enum": ["APROBADO", "PROPUESTA", "BLOQUEADO"]},
        "flow_type": {
            "type": "string",
            "enum": ["frontend", "backend", "fullstack", "data-migration", "hotfix", "test", "docs"],
        },
        "scope": {"type": "string"},
        # criteria: criterios de aceptación derivados (Modo B) que se devuelven para confirmar.
        "criteria": {"type": "string"},
        "missing": {"type": "string"},
    },
    "required": ["verdict"],
}


def _failed(result) -> bool:
    return result is None or "VERDICT: PASS" not in str(result)


def _visual_status(result) -> str:
    """Clasifica el veredicto del nodo de verificación visual.
    Devuelve 'PASS', 'PASS_WITH_NOTES', 'FAIL' o 'BLOCKED'.
    - PASS: coincide, sin desviaciones.
    - PASS_WITH_NOTES: coincide ≥85% (umbral de aprobación) pero con desviaciones MENORES
      que se informan; NO bloquea — 85% es el criterio de aprobación, no el piso para fallar.
    - FAIL: por debajo del 85% / desviaciones que rompen el diseño.
    - BLOCKED: no se pudo levantar el render.
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
    navegación + pixel_diff del agente): el detalle operativo vive en esos SKILL.md, no aquí.
    Agnóstico de framework/proyecto: NO nombra ng/vite/tsconfig ni rutas de runner del repo.
    Devuelve None si no hay figma_node (sin referencia no hay comparación que exigir)."""
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
    verificación visual BLOQUEANTE contra Figma: FAIL reintenta implement sin gastar en el resto,
    BLOCKED detiene. Solo con VISUAL PASS audita el diff (standards ‖ security) y build/tests.
    Loop de corrección hasta MAX_ITERS. Devuelve (ok, resumen).

    pre_implemented=True: la implementación YA ocurrió antes de llamar a este loop (p.ej. un
    fan-out paralelo de secciones). En la 1ª iteración se SALTA el nodo implement y se entra
    directo al gate (visual -> auditoría -> build/tests). Los reintentos por corrección sí
    vuelven a implementar con el agente dado."""
    correction = ""
    visual_notes = ""  # desviaciones menores informadas por PASS_WITH_NOTES (no bloquean)
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

        # --- GATE VISUAL PRIMERO (bloqueante) ---
        # La verificación visual corre ANTES de estándares/seguridad/tests: si el render no
        # coincide con el Figma, reintentamos implement SIN gastar tokens en auditar/testear
        # algo que el visual rechazaría igual. Solo cuando VISUAL PASS seguimos al resto.
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
                continue  # reintenta implement; NO gasta en estándares/seguridad/tests todavía
            if status == "PASS_WITH_NOTES":
                # ≥85%: APRUEBA pero informa las desviaciones menores. No bloquea.
                visual_notes = visual
            # PASS o PASS_WITH_NOTES -> seguimos a estándares/seguridad/tests

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

    # --- Fan-out paralelo de secciones (opt-in vía args) ---
    # parallel_sections: lista de {"label","prompt"} independientes que se implementan EN PARALELO.
    # prereq (opcional): {"label","prompt"} que se implementa PRIMERO en serie (su salida es
    #   prerequisito de las secciones, p.ej. un componente base que las demás consumen).
    # assemble (opcional): {"prompt"} que ENSAMBLA las secciones en la página tras el fan-out.
    # Cuando hay parallel_sections, la implementación ocurre aquí (olas) y el gate solo verifica.
    sections = ctx.args.get("parallel_sections")
    if sections:
        base = (
            f"Contexto del requerimiento (NO amplíes alcance):\n{scope}\n\n"
            f"Sigue las fases de `flow-frontend/SKILL.md` y el steering del PROYECTO: design system "
            f"al 100% con los tokens del DS del proyecto y fallback (NUNCA crear variables nuevas), "
            f"convenciones del framework del proyecto, accesibilidad de teclado, data-qa-id. "
            f"NO commit/push."
        )
        # Ola 0: prerequisito en serie (su contrato lo consumen las secciones)
        prereq = ctx.args.get("prereq")
        if prereq:
            ctx.phase(f"FRONTEND · prerequisito ({prereq.get('label','prereq')})")
            pr_prompt = f"{base}\n\nTAREA (prerequisito, créalo primero con su contrato input/output definido):\n{prereq['prompt']}"
            ctx.log(f"[FRONTEND-prereq] PROMPT ENVIADO:\n{pr_prompt}")
            pr_res = await ctx.agent(pr_prompt, agent=front, cwd=repo, label="FRONTEND-prereq")
            ctx.log(f"[FRONTEND-prereq] RESPUESTA:\n{pr_res}")
            base += f"\n\nPREREQUISITO YA IMPLEMENTADO (consúmelo, no lo recrees):\n{pr_res}"

        # Ola 1: secciones independientes EN PARALELO
        ctx.phase(f"FRONTEND · fan-out {len(sections)} secciones en paralelo")
        tasks = []
        for sec in sections:
            sec_prompt = f"{base}\n\nTAREA (implementa SOLO esta sección, no toques las otras):\n{sec['prompt']}"
            ctx.log(f"[FRONTEND-{sec['label']}] PROMPT ENVIADO:\n{sec_prompt}")
            tasks.append(lambda p=sec_prompt, lb=sec['label']: ctx.agent(p, agent=front, cwd=repo, label=f"FRONTEND-{lb}"))
        results = await ctx.parallel(tasks)
        for sec, res in zip(sections, results):
            ctx.log(f"[FRONTEND-{sec['label']}] RESPUESTA:\n{res}")

        # Ola 2: ensamblado en la página (integra las secciones, wiring, preserva lo viejo)
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

        # El gate NO reimplementa en la 1ª iteración: ya está hecho por el fan-out.
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

    # --- Camino monolítico (sin fan-out): un agente implementa todo en serie ---
    return await _gate_loop(
        ctx, agent=front, repo=repo,
        task=f"Implementa (frontend) siguiendo las fases de `flow-frontend/SKILL.md`; verifica con "
             f"el BUILD REAL del proyecto (el comando que su SKILL/README define; NO asumas ng/vite). "
             f"NO commit/push.\n\nRequerimiento: {scope}{figma_line}",
        verify_prompt="Corre los tests afectados con el runner de tests del proyecto (el que su SKILL/README define) con cobertura. Pega el resultado.",
        label="FRONTEND",
        visual_verify=_visual_prompt(ctx, repo),
    )


async def _run_backend(ctx, repo, scope, agent="dev-backend"):
    return await _gate_loop(
        ctx, agent=agent, repo=repo,
        task=f"Implementa (backend) siguiendo flow-backend: stack aprobado, tipado, validación, "
             f"consultas parametrizadas, API First. NO commit/push.\n\nRequerimiento: {scope}",
        verify_prompt="Compila con el build real del stack, corre tests afectados con cobertura y "
                      "valida el contrato del endpoint. Pega la salida.",
        label="BACKEND",
    )


async def _run_fullstack(ctx, repo, scope):
    """FULLSTACK contract-first PARALELO (metodología estándar).

    El frontend DEPENDE del contrato del backend, así que NO se paraleliza a ciegas:
      Ola 0 (serial): fija el CONTRATO de la API (documento + tipos) — única fuente de verdad.
      Ola 1 (paralelo): backend ‖ frontend se IMPLEMENTAN a la vez, ambos contra ese contrato.
      Ola 2: gate transversal (standards ‖ security) con loop de corrección, build/tests, e integración
             que verifica que ambos lados concuerdan con el contrato.
    Solo IMPLEMENT corre en paralelo (una llamada por lado) para no anidar ctx.parallel dentro de ctx.parallel;
    el gate va después, una sola vez, sobre el diff combinado."""
    front = _front_agent(ctx)
    base = (
        f"Contexto y criterios (NO amplíes alcance):\n{scope}\n\n"
        f"Sigue flow-* y clean code, sin 'any', consultas/args parametrizados. NO commit/push."
    )

    # --- Ola 0: contrato (serial), prerequisito compartido de ambos lados ---
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

    # --- Ola 1: backend ‖ frontend (paralelo), cada uno contra el contrato ---
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

    # --- Ola 2: gate transversal (standards ‖ security) con loop de corrección ---
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

    # --- verificación build/tests de ambos lados ---
    ctx.phase("FULLSTACK · verificación (build/tests ambos lados)")
    verify = await ctx.agent(
        "Corre el build real y los tests afectados de AMBOS lados (backend y frontend). Si hay figma_node, "
        "incluye la verificación visual imagen-vs-imagen. Pega la salida real.",
        agent=front, cwd=repo, label="FULLSTACK-verify",
    )
    ctx.log(f"[FULLSTACK-verify] RESPUESTA:\n{verify}")

    # --- integración: ambos lados concuerdan con el contrato de la Ola 0 ---
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


async def _run_hotfix(ctx, repo, scope):
    return await _gate_loop(
        ctx, agent="dev-backend", repo=repo,
        task=f"HOTFIX: reproduce la CAUSA RAÍZ y aplica el CAMBIO MÍNIMO. Build real + tests "
             f"afectados. NO commit/push.\n\nIncidente: {scope}",
        verify_prompt="Demuestra que el incidente está resuelto sin regresión. Pega la evidencia.",
        label="HOTFIX",
    )


async def _run_data_migration(ctx, repo, scope):
    return await _gate_loop(
        ctx, agent="dev-database", repo=repo,
        task=f"Migración versionada, compatible hacia atrás (expand/contract), idempotente, con "
             f"up + down/rollback. NUNCA DROP destructivo sin respaldo. NO commit/push.\n\n{scope}",
        verify_prompt="Valida en test env: up, rollback restaura, EXPLAIN sobre consultas afectadas, "
                      "código compila con el esquema nuevo. Pega la evidencia.",
        label="MIGRACIÓN",
    )


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


DISPATCH = {
    "frontend": _run_frontend,
    "backend": _run_backend,
    "fullstack": _run_fullstack,
    "hotfix": _run_hotfix,
    "data-migration": _run_data_migration,
    "test": _run_test,
    "docs": _run_docs,
}


async def workflow(ctx):
    repo = ctx.args.get("repo")
    jira_key = ctx.args.get("jira_key")
    requirement = ctx.args.get("requirement")
    if not repo or (not jira_key and not requirement):
        return "BLOCKED: falta 'repo' y al menos uno de 'jira_key' o 'requirement'."

    fuente = f"HU {jira_key}" if jira_key else "requerimiento en texto"

    # --- Nodo 1: PO gate — valida la calidad del requerimiento (con o sin Jira) ---
    ctx.phase(f"PO gate — análisis del {fuente}")
    if jira_key:
        origen = (
            f"MODO A (con HU). Trae la HU {jira_key} con el MCP nativo de Jira "
            f"(@jira -> jira_get_issue) y evalúala CRÍTICAMENTE. Que exista NO es aprobación: "
            f"BLOQUEA si tiene vacíos, criterios no testables, criterios innecesarios/redundantes, "
            f"alcance ambiguo o contradicciones."
        )
    else:
        confirmed = ctx.args.get("criteria_confirmed")
        if confirmed:
            origen = (
                f"MODO B (sin HU) — criterios YA confirmados por el humano. Requerimiento:\n"
                f"---\n{requirement}\n---\nCriterios confirmados:\n{confirmed}\n---\n"
                f"Trátalos como aceptados: NO vuelvas a PROPUESTA, evalúa suficiencia y APRUEBA "
                f"si están completos."
            )
        else:
            origen = (
                f"MODO B (sin HU). NO hay clave Jira. DERIVA los criterios de aceptación testables "
                f"a partir de ESTE requerimiento en texto (no inventes más allá de lo pedido; "
                f"extrae lo implícito y decláralo):\n---\n{requirement}\n---\n"
                f"Si el texto alcanza para derivarlos, devuelve verdict=PROPUESTA con 'criteria' "
                f"(la lista testable) y 'flow_type'/'scope', y DETENTE para confirmación humana. "
                f"Si el texto es insuficiente, verdict=BLOQUEADO con 'missing'."
            )
    po = await ctx.agent(
        f"Ejecuta flow-po. {origen}\n\n"
        f"Aplica la MISMA checklist: criterios de aceptación TESTABLES, alcance claro "
        f"(qué sí / qué no), entradas/salidas con ejemplos, casos límite, manejo de error, "
        f"dependencias, restricciones. Veredictos posibles: "
        f"APROBADO (Modo A que cumple, o Modo B ya confirmado) -> da flow_type "
        f"(frontend|backend|fullstack|data-migration|hotfix|test|docs) y scope (≤5 líneas); "
        f"PROPUESTA (solo Modo B sin confirmar) -> da criteria + flow_type + scope y detente; "
        f"BLOQUEADO -> da missing. No inventes criterios; ambiguo = BLOQUEADO.",
        agent="dev-po", schema=PO_SCHEMA, label="po-gate",
    )

    if po is None:
        return f"BLOCKED: el PO no devolvió veredicto para el {fuente}."
    ctx.log(f"[po-gate] VEREDICTO PO: {po}")

    # Modo B: el PO derivó criterios y espera confirmación humana antes de desarrollar.
    if po.get("verdict") == "PROPUESTA":
        return (
            f"## 📝 PROPUESTA de criterios — {fuente}\n\n"
            f"El PO derivó los criterios de aceptación y **espera tu confirmación antes de desarrollar**.\n\n"
            f"### Criterios de aceptación\n\n"
            f"{po.get('criteria') or '_(sin detalle)_'}\n\n"
            f"### Clasificación\n\n"
            f"- **Tipo:** `{po.get('flow_type') or 'sin clasificar'}`\n"
            f"- **Alcance:** {po.get('scope') or '_(sin resumen)_'}\n\n"
            f"---\n\n"
            f"**Para continuar:** relanza el workflow con el arg `criteria_confirmed` "
            f"(los criterios ya ajustados), o reformula `requirement`."
        )

    if po.get("verdict") != "APROBADO":
        remedio = (
            "Corrige la HU en Jira y vuelve a ejecutar." if jira_key
            else "Reescribe el requerimiento con criterios de aceptación testables y vuelve a ejecutar."
        )
        return (
            f"⛔ {fuente} BLOQUEADO por el PO — decisión humana.\n\n"
            f"Falta:\n{po.get('missing') or '(sin detalle)'}\n\n{remedio}"
        )

    flow_type = po.get("flow_type")
    runner = DISPATCH.get(flow_type)
    if runner is None:
        return f"✅ {fuente} APROBADO, pero el tipo '{flow_type}' no tiene runner inline."

    scope = po.get("scope") or (requirement or f"Implementar la HU {jira_key}")
    ctx.log(f"PO APROBADO. Tipo: {flow_type}. Scope: {scope}")
    ok, summary = await runner(ctx, repo, scope)

    estado = "✅ completado" if ok else "⛔ detenido (escala a decisión humana)"
    return (
        f"{estado} — pipeline maestro ({fuente}).\n\n"
        f"PO: APROBADO · tipo: {flow_type}\nScope: {scope}\n\n{summary}\n\n(Sin commit ni push.)"
    )
