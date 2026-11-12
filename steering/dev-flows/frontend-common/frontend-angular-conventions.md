---
inclusion: auto
name: frontend-angular-conventions
description: Angular guide when working with Angular components, signals, standalone components, inject(), OnPush, reactive forms, input()/output(), or native control flow (@if, @for).
---

# Angular Conventions — Seguros Bolívar

## Corporate UI Library Mandatory

Use `@seguros-bolivar/ui-bundle` for corporate UI components. It is a multi-brand Design System (6 brands, light/dark themes) built with Web Components (Lit) and CSS atoms. Architecture: `tokens`, `atoms`, `molecules`, `brand-overrides`, `bundle`.

```ts
// ✅ Good — import the bundle CSS via CDN or local
// <link rel="stylesheet" href="https://juancontreras-dev.github.io/seguros-bolivar-ui/dist/sb-ui-seguros-bolivar-light.min.css">

// ✅ Good — for Web Components (modal, toast, datepicker, calendar)
// <script type="module" src="https://juancontreras-dev.github.io/seguros-bolivar-ui/dist/sb-ui-components.min.js"></script>

// ❌ Bad — building UI components from scratch when they exist in the library
// ❌ Bad — using old import path
import '@seguros-bolivar/ui-lib/bundle';
```

Set `data-brand` and `data-theme` on `<html>` — without them only White Label base styles apply. Font Awesome, Bolívar font, and Roboto are bundled — never add separate CDN links for them.

## Standalone Components by Default

Use standalone components, directives, and pipes. Do not use `NgModules` for new features. Do not declare `standalone: true` explicitly — it is implicit.

```ts
// ✅ Good — implicit standalone
@Component({
  selector: 'app-policy-list',
  templateUrl: './policy-list.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PolicyListComponent {}

// ❌ Bad — NgModule or explicit standalone
@Component({ standalone: true, ... })
```

## Signals for State

Use Angular Signals for reactive state. `computed()` for derived state. Do not use `mutate` on signals — use `update` or `set`.

```ts
// ✅ Good — signals + computed
policies = signal<Policy[]>([]);
activePolicies = computed(() => this.policies().filter(p => p.isActive));

// ❌ Bad — mutable state without signals
policies: Policy[] = [];
get activePolicies() { return this.policies.filter(p => p.isActive); }
```

## input() and output() Instead of Decorators

Use `input()` and `output()` functions instead of `@Input()` and `@Output()`.

Never use `{ alias: 'name' }` in `input()`. The property name must match the binding name. If the internal name differs from the external one, rename the property directly. Aliases in inputs generate SonarCloud findings and violate official Angular guidelines (https://angular.dev/guide/components/inputs#choosing-input-names).

```ts
// ✅ Good
userId = input<string>('');
userSelected = output<string>();

// ❌ Bad
@Input() userId!: string;
@Output() userSelected = new EventEmitter<string>();

// ❌ Bad — aliased input
userIdSignal = input<string>('', { alias: 'userId' });

// ✅ Good — no alias, property name IS the binding name
userId = input<string>('');
```

## inject() Instead of Constructor Injection

Use `inject()` for dependency injection.

```ts
// ✅ Good
export class PolicyService {
  private http = inject(HttpClient);
}

// ❌ Bad
constructor(private http: HttpClient) {}
```

## Native Control Flow

Use `@if`, `@for`, `@switch` instead of `*ngIf`, `*ngFor`, `*ngSwitch`. Always include `track` in `@for`.

```html
<!-- ✅ Good -->
@if (isLoaded) {
  <section>Content</section>
}
@for (policy of policies(); track policy.id) {
  <app-policy-card [policy]="policy" />
}

<!-- ❌ Bad -->
<section *ngIf="isLoaded">Content</section>
<div *ngFor="let policy of policies">...</div>
```

## Native Class Bindings

Do not use `ngClass` or `ngStyle`. Use native `class` and `style` bindings.

```html
<!-- ✅ Good -->
<section [class.active]="isActive"></section>
<section [style.font-size.px]="fontSize"></section>

<!-- ❌ Bad -->
<section [ngClass]="{'active': isActive}"></section>
<section [ngStyle]="{'font-size': fontSize + 'px'}"></section>
```

## OnPush + Lazy Loading

Always use `ChangeDetectionStrategy.OnPush`. Lazy loading for feature routes. `NgOptimizedImage` for static images.

## Services

`providedIn: 'root'` for tree-shakable singletons. Single responsibility per service. Reactive Forms over Template-driven for complex forms.

## No any

`any` is forbidden. Use `unknown` if the type is uncertain. Prefer type inference when obvious.

```ts
// ✅ Good
let name = 'Angular';
const data: unknown = fetchData();

// ❌ Bad
let name: string = 'Angular';
const data: any = fetchData();
```
