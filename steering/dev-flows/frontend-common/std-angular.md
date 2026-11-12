---
inclusion: fileMatch
fileMatchPattern: ["angular.json", "**/*.component.ts", "**/*.service.ts", "**/*.directive.ts", "**/*.pipe.ts", "**/*.component.html"]
---

# Reglas Angular (17+)

Aplican cuando existe `angular.json`. Se suman a las reglas de `javascript-typescript.md`.

## Arquitectura moderna
- Componentes standalone por defecto; NgModules solo en código legado.
- Signals para estado local y derivado (`signal`, `computed`); RxJS para flujos de eventos y datos asíncronos — no convertir todo a observables por costumbre.
- Change detection `OnPush` en todo componente nuevo (o zoneless donde el proyecto lo adopte).
- Control flow nativo (`@if`, `@for` con `track`) en lugar de `*ngIf`/`*ngFor` en código nuevo.
- Lazy loading por ruta (`loadComponent`/`loadChildren`) desde el inicio.

## Componentes
- Convención de archivos Angular: `feature-list.component.ts|html|scss` juntos.
- `input()`/`output()` funcionales tipados; sin lógica de negocio en componentes: delegar a servicios.
- **Input bindings SIN alias**: nunca usar `{ alias: 'nombre' }` en `input()`. El nombre de la propiedad debe coincidir con el nombre del binding. Si el nombre interno difiere del externo, renombrar la propiedad directamente. Alias en inputs genera hallazgos en SonarCloud y viola las guías oficiales de Angular (https://angular.dev/guide/components/inputs#choosing-input-names).
- Componentes de presentación (reciben inputs, emiten outputs) separados de contenedores (inyectan servicios).
- Plantillas simples: sin llamadas a funciones costosas en el template (usar `computed`/pipes puros).

## Servicios e inyección
- `inject()` funcional sobre inyección por constructor en código nuevo.
- `providedIn: 'root'` para singletons; providers a nivel de ruta para estado por feature.
- Acceso HTTP solo en servicios; componentes nunca llaman a `HttpClient` directo.
- Interceptores para auth, errores y trazas — una sola vez, no por servicio.

## RxJS con disciplina
- Suscripciones gestionadas: pipe `async` en template, `takeUntilDestroyed()` o `toSignal()` — nunca `subscribe` sin cierre.
- Encadenar con operadores (`switchMap` para cancelar peticiones obsoletas, `exhaustMap` para evitar dobles submits).
- No anidar `subscribe` dentro de `subscribe`.

## Formularios
- Reactive Forms tipados (`FormGroup<...>`) para todo formulario no trivial; template-driven solo para casos triviales.
- Validadores reutilizables y mensajes de error centralizados.

## Anti-patrones prohibidos
- Lógica en constructores de componentes (usar `ngOnInit`/inicializadores).
- Manipular el DOM directo (`document.querySelector`) — usar Renderer2 o bindings.
- `any` en servicios HTTP: tipar las respuestas de la API.
- Estado compartido en servicios mutables sin señal/observable — cambios invisibles para la vista.

## Testing
- TestBed con componentes standalone; harnesses de Angular Material cuando aplique.
- Servicios: test unitario puro con dependencias fake; HTTP con `HttpTestingController`.
