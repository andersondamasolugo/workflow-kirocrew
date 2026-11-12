---
inclusion: fileMatch
fileMatchPattern: ["**/*.spec.ts", "**/*.test.ts", "jest.config*"]
---

# 🧪 Testing con Jest

## 📋 TL;DR

- ✅ Tests para toda lógica de negocio
- ✅ Arrange-Act-Assert (AAA)
- ✅ Mocks para dependencias
- ✅ Cobertura > 80% (incluyendo nuevo código)
- ✅ **OBLIGATORIO** verificar cobertura del nuevo código antes de afirmar cambios
- ❌ NO tests de UI complejos en unitarios
- ❌ NO comentarios innecesarios en tests
- ❌ NO console.* en tests
- ❌ NO afirmar cambios completos sin verificar cobertura del nuevo código

## 🎯 QUÉ TESTEAR

### Obligatorio
- Servicios (lógica de negocio)
- Pipes y directivas
- Guards e interceptors
- Utilidades y helpers
- Validadores custom

### Opcional/E2E
- Componentes UI simples
- Templates complejos

## 📝 ESTRUCTURA AAA

```typescript
describe('UserService', () => {
  let service: UserService;
  let httpMock: HttpTestingController;
  
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UserService]
    });
    
    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
  });
  
  it('should get user by id', () => {
    // Arrange
    const mockUser = { id: '1', name: 'John' };
    const userId = '1';
    
    // Act
    service.getUser(userId).subscribe(user => {
      // Assert
      expect(user).toEqual(mockUser);
      expect(user.id).toBe(userId);
    });
    
    const req = httpMock.expectOne(`${service.apiUrl}/users/${userId}`);
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);
  });
  
  afterEach(() => {
    httpMock.verify();
  });
});
```

## 🔧 MOCKS

### Servicios

```typescript
const mockUserService = {
  getUser: jest.fn().mockReturnValue(of({ id: '1', name: 'John' })),
  createUser: jest.fn().mockReturnValue(of({ id: '2' }))
};

TestBed.configureTestingModule({
  providers: [
    { provide: UserService, useValue: mockUserService }
  ]
});
```

### HTTP

```typescript
it('should handle HTTP errors', () => {
  const errorMessage = 'User not found';
  
  service.getUser('999').subscribe({
    error: (error) => {
      expect(error.status).toBe(404);
      expect(error.statusText).toBe(errorMessage);
    }
  });
  
  const req = httpMock.expectOne(url);
  req.flush(errorMessage, { status: 404, statusText: errorMessage });
});
```

## 📊 COBERTURA

| Métrica | Objetivo | Mínimo |
|---------|----------|--------|
| Statements | 90% | 80% |
| Branches | 85% | 75% |
| Functions | 90% | 80% |
| Lines | 90% | 80% |

### REGLA CRÍTICA: Cobertura del Nuevo Código

**OBLIGATORIO**: Todo código nuevo o modificado DEBE tener cobertura mínima del 80% antes de afirmar cambios completos.

**Proceso obligatorio:**
1. Realizar cambios en código
2. **EJECUTAR** `npm run test:coverage` para generar reporte
3. **VERIFICAR** cobertura específica de archivos nuevos/modificados
4. **AGREGAR** tests faltantes si la cobertura es < 80%
5. **RE-EJECUTAR** tests hasta alcanzar ≥ 80% de cobertura
6. **SOLO ENTONCES** afirmar que los cambios están completos

**Archivos a verificar:**
- Archivos nuevos creados en la sesión actual
- Archivos modificados con cambios significativos (> 10 líneas)
- Métodos nuevos agregados a archivos existentes
- Servicios, componentes y utilidades nuevos

```bash
# Generar reporte de cobertura
npm run test:coverage

# Ver reporte detallado
open coverage/index.html

# Ejecutar tests específicos de archivos modificados
npm test -- --testPathPattern="archivo-modificado"
```

**Ejemplo de verificación:**
```bash
# Después de modificar experian.service.ts
npm run test:coverage -- --testPathPattern="experian.service"

# Verificar que la cobertura sea ≥ 80%
# Si es menor, agregar tests faltantes
```

## 🎯 NOMENCLATURA

```typescript
describe('FeatureName', () => {
  describe('methodName', () => {
    it('should do something when condition', () => {
      // Test
    });
    
    it('should throw error when invalid input', () => {
      // Test
    });
    
    it('should return default when empty', () => {
      // Test
    });
  });
});
```

**Patrón:** `should [expected behavior] when [condition]`

## 🚫 RESTRICCIONES

1. **PROHIBIDO** tests sin estructura AAA
2. **PROHIBIDO** tests sin cleanup cuando sea necesario
3. **PROHIBIDO** tests dependientes entre sí
4. **PROHIBIDO** comentarios innecesarios (históricos, obvios, redundantes)
5. **PROHIBIDO** `console.*` en tests (log, error, warn, info, debug)
6. **PROHIBIDO** tests de UI complejos en unitarios (usar E2E)
7. **PROHIBIDO** hardcodear valores sin explicación en tests críticos
8. **PROHIBIDO** usar `any` sin justificación en mocks
9. **PROHIBIDO** tests sin assertions (expects)
10. **PROHIBIDO** afirmar cambios completos sin verificar cobertura del nuevo código
11. **PROHIBIDO** código nuevo con cobertura < 80% (statements, branches, functions, lines)
12. **PROHIBIDO** ignorar archivos nuevos/modificados sin tests adecuados

## ✅ VALIDACIÓN AUTOMÁTICA

Cursor debe:
1. **DETECTAR** servicios sin tests
2. **VALIDAR** estructura AAA
3. **SUGERIR** mocks para dependencias
4. **ADVERTIR** sobre cobertura baja
5. **DETECTAR** tests sin cleanup
6. **DETECTAR** comentarios innecesarios en tests
7. **DETECTAR** uso de `console.*` en archivos `.spec.ts`
8. **FORZAR** eliminación antes de afirmar cambios completos
9. **VERIFICAR OBLIGATORIAMENTE** cobertura del nuevo código antes de afirmar cambios completos
10. **EJECUTAR AUTOMÁTICAMENTE** `npm run test:coverage` para archivos nuevos/modificados
11. **ADVERTIR** si el nuevo código tiene cobertura < 80%
12. **BLOQUEAR** afirmación de cambios completos si el nuevo código no cumple con el 80% de cobertura
13. **SUGERIR** qué tests agregar para mejorar la cobertura del nuevo código
14. **VERIFICAR** que métodos nuevos tienen tests correspondientes

## 🎯 OBJETIVO

Tests mantenibles y confiables que validen la lógica de negocio sin fragilidad, garantizando que todo código nuevo tenga cobertura adecuada.

**REGLA DE ORO**: 
- AAA siempre, mocks para dependencias, > 80% cobertura
- **OBLIGATORIO** verificar cobertura del nuevo código antes de afirmar cambios
- Sin comentarios innecesarios, sin console.*
- **NUNCA** afirmar cambios completos sin verificar cobertura ≥ 80% del nuevo código
