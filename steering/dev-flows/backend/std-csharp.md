---
inclusion: fileMatch
fileMatchPattern: ["**/*.cs", "**/*.csproj", "**/*.sln"]
---

# Reglas C# / .NET (8+)

## Estilo
- Convenciones Microsoft: `PascalCase` para tipos, métodos y propiedades públicas; `camelCase` para locales y parámetros; `_camelCase` para campos privados; interfaces con prefijo `I`.
- `dotnet format` + analizadores Roslyn habilitados (`<AnalysisLevel>latest</AnalysisLevel>`, `TreatWarningsAsErrors` en CI).
- Nullable reference types habilitado (`<Nullable>enable</Nullable>`) en todos los proyectos.
- Una clase por archivo; namespaces file-scoped.

## Lenguaje moderno
- `record` para DTOs y value objects; `init` para propiedades inmutables.
- Pattern matching (`is`, `switch` expressions) sobre cascadas de `if`.
- LINQ para transformaciones legibles; evitar consultas LINQ de más de ~3 encadenamientos sin variables intermedias.
- `IEnumerable<T>`/`IReadOnlyList<T>` en firmas públicas; no exponer `List<T>` mutable.

## Asincronía
- `async/await` de punta a punta: nunca `.Result` ni `.Wait()` (deadlocks).
- Sufijo `Async` en métodos asíncronos; `CancellationToken` en toda API pública asíncrona.
- `ConfigureAwait(false)` en librerías.

## Errores
- Excepciones específicas de dominio; nunca `catch (Exception)` sin relanzar o loguear.
- `ArgumentNullException.ThrowIfNull` para precondiciones.
- Result pattern (o excepciones bien tipadas) consistente en toda la solución — no mezclar ambos estilos al azar.

## Patrones recomendados
- Inyección de dependencias con el contenedor nativo (`IServiceCollection`); lifetimes correctos (Singleton sin estado mutable).
- Options pattern (`IOptions<T>`) para configuración tipada; secretos fuera de `appsettings.json` (User Secrets, Key Vault).
- Arquitectura limpia: Domain sin referencias a infraestructura; MediatR o servicios de aplicación para casos de uso.
- Repositorio + Unit of Work solo si aporta valor sobre EF Core directo (DbContext ya es UoW).
- `ILogger<T>` con logging estructurado (message templates), nunca interpolación en el mensaje.

## Anti-patrones prohibidos
- Service Locator (`IServiceProvider` inyectado para resolver a mano).
- Entidades EF expuestas directamente en la API pública (usar DTOs).
- `async void` salvo event handlers.
- Estado estático mutable.

## Testing
- xUnit + FluentAssertions + NSubstitute/Moq.
- `WebApplicationFactory` para tests de integración de APIs; Testcontainers para BD real.
- Nombres: `Method_Scenario_ExpectedResult`.
