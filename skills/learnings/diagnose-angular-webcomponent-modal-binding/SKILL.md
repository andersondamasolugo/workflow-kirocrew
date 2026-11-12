---
name: auto/diagnose-angular-webcomponent-modal-binding
description: Diagnose why an Angular modal wrapping a shared web component won't open, isolating code from runtime without a browser
triggers: modal no abre, sb-ui-modal, web component binding, OnPush markForCheck, jsdom integration test, Module Federation remote, two modals stacking tick
source: auto
session_key: dashboard:chat-21-1793280258
created_at: 2026-11-03T18:31:25+00:00
---

## When to use
Use when an Angular component that wraps a shared/custom web component (e.g. a design-system `<xx-modal>`) renders but does NOT visibly open/react, and the browser is unavailable or unreliable (headless Chromium/Edge crashing under host load). The method separates three root-cause classes without guessing: (1) Angular binding/CD, (2) component contract mismatch, (3) runtime/bundle (Module Federation remote, stale dist).

## Steps
1. **Read the exact binding, don't theorize.** Open the template line for the trigger (`(click)=...`) and the modal element. Confirm the handler sets the state and the modal's visibility input is bound to it.
2. **Compare against a working sibling.** Find another usage of the SAME web component that DOES open in the same app. Diff the two: change-detection strategy (OnPush vs Default), input shape (object `[customModal]="{visible}"` vs primitive `[visible]`), presence of `OnChanges`/open logic. The working sibling reveals the real contract the team uses.
3. **Get hard data WITHOUT the browser via a jsdom integration test.** Write a throwaway spec that imports the REAL child modal component (not `CUSTOM_ELEMENTS_SCHEMA` stub), renders the parent, triggers the action, runs CD, and asserts the web-component host received its open attribute (e.g. `querySelector('xx-modal').getAttribute('open')`). Green here = Angular binding works, so the fault is runtime/bundle, not code. This is the key move: it gives browser-equivalent evidence when the browser crashes.
4. **If the test proves binding works, pivot to runtime.** Check whether the child lives in a separately-built library consumed via Module Federation; a stale `remoteEntry`/dist served by the shell makes the click no-op. Ask the user to recompile the LIBRARY (not just the host) and cold-restart the shell (hard reload does not evict an already-loaded remote).
5. **If the test and sibling diff disagree, align to the proven contract.** When the failing usage passes a primitive but every working usage passes the object input, switch to the object input the project already uses — the contract match is the fix, not a CD patch.
6. **Stop after two blind patches.** If two code fixes pass tests but you still cannot see the DOM, request ONE cheap decisive datum from the user: open DevTools Console, click, report (a) a red error, (b) whether the child element exists in the DOM, (c) whether the host element has the open attribute. These three branches map 1:1 to the three root-cause classes.
7. **Two stacked modals → defer the open by one tick.** If closing modal A and opening modal B in the same handler leaves B invisible (A's closing backdrop covers B), open B in the next tick (`setTimeout(0)`). Update the affected test to `fakeAsync`/`tick`.
8. Delete the throwaway diagnostic spec; keep only the regression test for the real fix.

## Gotchas
- jsdom treats the web component as an inert element under `CUSTOM_ELEMENTS_SCHEMA`, so it proves the Angular binding path but NOT the component's runtime behavior — that's exactly why green-in-jsdom + invisible-in-browser points to runtime/bundle.
- Headless Chromium/Edge `Target crashed` is usually host load (an active `ng serve`/watcher saturating CPU), not the browser or your flags; `--single-process` tends to make real browsers worse. Don't burn turns retrying — use the jsdom route.
- OnPush + signals propagates a changed input to a Default-CD child fine; `markForCheck` is defensible hardening but rarely the actual root cause when a working sibling uses the same strategy.
- A working Edit-modal-in-host but broken shared confirm-modal is a strong tell the fault is in the separately-built library, not the host code.
