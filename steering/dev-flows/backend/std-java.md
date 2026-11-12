---
inclusion: fileMatch
fileMatchPattern: ["**/*.java", "pom.xml", "build.gradle", "build.gradle.kts"]
---

# Reglas Java (17+ / prácticas profesionales)

## Estilo
- Google Java Style o el formatter del proyecto; verificar con Checkstyle/Spotless en CI.
- Nombres: `camelCase` métodos/variables, `PascalCase` clases, `UPPER_SNAKE` constantes, paquetes en minúscula.
- Clases pequeñas y finales por defecto; visibilidad mínima necesaria (package-private antes que public).

## Lenguaje moderno
- `record` para DTOs y value objects inmutables.
- `Optional<T>` como retorno para ausencia de valor; NUNCA como parámetro ni campo.
- `var` solo cuando el tipo es evidente en la misma línea.
- Streams para transformaciones simples; bucle clásico si el stream se vuelve ilegible.
- `switch` con expresiones y pattern matching donde aplique.

## Errores
- Excepciones no chequeadas para errores de programación; chequeadas solo si el llamador puede recuperarse.
- Excepciones de dominio propias con jerarquía (`OrderException` → `OrderNotFoundException`).
- Nunca `catch (Exception e) {}` vacío; loguear o relanzar envolviendo (`throw new X(..., e)` para conservar causa).
- try-with-resources para todo `AutoCloseable`.

## Patrones recomendados
- Inyección de dependencias por constructor (Spring: sin `@Autowired` en campos).
- Arquitectura en capas: controller → service → repository; el dominio no depende del framework.
- Builder para objetos con muchos parámetros opcionales; Factory para creación polimórfica.
- Strategy sobre cadenas de `if/else` por tipo; evitar `instanceof` en lógica de negocio.
- Inmutabilidad: colecciones con `List.copyOf`, campos `final`.

## Anti-patrones prohibidos
- Retornar `null` en colecciones (retornar vacías).
- Lógica de negocio en controladores o entidades JPA anémicas con setters públicos por todo.
- Estado mutable compartido sin sincronización; preferir estructuras inmutables o `java.util.concurrent`.
- `System.out.println` — usar SLF4J.

## Build y dependencias
- Maven/Gradle con versiones centralizadas (BOM / version catalog).
- Sin dependencias duplicadas o con alcance incorrecto; analizar con `dependency:analyze`.

## Testing
- JUnit 5 + AssertJ (`assertThat`) + Mockito.
- Tests de slice de Spring (`@WebMvcTest`, `@DataJpaTest`) sobre `@SpringBootTest` completo cuando sea posible.
- Testcontainers para integración con base de datos real.
