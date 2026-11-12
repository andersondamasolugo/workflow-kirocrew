---
name: flow-frontend
description: Flujo end-to-end para desarrollo SOLO-FRONTEND (UI Angular/React). Implementa contra el design system, audita estándares+seguridad sobre el diff, verifica el build con la config real de la app (tsconfig.app.json), corre los tests afectados y hace verificación visual imagen-vs-imagen. Nativo KiroCrew — la validación corre como fases embebidas de este skill. Úsalo cuando el cambio toca solo UI.
always: false
triggers: frontend flow, run frontend flow, flow-frontend, front only, ui change flow
---

# flow-frontend — flujo E2E solo-frontend

> ## 🎫 Flujo activo — FRONTEND
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-frontend` |
> | **Tipo** | Frontend-only (UI Angular/React) |
> | **Agente** | `dev-front-tienda` (`td-*`/PrimeNG) o `dev-front-bolivar-ui` (`sb-ui-*`) |
> | **Fases** | Understand → Implement → **Visual (gate, primero)** → Standards‖Security → Build/Test → Deliver |
> | **Orquestación** | 1 agente; `spawn_run` solo para ≥2 specs frontend independientes |
> | **NO hace** | Backend/API, migraciones de datos |
> | **Cierre** | Deliver gate con evidencia real por fase |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Flujo nativo KiroCrew. Lo ejecutas en esta sesión; la validación corre como fases embebidas
de este skill (no requiere eventos de `.kiro/hooks` del IDE).

## Orquestación de agentes (spawn_run nativo)
Este es un flujo de UN agente frontend — la implementación + auditoría + build + visual son
fases secuenciales dependientes, NO fan-out. Solo delega vía `spawn_run` cuando haya trabajo
**genuinamente paralelo e independiente**, con `cwd` = raíz del proyecto (permitida en
`subagent_cwd_allowed_roots`):
- **≥2 specs frontend rotos e independientes** → un batch, un task por spec.
- Una investigación amplia/ruidosa que convenga aislar del contexto → 1 sub-agente.
NO paralelices las fases del propio flujo (dependientes). Si un spawn se rechaza por memoria,
corre en la sesión principal.

## Garantías del workflow (Carril B) — nativas, no dependen de la memoria del agente

Cuando este flujo corre por el **Carril B** (`workflow_run`), estas reglas son **estructurales**:
se codifican en el propio script del workflow copiando el bloque de
`~/.kiro/crew/dev-flows/workflows/_scaffold.py` (⚠️ ese archivo NO se importa —
`from ... import` está prohibido en el sandbox del motor; sus helpers se **copian inline**).

Reglas duras (todo workflow de dev las cumple):

1. **Guard de args + validación con args vacíos.** El workflow arranca con `require_args(ctx, "repo", ...)`
   → `BLOCKED: faltan args`. ANTES del run real, ejecuta el script con `args` vacíos: debe terminar
   `finished` con ese `BLOCKED` y `error: null`. Es la verificación autoritativa de que el motor
   acepta el grafo (atrapa el bug del autor automático).
2. **`ctx.parallel([...])` SIEMPRE con lambdas**, nunca `ctx.agent(...)` ya evaluado
   (el resultado evaluado provoca `TypeError: 'str' object is not callable`).
3. **Gate de auditoría `dev-standards ‖ dev-security` en paralelo con loop OBLIGATORIO** antes de
   build/verify (`audit_gate(...)`). Critical/High bloquean y reinician la corrección (hasta 3 iter).
4. **Fan-out contract-first cuando los componentes son INDEPENDIENTES** (`contract_then_parallel(...)`):
   un nodo *contrato* fija interfaces/modelo compartidos → los componentes se construyen **en paralelo**
   (un agente cada uno) → un nodo *ensamble* integra. Esto **corrige** la regla de "1 agente": el flujo
   es 1-agente solo cuando las fases son dependientes o los componentes comparten estado mutable sin
   contrato posible; una pantalla con piezas independientes (p. ej. modal ‖ card) SÍ se paraleliza.
5. **Tras borrar código, la auditoría verifica que NO queda dead code / huérfanos** (imports, métodos,
   specs, directorios sin uso).
6. **Respetar el ALCANCE declarado** del requerimiento; no ampliarlo por cuenta propia.

> El Carril A (secuencial, en tu turno) cumple las mismas reglas por disciplina; el Carril B las
> cumple por construcción. Ver `~/.kiro/crew/dev-flows/workflows/README.md` y `_scaffold.py`.

## Fases

> **Orden del gate (ahorro de tokens):** tras Implement, la **verificación visual corre PRIMERO**
> y es bloqueante. Si el render no coincide con el Figma, se vuelve a Implement SIN gastar en
> estándares/seguridad/build/tests (que rechazarían igual el resultado). Solo con `VISUAL PASS`
> se corre el resto del gate. Si se agota el límite de reintentos sin `VISUAL PASS`, el flujo
> FINALIZA (escala a decisión humana) — no se entrega.

1. **Understand** — lee `projects/{proyecto}/.kiro/steering/*.md` + powers corporativos +
   código existente. Identifica el design system (`td-*`/PrimeNG o `@seguros-bolivar/tienda-seguros-ui-kit`; o `sb-ui-*`).
2. **Implement** — convenciones Angular 17+: standalone, signals, `input()`/`output()`
   sin alias, `inject()`, `OnPush`, `@if`/`@for` nativos, sin `any`, sin `ngClass`/`ngStyle`,
   sin `::ng-deep`. Design system al 100% — si Figma no tiene la variante, PREGUNTA.
   (Audita cada archivo al escribirlo — fase embebida, no un hook del IDE.)
3. **Build** — verifica con la config REAL: `npx ng build --configuration=development`
   (o `tsc -p tsconfig.app.json`). NO solo el type-check de specs. Corrige hasta que quede limpio.
4. **Test** — Jest sobre los specs afectados (dirigido, no la suite completa en un host ajustado).
   Cobertura ≥80% en la lógica tocada.
5. **Visual verify (nativo KiroCrew) — imagen-vs-imagen, OBLIGATORIA y BLOQUEANTE.**
   El desarrollo NO está hecho hasta confrontar el render contra el Figma. No se declara PASS
   "a ojo": hay que producir DOS imágenes y compararlas. Pasos en orden:
   1. **Extrae la referencia Figma primero.** Con la herramienta Figma (`get_screenshot` /
      `get_design_context`) captura el nodo de referencia (p. ej. `4242-14110` desktop,
      `4061-22024` móvil) y guárdalo como **baseline** en `$KIROCREW_SCRATCH`. Sin baseline
      extraído no hay comparación posible.
   2. **Deja el front-view en la pantalla con el AUTOMATIZADOR DE NAVEGACIÓN, no con goto directo.**
      Una pantalla del stepper cae al home si se salta a su URL, así que la navegación se delega
      al automatizador del repo. Levanta el dev server en loopback
      (`npx ng serve --configuration=development`) usando el host **`localhost`** (NO `127.0.0.1`:
      el ng serve de este host bindea IPv6/localhost y rechaza 127.0.0.1), emite el marcador
      `<!-- kirocrew:preview url="http://localhost:PORT" -->`, y corre:
      `node e2e/visual-nav/run-visual-nav.mjs --screen <SCREEN_KEY> --base-url http://localhost:PORT --out $KIROCREW_SCRATCH/visual-nav/out`.
      El runner navega como usuario real (respeta guards y stepper), deja el front en la ruta y
      escribe `render_<KEY>_desktop.png` / `render_<KEY>_mobile.png` en `--out` — usa ESAS como render.
      **Contrato autosuficiente** (mapa `e2e/visual-nav/screens.map.json`):
      - Exit 3 `AUTOMATIZACION FALTANTE` → la pantalla no tiene `navSteps`. **CREA el flujo**:
        descubre navegando desde el home la secuencia (goto de la ruta de entrada del stepper,
        llenar el onboarding con datos de prueba válidos, marcar consentimientos por su `label[for]`,
        click Continuar, avanzar hasta que monte el componente objetivo), añádela como `navSteps`
        de la pantalla en el mapa y reejecuta.
      - `[navSteps paso #N] FALLO … URL alcanzada: …` → un paso ya no coincide; corrígelo en el
        mapa con esa evidencia y reintenta.
      - Solo cuando imprime `CAPTURE desktop/mobile: <ruta>` con la URL final en la ruta objetivo,
        el front-view quedó listo. Si no lo logras, el veredicto es `VISUAL BLOCKED` (nunca PASS
        sobre una captura del home). Fallback de screenshot puntual: **`browser` MCP tool** /
        `playwright-cli`; para diff-vs-baseline o a11y, la skill **`web-verify`**.
   3. **Compara imagen-vs-imagen** baseline Figma vs render: layout, tipografía, colores/tokens,
      spacing e iconografía. Umbral de coincidencia **85%**. Si hay layout móvil en el diseño,
      repite con el nodo móvil en viewport angosto. Para diff-vs-baseline o a11y usa la skill
      **`web-verify`**.
   4. **Embebe AMBAS imágenes** en el mensaje (`![desc](/ruta/abs.png)` de baseline y de render)
      y enumera las diferencias.
   5. **Veredicto explícito** — última línea, exactamente una de:
      - `VERDICT: VISUAL PASS` — coincide, sin desviaciones dignas de nota.
      - `VERDICT: VISUAL PASS_WITH_NOTES` — coincide **≥85% (APRUEBA)** pero quedan desviaciones
        MENORES que se informan para que el humano decida si vale pulirlas (p.ej. 20 vs 24px, un
        breakpoint en el borde exacto). NO bloquea: 85% es el criterio de aprobación, no el piso
        para fallar.
      - `VERDICT: VISUAL FAIL` — por debajo del 85% o con desviaciones que ROMPEN el diseño;
        enuméralas y vuelve a Implement a corregirlas.
      - `VERDICT: VISUAL BLOCKED` — no se pudo levantar el render/backend; di qué falta.
        BLOCKED **detiene la entrega**, no es un PASS. Screenshot <2000px por lado. El remedio de
        un clic para el backend del panel es Settings → Browser (el `browser` tool ya es nativo).
   > En el Carril B (`master_dispatch`) este nodo corre como **gate bloqueante**: `VISUAL FAIL`
   > reinicia el loop de corrección, `VISUAL PASS`/`PASS_WITH_NOTES` deja pasar (las notas se
   > arrastran al resumen final para el humano) y `VISUAL BLOCKED` detiene el frontend. En Carril
   > A lo corres tú en esta sesión con el mismo veredicto.
6. **Deliver** — `git status`, resumen. NO commit sin autorización. Si el usuario
   autoriza un PR → entrega a `prepare-pr`.

## Notas
- **Visibilidad (no caja negra).** En **Carril A** (este skill ejecutado en la sesión principal)
  cada fase es visible en el propio chat: muestra el prompt/comando y su salida real, sin
  ocultarlos tras un resumen. En **Carril B** (`master_dispatch`) el workflow ya registra por
  cada nodo (PO, implement, visual, standards, security, build/tests) el prompt enviado y la
  respuesta del agente vía `ctx.log`, para que el panel Workflows no sea caja negra.
- Los sub-agentes SÍ pueden leer el FS del proyecto si `cwd` está bajo un root permitido
  (`subagent_cwd_allowed_roots`). Si un spawn se rechaza por memoria, corre la auditoría en la sesión principal.
- La validación (build + tests) es una fase obligatoria de este skill (fase 3-4), no un
  hook del IDE — corre en el mismo turno en KiroCrew.

## Deliver gate — evidencia por fase (obligatorio, nativo)

Antes de declarar este flujo TERMINADO, vuelve a leer este mismo `SKILL.md` y, por CADA
fase que define arriba, emite una fila en esta tabla:

| Fase | Herramienta/comando ejecutado | Resultado (evidencia real) |
|------|-------------------------------|----------------------------|

Reglas del gate:
- Una fase SOLO cuenta como hecha si pegas la **evidencia real** de haberla ejecutado
  (salida del comando, no una afirmación). Sin evidencia = NO hecha.
- La fila **Visual** es especial: su evidencia son las **DOS imágenes embebidas** (baseline
  Figma + render) MÁS el veredicto explícito (`VERDICT: VISUAL PASS`, `PASS_WITH_NOTES`, `FAIL`
  o `BLOCKED`). `PASS_WITH_NOTES` (≥85%, APRUEBA con desviaciones menores) es un cierre válido:
  lista esas notas en la fila para que el humano decida si pulirlas — 85% aprueba, no falla.
  Una fila Visual sin ambas imágenes NO cuenta como hecha, aunque diga "coincide". Es
  exactamente el hueco que provocó que un desarrollo se declarara terminado sin confrontarse
  con el Figma.
- Prohibido sustituir un paso por un atajo más barato (p. ej. type-check de specs o
  `sass.compile` en lugar del build real que la fase de Build exige; o "se ve bien" en lugar
  de la comparación imagen-vs-imagen que la fase Visual exige). El atajo NO es evidencia.
- Si una fase no se puede ejecutar en este host/entorno, decláracla **BLOCKED** con el motivo
  concreto y qué falta para desbloquearla — nunca la marques PASS "a ojo".
- No puedes decir "listo"/"flujo cumplido" con filas sin evidencia ni BLOCKED justificado.
- Este gate es la fase final y se aplica a sí mismo: es parte del flujo, no un extra opcional.
