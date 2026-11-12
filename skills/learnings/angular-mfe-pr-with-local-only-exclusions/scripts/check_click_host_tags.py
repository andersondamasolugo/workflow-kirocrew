"""Reporta, para cada atributo (click) en archivos .html, sobre qué etiqueta HTML
de apertura está colgado, para auditar la regla Sonar S6827 (los (click) deben ir
en elementos interactivos como <button> o <a>, no en div/span/label).

Uso: python check_click_host_tags.py <dir_raiz>
Solo lee archivos; no modifica nada, no accede a red.
"""
import os
import re
import sys

OPEN_TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)")
CLICK = re.compile(r"\(click\)")
INTERACTIVE = {"button", "a"}


def audit_file(path):
    findings = []
    last_open = None
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for lineno, line in enumerate(fh, 1):
                m = OPEN_TAG.search(line)
                if m:
                    last_open = m.group(1).lower()
                if CLICK.search(line):
                    tag = last_open or "?"
                    ok = tag in INTERACTIVE
                    findings.append((lineno, tag, ok))
    except OSError as exc:
        print(f"  (no se pudo leer {path}: {exc})")
    return findings


def main():
    if len(sys.argv) < 2:
        print("uso: python check_click_host_tags.py <dir_raiz>")
        return 1
    root = sys.argv[1]
    total = 0
    violations = 0
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if not name.endswith(".html"):
                continue
            full = os.path.join(dirpath, name)
            for lineno, tag, ok in audit_file(full):
                total += 1
                mark = "OK" if ok else "VIOLATION"
                if not ok:
                    violations += 1
                print(f"{mark}  {full}:{lineno}  <{tag}>")
    print(f"\n(click) totales: {total}  violaciones S6827: {violations}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
