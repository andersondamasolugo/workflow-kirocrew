---
name: auto/expose-jpa-audit-fields-in-mapstruct-dto
description: Expose JPA auditing author/date fields in a read-only output DTO via MapStruct without allowing client mass-assignment
triggers: expose audit fields, creationUser modificationUser, JPA Auditing DTO, MapStruct read-only field, @InheritInverseConfiguration, Auditable MappedSuperclass, mass assignment prevention
source: auto
session_key: dashboard:chat-15-1793029684
created_at: 2026-10-26T17:12:05+00:00
---

## When to use
A JPA entity already persists audit fields (via `@CreatedBy`/`@LastModifiedBy` on an `Auditable` `@MappedSuperclass` driven by an `AuditorAware`), the data is in the DB, but the REST GET response does not include them because the output DTO omits them. Goal: surface `creationUser/creationDate/modificationUser/modificationDate` in the API response WITHOUT letting a client forge the author on POST/PUT.

First confirm the audit chain actually works before touching anything: entity `extends Auditable`; write path uses `repository.save()` (NOT `@Modifying @Query`, which bypasses the `AuditingEntityListener`); `AuditorAware` reads a populated user context. If any of those is broken, fix persistence first — exposing an empty field is pointless.

## Steps
1. Read the entity, its `Auditable` superclass, the `AuditorAware` impl, the DTO, and the MapStruct mapper. Confirm getters on `Auditable` are public (`@Getter`) and setters are restricted (`@Setter(AccessLevel.PROTECTED)`) — this detail drives steps 3 and 5.
2. Add the 4 fields to the OUTPUT DTO, marked read-only for serialization: `@JsonProperty(access = JsonProperty.Access.READ_ONLY)` (Jackson) + `@Schema(accessMode = READ_ONLY)` so Swagger shows them as readOnly.
3. In the mapper, make the two directions explicit and asymmetric:
   - `entityToDto`: must COPY the audit fields. If it was using `@InheritInverseConfiguration`, REMOVE it — inversion turns a write-side `ignore(target=X)` into a read-side `ignore(source=X)`, silently dropping the fields you want to expose. Let MapStruct map by name (names match between `Auditable` and DTO).
   - `dtoToEntity`: add explicit `@Mapping(target="creationUser", ignore=true)` for all 4, to deterministically block mass-assignment regardless of setter visibility.
   - Any list mapper (`listEntityToListDto`) that depended on the inverse config must also drop it; MapStruct resolves the list via the singular `entityToDto` by type.
4. Update CHANGELOG (`[No publicado] → Agregado`) in the same change if the repo mandates it.
5. Add/extend a mapper unit test asserting (a) `entityToDto` exposes the 4 fields and (b) `dtoToEntity` ignores them. Because the inherited setters are PROTECTED and unreachable from the test package, seed the entity's audit fields with `org.springframework.test.util.ReflectionTestUtils.setField(...)` instead of raising setter visibility on the shared superclass. Get the mapper via `Mappers.getMapper(XMapper.class)` for a pure unit test even if `componentModel="spring"`.
6. Audit the diff for standards + security by reading: the security win is explicit read-only + ignore (no author forgery); note the audit user is a system login, not regulated PII.
7. Build/test: run `gradlew test jacocoTestReport --tests "*XMapperTest"`. If the host is memory-TIGHT, declare build/test BLOCKED and defer to CI/the user's machine rather than risking an OOM.
8. Hand off to consumers: list affected GET endpoints, the new JSON fields with types, and the rules (read-only, last-writer-not-history, may be null for old rows, LocalDateTime without zone).

## Gotchas
- `@InheritInverseConfiguration` + an `ignore` is the classic trap: it inverts source/target, so protecting the write side silently breaks the read side. Separate the two methods.
- `@Setter(AccessLevel.PROTECTED)` on the superclass means neither MapStruct (from another package) nor a test can write those fields — which is exactly what prevents mass-assignment, but also forces ReflectionTestUtils in the test.
- `updatable=false` on create columns and the read-only JSON annotation are complementary, not redundant: one guards DB write, the other guards deserialization.
- Audit fields may be null for rows created before auditing was enabled — consumers must handle null.
- `modificationUser` is last-writer-wins, not a history log. If the requirement needs who-activated-vs-who-reactivated, that is a separate audit/bitácora table, a much larger change — flag it, don't silently under-deliver.
