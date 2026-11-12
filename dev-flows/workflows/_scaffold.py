"""
_scaffold.py — PLANTILLA DE REFERENCIA para workflows de dev (Carril B).

⚠️ NO ES IMPORTABLE. El sandbox del motor de workflows PROHIBE `from ... import`
(verificado: "'from ... import' is not allowed in workflow scripts"). Por eso estos
helpers NO se importan: se COPIAN dentro de cada script de workflow como funciones
locales. Este archivo es la fuente de verdad del bloque a pegar.

Codifica en el RUNTIME las lecciones aprendidas, para que el grafo correcto sea el
camino facil y los gates no dependan de que el agente los recuerde:

- require_args(ctx, *names)         -> guard 'BLOCKED: faltan args' (permite validar el script
                                        ejecutandolo con args vacios: debe terminar finished + BLOCKED).
- audit_gate(ctx, repo, fix_agent,  -> auditoria dev-standards || dev-security en paralelo, con
             audit_prompt, ...)        loop de correccion (hasta max_iters). Devuelve True/False.
- contract_then_parallel(...)       -> patron contract-first: contrato -> componentes en paralelo
                                        -> ensamble. Para pantallas cuyos componentes son
                                        INDEPENDIENTES (fan-out real); si comparten estado mutable
                                        sin contrato posible, usar 1 nodo implement secuencial.

REGLAS DURAS que todo workflow de dev debe respetar (garantia estructural):
  1. Guard de args al inicio (require_args) + VALIDAR con args vacios antes del run real.
  2. En ctx.parallel([...]) pasar SIEMPRE lambdas (callables), NUNCA ctx.agent(...) ya evaluado
     (evita el TypeError "'str' object is not callable").
  3. Gate de auditoria standards||security con loop OBLIGATORIO antes de verify.
  4. Fan-out contract-first cuando los componentes son independientes; ensamble al final.
  5. Tras borrar codigo: la auditoria debe verificar que NO quede dead code / huerfanos.
  6. Respetar el ALCANCE declarado del requerimiento; no ampliarlo por cuenta propia.

@author kirocrew
"""

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE A COPIAR EN CADA WORKFLOW (no importar) — desde aqui hasta el final.
# ─────────────────────────────────────────────────────────────────────────────


def require_args(ctx, *names):
    """Guard de args obligatorios. Devuelve mensaje BLOCKED si falta alguno; None si estan todos."""
    missing = [n for n in names if not ctx.args.get(n)]
    if missing:
        return f"BLOCKED: faltan args ({', '.join(missing)} obligatorio(s))."
    return None


def _failed(result) -> bool:
    """Un veredicto de auditoria es fallo si no contiene exactamente 'VERDICT: PASS'."""
    return result is None or "VERDICT: PASS" not in str(result)


async def audit_gate(ctx, repo, fix_agent, audit_prompt, fix_prompt_builder=None, max_iters=3):
    """dev-standards || dev-security en paralelo sobre el diff, con loop de correccion.

    audit_prompt debe pedir 'VERDICT: PASS'/'VERDICT: FAIL' en la ULTIMA linea.
    Devuelve True si ambas pasan dentro de max_iters, False si no.
    """
    for iteration in range(1, max_iters + 1):
        ctx.phase(f"audit (standards || security) · iter {iteration}")
        standards, security = await ctx.parallel([
            lambda it=iteration: ctx.agent(audit_prompt, agent="dev-standards", cwd=repo, label=f"std#{it}"),
            lambda it=iteration: ctx.agent(audit_prompt, agent="dev-security", cwd=repo, label=f"sec#{it}"),
        ])
        ctx.log(f"[std#{iteration}] {str(standards)[:400]}")
        ctx.log(f"[sec#{iteration}] {str(security)[:400]}")
        if not _failed(standards) and not _failed(security):
            return True
        ctx.phase(f"correccion · iter {iteration}")
        if fix_prompt_builder is not None:
            fix_prompt = fix_prompt_builder(standards, security)
        else:
            fix_prompt = (
                "Corrige SOLO los hallazgos Alta/Critica de estas auditorias, sin cambiar el "
                f"comportamiento:\n\n[ESTANDARES]\n{standards}\n\n[SEGURIDAD]\n{security}"
            )
        fix = await ctx.agent(fix_prompt, agent=fix_agent, cwd=repo, label=f"fix#{iteration}")
        ctx.log(f"[fix#{iteration}] {str(fix)[:400]}")
    return False


async def contract_then_parallel(ctx, repo, agent, contract_prompt, component_specs, assemble_prompt):
    """Patron contract-first: contrato -> componentes en paralelo -> ensamble.

    component_specs: dict {label: prompt} de componentes INDEPENDIENTES (paralelo).
    Devuelve (contract_result, {label: result}, assemble_result).
    """
    ctx.phase("contract · interfaces/modelo compartidos")
    contract = await ctx.agent(contract_prompt, agent=agent, cwd=repo, label="contract")
    ctx.log(f"[contract] {str(contract)[:400]}")

    labels = list(component_specs.keys())
    ctx.phase("components-parallel · " + " || ".join(labels))
    tasks = [
        (lambda p=component_specs[label], l=label: ctx.agent(p, agent=agent, cwd=repo, label=l))
        for label in labels
    ]
    results = await ctx.parallel(tasks)
    comp_results = {}
    for label, res in zip(labels, results):
        comp_results[label] = res
        ctx.log(f"[{label}] {str(res)[:400]}")

    ctx.phase("assemble · integra los componentes")
    assemble = await ctx.agent(assemble_prompt, agent=agent, cwd=repo, label="assemble")
    ctx.log(f"[assemble] {str(assemble)[:500]}")

    return contract, comp_results, assemble
