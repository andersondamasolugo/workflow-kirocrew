---
inclusion: fileMatch
fileMatchPattern: ["**/*.go", "go.mod"]
---

# Reglas Go (idiomatic Go)

## Estilo
- `gofmt`/`goimports` obligatorio; lint con `golangci-lint` (govet, staticcheck, errcheck).
- Nombres cortos e idiomáticos: `srv`, `ctx`, `err`; exportado = `PascalCase`, no exportado = `camelCase`.
- Paquetes con nombre corto, en singular, sin `util`/`common`/`helpers`.
- Sin getters con prefijo `Get`: `user.Name()`, no `user.GetName()`.

## Errores
- Manejar TODO error: `if err != nil` inmediato; nunca `_` para descartar errores salvo justificación comentada.
- Envolver con contexto: `fmt.Errorf("opening config: %w", err)`.
- Errores centinela (`var ErrNotFound = errors.New(...)`) o tipos propios; comparar con `errors.Is`/`errors.As`.
- `panic` solo para errores de programación irrecuperables en init; nunca en flujo normal.

## Diseño
- Aceptar interfaces, retornar structs. Interfaces pequeñas (1-3 métodos) definidas por el consumidor.
- Composición sobre pseudo-herencia; embedding con moderación.
- `context.Context` como primer parámetro de toda función que cruce límites de red/tiempo; propagarlo, no almacenarlo en structs.
- Inyección de dependencias explícita por constructor (`NewServer(db, logger)`); sin frameworks mágicos ni globals.
- Configuración por variables de entorno/flags parseadas en `main`, pasada como struct.

## Concurrencia
- No lanzar goroutines sin saber cómo terminan: usar `errgroup`, `sync.WaitGroup` o canales con cierre claro.
- Channels para transferir propiedad; mutex para proteger estado compartido — elegir uno, documentarlo.
- Detectar data races en CI: `go test -race`.

## Proyecto
- Layout estándar: `cmd/<app>/main.go` fino; lógica en `internal/`; `pkg/` solo si de verdad es reutilizable externamente.
- `go.mod` con versiones mínimas necesarias; `go mod tidy` antes de cada commit.
- `main` solo cablea dependencias y arranca; nada de lógica de negocio.

## Anti-patrones prohibidos
- Variables globales mutables y `init()` con lógica compleja.
- Interfaces "por si acaso" con un solo implementador y sin consumidor que las pida.
- Ignorar `ctx.Done()` en operaciones largas.

## Testing
- Tests de tabla (`[]struct{...}`) como patrón por defecto.
- `t.Helper()` en helpers; subtests con `t.Run`.
- Interfaces pequeñas + fakes escritos a mano sobre frameworks de mocks pesados.
