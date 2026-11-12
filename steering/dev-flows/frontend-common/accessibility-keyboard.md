---
inclusion: fileMatch
fileMatchPattern: ["**/*.component.html", "**/*.component.ts", "**/*modal*", "**/*dialog*"]
---

# ♿ Accesibilidad - Eventos de Teclado

## 📋 TL;DR

- ✅ Usar `AccessibilityService` centralizado para eventos de teclado
- ✅ Todos los elementos interactivos DEBEN tener `(keydown)`, `(keypress)`, `(keyup)`
- ✅ Solo ejecutar callback con teclas `Enter` o `Space`
- ❌ NO crear métodos duplicados de manejo de eventos
- ❌ NO elementos interactivos sin eventos de teclado

## 🎯 REGLAS PRINCIPALES

### REGLA 1: USO OBLIGATORIO DE ACCESSIBILITY SERVICE

**OBLIGATORIO**: Usar únicamente `AccessibilityService` para manejar eventos de teclado en elementos interactivos.

- ✅ SÍ usar `AccessibilityService.handleKeyEvent()`
- ❌ NO crear métodos duplicados de manejo de eventos
- ❌ NO implementar lógica de teclado directamente en componentes

### REGLA 2: TRES EVENTOS DE TECLADO OBLIGATORIOS

**TODOS** los elementos interactivos (`<p-button>`, `<div>` clickeables, iconos con `role="button"`, etc.) DEBEN tener los **TRES eventos**:
- `(keydown)` - Evento cuando se presiona la tecla
- `(keypress)` - Evento cuando se mantiene presionada
- `(keyup)` - Evento cuando se suelta la tecla

### REGLA 3: SOLO ENTER Y SPACE

**SOLO** las teclas `Enter` y `Space` deben ejecutar acciones:
- ✅ `Enter` - Ejecuta callback
- ✅ `Space` - Ejecuta callback
- ❌ Otras teclas - No ejecutan callback

## 📊 PATRÓN ESTÁNDAR

### Servicio Centralizado

```typescript
import { AccessibilityService } from '../../shared/services/accessibility.service';

@Component({...})
export class MyComponent {
  private readonly accessibilityService = inject(AccessibilityService);

  /**
   * Maneja eventos de teclado para accesibilidad
   * 
   * @param event - Evento de teclado
   */
  handleContinueKeyEvent(event: KeyboardEvent): void {
    this.accessibilityService.handleKeyEvent(event, () => this.onContinue());
  }
}
```

### Botón con Eventos de Teclado

```html
<p-button 
  label="Continuar"
  (click)="onContinue()"
  (keydown)="handleContinueKeyEvent($event)"
  (keypress)="handleContinueKeyEvent($event)"
  (keyup)="handleContinueKeyEvent($event)"
  class="td-button td-button__primary">
</p-button>
```

### Div Clickeable con Eventos de Teclado

```html
<div 
  (click)="onItemClick(item, index)"
  (keydown)="handleItemKeyEvent($event, item, index)"
  (keypress)="handleItemKeyEvent($event, item, index)"
  (keyup)="handleItemKeyEvent($event, item, index)">
  Contenido clickeable
</div>
```

**TypeScript con parámetros:**
```typescript
handleItemKeyEvent(event: KeyboardEvent, item: ItemData, index: number): void {
  this.accessibilityService.handleKeyEvent(event, () => this.onItemClick(item, index));
}
```

## 🔧 EJEMPLOS

### Botón Simple

```typescript
// Componente
export class AuthorizationsComponent {
  private readonly accessibilityService = inject(AccessibilityService);

  handleContinueKeyEvent(event: KeyboardEvent): void {
    this.accessibilityService.handleKeyEvent(event, () => this.onContinue());
  }
}
```

```html
<!-- Template -->
<p-button 
  label="Continuar"
  (click)="onContinue()"
  (keydown)="handleContinueKeyEvent($event)"
  (keypress)="handleContinueKeyEvent($event)"
  (keyup)="handleContinueKeyEvent($event)">
</p-button>
```

### Elemento con Parámetros

```typescript
// Componente
export class PolicyHoldersComponent {
  private readonly accessibilityService = inject(AccessibilityService);

  handleInsuredKeyEvent(event: KeyboardEvent, insured: InsuredPersonData, index: number): void {
    this.accessibilityService.handleKeyEvent(event, () => this.onInsuredClicked(insured, index));
  }
}
```

```html
<!-- Template -->
<div 
  (click)="onInsuredClicked(insured, i)"
  (keydown)="handleInsuredKeyEvent($event, insured, i)"
  (keypress)="handleInsuredKeyEvent($event, insured, i)"
  (keyup)="handleInsuredKeyEvent($event, insured, i)">
  Contenido
</div>
```

## 📋 REFERENCIA RÁPIDA

| Elemento | Eventos Requeridos | Servicio | Método Wrapper |
|----------|-------------------|----------|----------------|
| `<p-button>` | `keydown`, `keypress`, `keyup` | `AccessibilityService` | `handle*KeyEvent()` |
| `<div>` clickeable | `keydown`, `keypress`, `keyup` | `AccessibilityService` | `handle*KeyEvent()` |
| Iconos interactivos (`<i>`, `<em>` con `role="button"`) | `keydown`, `keypress`, `keyup` | `AccessibilityService` | `handle*KeyEvent()` |

## 🚫 RESTRICCIONES

1. **PROHIBIDO** elementos interactivos sin los tres eventos de teclado (`keydown`, `keypress`, `keyup`)
2. **PROHIBIDO** crear métodos duplicados de manejo de eventos de teclado
3. **PROHIBIDO** implementar lógica de teclado directamente en componentes
4. **PROHIBIDO** usar otras teclas además de `Enter` y `Space` para acciones
5. **PROHIBIDO** elementos interactivos sin usar `AccessibilityService`
6. **PROHIBIDO** métodos de manejo de eventos sin llamar a `AccessibilityService`

## ✅ VALIDACIÓN AUTOMÁTICA

Cursor debe:
1. **DETECTAR** elementos interactivos sin los tres eventos de teclado (`keydown`, `keypress`, `keyup`)
2. **DETECTAR** métodos duplicados de manejo de eventos de teclado
3. **SUGERIR** uso de `AccessibilityService` cuando se detecte lógica duplicada
4. **VALIDAR** que todos los métodos wrapper llamen a `AccessibilityService`
5. **ADVERTIR** cuando se use lógica de teclado directamente en componentes
6. **VERIFICAR** que los tres eventos (`keydown`, `keypress`, `keyup`) estén presentes en todos los elementos interactivos

## 📝 IMPORTS NECESARIOS

```typescript
import { AccessibilityService } from '../../shared/services/accessibility.service';
import { inject } from '@angular/core';
```

## 🎯 OBJETIVO

Garantizar accesibilidad completa mediante eventos de teclado centralizados y consistentes, siguiendo las mejores prácticas WCAG 2.1.

**REGLA DE ORO**: 
- **SIEMPRE** usar `AccessibilityService` para eventos de teclado
- **SIEMPRE** incluir los tres eventos (`keydown`, `keypress`, `keyup`) en todos los elementos interactivos
- **SOLO** `Enter` y `Space` ejecutan acciones
- **NUNCA** duplicar lógica de manejo de eventos
