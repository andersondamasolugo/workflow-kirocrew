# Ser pro en GitHub: flujo de ramas, ambientes y trabajo en paralelo

> Guía escrita para el equipo a partir del caso real GD929-2732 (san-andres).
> Objetivo: entender **por qué** pasan los conflictos, cómo cortar ramas limpias
> y cómo trabajar varias HU a la vez (varias sesiones/agentes Kiro Crew) sin
> romperte a ti mismo.

---

## 1. La regla de oro (si solo recuerdas una cosa, que sea esta)

> **Una rama mergea LIMPIO solo hacia la rama de la que fue cortada (o a un descendiente de ella). Hacia cualquier otra rama, el merge es "no automático" si ambas tocaron los mismos archivos.**

Caso real GD929-2732 (BE), probado con `git merge-tree`:

| Rama | Cortada de | → a master | → a develop |
|------|-----------|-----------|-------------|
| `GD929-2732-to-master` | `master` | ✅ limpio | ❌ conflicto |

No es un bug ni tu rama está mal. Es matemática de git.

### Por qué exactamente

GitHub, para mergear A en B, busca el **ancestro común** (merge-base) y compara
los dos lados. Si una misma línea cambió distinto en ambos lados desde ese
ancestro → **conflicto**.

En el BE, el archivo `ErrorCodesEnum.java`:

```
master:   ... GB000021;                 (termina ahí)
develop:  ... GB000021,
              GB000022, GB000023, GB000024   <- otra HU (siniestros) ya los metió
              GB000025..28                    <- GD929-2732
tu rama:  ... GB000021,
              GB000025..28                    <- SOLO lo tuyo (cortaste de master)
```

Tu rama y develop **difieren en la misma zona del enum** → git no sabe cuál
gana → "Can't automatically merge". Hacia master da limpio porque tu rama ES
master + tus líneas, sin nada en medio.

**`CHANGELOG.md` es el imán de conflicto #1**: todas las HU agregan líneas al
mismo bloque `## [No publicado]`. Siempre va a chocar entre ambientes que
divergieron. Es normal.

---

## 2. Por qué el FE sí pasó a develop y el BE no

Mismo procedimiento en los dos repos, resultado distinto:

- **FE**: el MFE `arl-settings` es **código nuevo** (archivos que nadie más
  tocó). Los pocos archivos compartidos (`angular.json`, `constants.ts`) no
  chocaban con develop → merge limpio.
- **BE**: tocaste **2 archivos compartidos** (`CHANGELOG.md`, `ErrorCodesEnum.java`)
  que otra HU también editó entre master y develop → conflicto.

**Moraleja**: el conflicto no depende del "repo" ni de la "suerte". Depende de
si tu HU toca archivos que otras HU también tocaron. Archivos nuevos = casi
nunca conflicto. Archivos compartidos (enums, constantes, CHANGELOG, routing) =
imanes de conflicto.

---

## 3. Tu idea de la "rama puente": cuándo sí y cuándo no

Propusiste: *"cortar desde master (código limpio) y crear una rama puente a la
que le metemos los desarrollos de develop para pasearla por todos los
ambientes."*

Aquí hay que separar dos cosas, porque una funciona y la otra pelea contra git:

### ❌ Lo que NO funciona: una sola rama que sirva para master Y para develop

Es **imposible** tener una sola rama que:
- tenga los commits "limpios desde master" (sin arrastrar las otras 208 HU), **y**
- al mismo tiempo mergee sin fricción a develop (que SÍ tiene esas 208 HU).

Porque en git **un commit incluye a sus ancestros por definición**. Si tu rama
nace de master, no conoce lo de develop; si nace de develop, arrastra las 208
HU ajenas. No existe el punto medio mágico. (Esto ya lo viviste en GD929-2727.)

### ✅ Lo que SÍ funciona: una rama por DESTINO, no una rama puente universal

El patrón pro es: **el código vive una sola vez, pero lo "presentas" a cada
ambiente con la rama que ese ambiente acepta limpio.**

```
                 ┌─ feature/GD929-XXXX  (tu trabajo diario, cortada de develop)
                 │      │
   origin/develop ◄─────┘  PR normal, merge limpio (naciste de develop)
                 │
                 │   para el pase a master:
   origin/master ◄── GD929-XXXX-to-master  (rama fresca cortada de MASTER
                        + cherry-pick de TUS commits)  → merge limpio a master
```

- **Para el día a día y develop/stage**: trabajas en `feature/GD929-XXXX`
  cortada de **develop**. PR a develop = limpio (naciste de ahí).
- **Para el pase a master**: NO reusas la misma rama. Creas una **rama fresca
  cortada de master** y le haces `cherry-pick` solo de TUS commits. Esa rama va
  limpia a master.

Son **dos ramas, mismo contenido, distinto ancestro**. Eso es exactamente lo
que hiciste bien en GD929-2732. No es "nivelar"; es "presentar el mismo cambio
en la base correcta para cada destino".

> La "rama puente" tiene sentido como **puente hacia UN destino concreto**
> (ej. `-to-master`), no como una rama única que atraviese todos los ambientes.

---

## 4. Por qué NO vamos a "nivelar ramas" (salvo de vez en cuando)

**Nivelar** = traer develop encima de tu rama (merge/rebase de develop) para
"ponerla al día". Suena ordenado, pero te rompe a ti mismo:

1. **Arrastras trabajo ajeno.** Al meter develop en tu rama, tu rama pasa a
   contener las 208 HU de otros. Tu PR ya no muestra "lo tuyo": muestra un
   diff gigante y sucio. (Lección GD929-2727: una rama terminó con 197 commits
   y 190 archivos ajenos por resolver un conflicto en el lado equivocado.)
2. **Importas inestabilidad.** Si develop tiene una HU a medias (ej. el timer de
   sesión toggled 6 veces), ahora vive en tu rama.
3. **Te peleas con conflictos que no son tuyos.** Resuelves choques entre HU
   ajenas que no entiendes.

### La alternativa (lo que sí haremos)

- **Ramas de vida corta.** Una HU = una rama = un PR, y se mergea rápido. Cuanto
  menos vive una rama, menos diverge, menos conflictos.
- **Cortar fresco del ambiente destino.** En vez de "subir develop a mi rama",
  cortas una **rama nueva del ambiente destino** y traes solo tus commits
  (cherry-pick). Siempre partes de una base actualizada → merge limpio.
- **Nivelar solo de vez en cuando y con intención.** Si una rama DEBE vivir
  mucho (un refactor grande), ahí sí niveas puntualmente — pero es la excepción,
  no la rutina.

> Regla práctica: **nunca metas develop en tu feature para "ponerla al día".
> Mejor corta una rama nueva del destino y cherry-pickea lo tuyo.**

---

## 5. Trabajar varias HU en paralelo (varias sesiones/agentes Kiro Crew)

Tu meta: varias HU al mismo tiempo, varios agentes, sin pisarte. Esto es
perfectamente posible si respetas el aislamiento. Claves:

### 5.1 Una HU = una rama = un worktree = (idealmente) un agente

- Cada HU en **su propia rama** cortada de develop actualizado.
- Usa **`git worktree`** para tener varias ramas abiertas en carpetas distintas
  SIN clonar el repo varias veces ni cambiar de rama destruyendo tu WIP:

```bash
# desde el repo principal
git worktree add ../repo-GD929-AAAA feature/GD929-AAAA   # HU A en su carpeta
git worktree add ../repo-GD929-BBBB feature/GD929-BBBB   # HU B en otra carpeta
```

Cada carpeta es un árbol de trabajo independiente. El agente A trabaja en la
suya, el agente B en la suya. **No se pisan.** (Esto es justo lo que usé para
crear las ramas `-to-master` sin tocar tu WIP sucio del FE.)

### 5.2 Evita que dos HU toquen el mismo archivo compartido a la vez

El 90% de los choques entre HU paralelas vienen de **archivos imán**:
`CHANGELOG.md`, enums de códigos de error, archivos de constantes, routing.

Estrategias:
- **Divide por dominio/carpeta.** Si HU A toca `arl-settings/` y HU B toca
  `programs/`, nunca chocan.
- **CHANGELOG al final.** Agrega tu línea de CHANGELOG lo más tarde posible (o
  acepta que ese archivo siempre se resuelve a mano al mergear — es trivial).
- **Enums/constantes compartidos**: coordina los códigos (ej. tú usas GB0000025+,
  el otro agente 0000030+) o acéptalo como conflicto esperado de 1 línea.

### 5.3 Orden de merge: primero a develop, uno a uno

- Cada HU mergea **a develop** cuando está lista (PR corto, merge rápido).
- develop es el **pote común**: ahí conviven todas. Es su trabajo.
- El pase a **master/stage** se hace con rama fresca del destino + cherry-pick,
  por HU o por corte de release (según el flujo del repo).

### 5.4 Con agentes Kiro Crew

- **Una sesión por HU** mantiene el contexto separado (no mezclas el estado de
  GD929-2732 con GD929-XXXX).
- Cada sesión trabaja en su **worktree**; el proyecto de la sesión apunta a esa
  carpeta.
- El agente registra su estado en el **ledger de sesión** para sobrevivir
  compactaciones y retomar donde quedó.

---

## 5.5 Caso de estudio real: UNA rama, DOS PR (develop y stage) sin conflicto

Un compañero (PR #1404 y #1405 en `autorizaciones-ms`) hizo algo que parece
magia: **la misma rama** `fix/ajuste-deducible-historial-autorizaciones`, con
los **mismos 7 SHA exactos**, abrió un PR a `develop` (#1404) y otro a `stage`
(#1405), y ambos mergearon limpio. Sin cherry-pick, sin dos ramas, sin resolver
conflictos.

### El secreto: de dónde cortó la rama

El padre de su primer commit es `3da814c1` = *"Merge pull request #1377 from
v2.0.0.14-to-master"* (un **merge de release**). Ese commit está en **develop Y
en stage a la vez**.

> Cortó su rama de un punto que es **ancestro común de develop y de stage**.
> Por la regla de oro, una rama mergea limpio hacia sus descendientes → si el
> punto de corte es ancestro de los DOS ambientes, la rama va limpio a los DOS.

```
          3da814c1  ← merge release (develop y stage estaban aquí a la par)
         /        \
        │          ├────────────► origin/develop  (avanzó con otras HU)
        │          └────────────► origin/stage    (avanzó con otras HU)
        │
        └─ fix/ajuste-deducible...  (7 commits)
                  ├─► PR #1404 base: develop  ✅ limpio
                  └─► PR #1405 base: stage    ✅ limpio
```

### La receta para hacerlo igual (AL INICIAR una HU)

```bash
git fetch origin
# punto donde develop y stage están a la par (último release común):
BASE=$(git merge-base origin/develop origin/stage)
git checkout -b fix/mi-hu $BASE
# ...trabajas y commiteas...
git push -u origin fix/mi-hu
# luego en GitHub: dos PR con la MISMA rama, uno base develop, otro base stage
```

### La condición para que NO choque

Que entre el punto de corte y ahora, **ni develop ni stage hayan tocado tus
mismos archivos**. Si tocas archivos imán (CHANGELOG, enums) que otra HU ya
editó en uno de los ambientes, ese PR chocará y vuelves al cherry-pick.

### Por qué a mí (GD929-2732) me chocó y a él no

| | Compañero (#1404/#1405) | GD929-2732 (mío) |
|---|---|---|
| De dónde cortó | punto ancestro de develop **y** stage (release reciente) | de **master**, 208 commits detrás de develop |
| Archivos | nadie más los tocó desde el corte | toqué CHANGELOG/enum que otra HU ya editó |

Él cortó **reciente y compartido**; yo corté de master (lejísimos). Por eso su
rama es compatible con ambos ambientes y la mía no.

### Cuándo usar cada técnica

- **HU NUEVA** → técnica del compañero: cortar del punto común develop/stage,
  abrir 2 PR con la misma rama. Es lo ideal, sin cherry-pick.
- **HU que YA está en develop** (como GD929-2732) → ya no puedes abrir 2 PR de
  una rama; el código ya avanzó a develop. Para el pase a stage cortas de
  `origin/stage` + cherry-pick de tus commits (SHA nuevos, contenido idéntico).

---

## 5.6 "Mismos commits sin crear nuevos": el matiz honesto

Querrás a veces "pasar la rama con los mismos commits, sin crear nuevos". Ojo
con esto, porque git tiene una verdad incómoda:

> Un commit está definido por su contenido **+ su commit padre (ancestro)**. Si
> cambias la base (lo pones sobre otra rama), el SHA cambia **aunque el código
> sea idéntico**. Eso es lo que hace `cherry-pick`: mismo contenido, SHA nuevo.

Entonces solo hay dos posibilidades, nunca una tercera:

1. **Mismos SHA exactos** → obligatoriamente arrastras TODO el ancestro de esos
   commits (si nacieron sobre develop, arrastras develop entero). Sirve cuando
   el destino acepta ese ancestro (ej. la técnica 5.5 del punto común).
2. **Mismo contenido, SHA nuevos** (cherry-pick sobre otra base) → NO arrastras
   ancestro ajeno, pero los SHA son nuevos. Sirve para aislar tu HU a un
   ambiente que divergió (stage/master) sin traer las otras HU.

"Mismos commits sin crear nuevos" + "sin arrastrar lo ajeno" al mismo tiempo es
**imposible** cuando los ambientes ya divergieron. Eliges: o SHA iguales con
ancestro, o contenido igual con SHA nuevos. Para un pase aislado a stage/master,
la respuesta correcta es **cherry-pick (contenido igual, SHA nuevos)** — y eso
NO genera choques, porque el contenido es el mismo que el destino espera.

---

## 6. Checklist pro antes de abrir un PR

```
[ ] ¿De qué rama corté? → esa es la única a la que mergea limpio.
[ ] ¿El PR apunta al base correcto? (rama -to-master → base master, NO develop)
[ ] ¿El diff muestra SOLO mi HU? (git diff --stat origin/<base>..HEAD)
[ ] ¿Cero archivos de otras HU? (grep de tickets ajenos en el diff)
[ ] ¿Verifiqué el merge antes? (git merge-tree --write-tree origin/<base> mi-rama)
[ ] Si hay conflicto: ¿es en archivo imán (CHANGELOG/enum)? → esperado, se
    resuelve aceptando la versión del destino + re-agregando mi línea.
```

---

## 7. Resumen de una línea por tema

- **Conflicto a develop, limpio a master**: normal; cortaste de master, mergea
  limpio solo a master.
- **Rama puente**: sí, pero una por DESTINO (`-to-master`), no una universal.
- **Nivelar ramas**: casi nunca; mejor cortar fresco del destino + cherry-pick.
- **Paralelo sin romperte**: una HU = una rama = un worktree = una sesión;
  evita archivos imán compartidos; mergea a develop seguido; pase a master con
  rama fresca.

---

## 8. El comando que lo revela todo

Antes de crear cualquier PR, para saber si va a chocar **sin crear el PR**:

```bash
git fetch origin
git merge-tree --write-tree origin/<rama-destino> origin/<mi-rama>
echo $?   # 0 = merge limpio ; 1 = habrá conflicto (y lista los archivos)
```

Esto te dice la verdad antes de que GitHub te muestre el aviso rojo.

---

## 9. El estándar OFICIAL del validador de control de cambios

> Fuente: `segurosbolivar/devops-documentacion-estandares` →
> `Validacion_Control_de_Cambios/`. Esto es lo que valida el "control de cambios"
> (lo que llamábamos DOFI). **Manda sobre la intuición**: aunque una rama sea
> técnicamente limpia, si no cumple estas reglas el control se rechaza.

### 9.1 Reglas del PR a master (TODOS los controles)

- La **rama base** del PR debe ser **master**.
- La **rama head** del PR debe ser **pre, stage, o haber sido creada a partir de
  un TAG válido**. → Una rama cortada directo de master + cherry-pick **NO
  cumple**: debe nacer de un tag (que salió de stage/pre).
- Debe existir **CODEOWNERS** válido (equipos/personas correctos) en el repo.
- Debe existir **pull_request_template.md** en el repo.
- Reviewers: se asignan por CODEOWNERS; solo cuentan aprobaciones de personas del
  team configurado. Reviewers manuales generan error en la validación.
- El **PR debe estar abierto** al momento de la ejecución.

### 9.2 Formato de TAG obligatorio

- `v#.#.#.#` (v minúscula + 4 números por punto). Opcional: `-release` o `-pre`
  (`v#.#.#.#-release`, `v#.#.#.#-pre`).
- **El nombre de la rama debe ser IGUAL al nombre del tag.**
- Si no coincide o el formato es inválido → recrear tag + rama + PR nuevo (con
  ayuda de las Gestoras de Cambios).
- (Complementa la lección previa: el tag debe ser **ligero**, no anotado.)

### 9.3 Flujo oficial para llevar cambios AISLADOS a master (nivelación)

El caso "quiero llevar SOLO mi HU a master sin arrastrar todo stage". Pasos
oficiales (de la NOTA TIP de "Validaciones Generales"):

```
1. Nivelar la rama previa (stage/pre) con respecto a master.
2. Subir al ambiente nivelado ÚNICAMENTE los cambios que van a master.
3. Validar que queden estables en stage o pre.
4. Crear un TAG v#.#.#.# + una rama con el MISMO nombre del tag.
5. Crear el PR de esa rama (base: master) y usarlo en el control de cambios.
6. Una vez el PR pase las validaciones, dejar el ambiente nivelado como estaba.
```

> La nivelación SÍ existe en el flujo oficial, pero es una maniobra **puntual y
> controlada** para el pase aislado a master — no es rutina.

### 9.4 Reglas que te muerden si no las sabes

- **NO subir cambios tras pasar las validaciones.** Una vez el control sale del
  bucle "PR CON ERROR", cualquier push a las ramas del PR hace que el control sea
  **rechazado** y haya que **gestionarlo desde cero**.
- **Fix sobre una rama de tag: NO se puede directo.** Hay que subir el fix al
  ambiente previo (stage/pre), crear un tag NUEVO, nueva rama del tag, y un PR
  nuevo que reemplaza el anterior. (Es la lección del "commit huérfano".)
- Las HU del control deben estar en estado **"Pendiente PAP"**.

### 9.5 Tipos de control y terminación de repo

| Tipo de control | Terminación repo |
|---|---|
| Microservicio | `-ms` |
| Frontend | `-frontend` |
| Microfrontend | `-mf` |
| Lambda | `-lambda` |
| Librería | `-lib` |
| Base de datos | `-db` / `-db-cloud` (requiere docuwiki + PR de registro de scripts SQL) |

El "Tipo de despliegue" del control debe coincidir con la terminación del repo.

---

## 10. Plan AJUSTADO de GD929-2732 al flujo oficial

Lo que montamos (rama cortada de master + cherry-pick) era limpio pero **NO
pasaría el validador** (la head del PR a master debe nacer de un TAG, no de
master). El plan correcto según el estándar:

```
1. GD929-2732 ya está en DEVELOP (✅ hecho).
2. Llevar la HU a STAGE: rama cortada de origin/stage + cherry-pick de los
   commits de la HU → PR base: stage. Validar estable en stage.
3. Crear el TAG sobre stage con el formato v#.#.#.# (BE: v2.0.0.21 aprox;
   FE: v1.4.0.7 aprox) — tag LIGERO.
4. Crear una rama con el MISMO nombre del tag, a partir del tag.
5. PR de esa rama con base: master → al control de cambios.
6. NO tocar las ramas del PR después de que pase validación.
```

El "aislar solo mi HU" se resuelve en el paso 2-3: al tag solo entra lo que esté
estable en stage para esta HU, siguiendo la maniobra de nivelación 9.3 cuando
stage tiene trabajo ajeno que no debe ir a master.

