#!/usr/bin/env python3
"""Extrae el/los test(s) fallidos de un log de CI de Gradle ya descargado.

Uso:
    gh run view <RUN_ID> --log-failed > ci-failed.log
    python find_failing_gradle_test.py ci-failed.log

Imprime cada 'Clase > metodo FAILED' (sin BUILD FAILED / Task :) con su numero
de linea en el log y las lineas de contexto siguientes (excepcion/assert),
limpiando el prefijo de timestamp ISO de GitHub Actions.

No accede a la red ni a credenciales; solo parsea un archivo de texto local.
"""
import re
import sys

TS = re.compile(r"^.*?\d{4}-\d{2}-\d{2}T[0-9:.]+Z\s")
TEST_FAILED = re.compile(r">\s+.+\sFAILED\s*$")
NOISE = re.compile(r"BUILD FAILED|Task\s+:", re.IGNORECASE)
CAUSE = re.compile(
    r"Exception|Error|Expected|Actual|WantedButNotInvoked|"
    r"AssertionError|at .+\.java:\d+",
    re.IGNORECASE,
)


def strip_ts(line: str) -> str:
    return TS.sub("", line).rstrip("\n")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: find_failing_gradle_test.py <ci-failed.log>")
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        print(f"cannot read log: {exc}")
        return 1

    hits = []
    for idx, raw in enumerate(lines):
        clean = strip_ts(raw)
        if TEST_FAILED.search(clean) and not NOISE.search(clean):
            hits.append((idx, clean))

    if not hits:
        print("No se encontro 'Clase > metodo FAILED' en el log.")
        print("Confirma que es --log-failed de un run de Gradle.")
        return 0

    print(f"== {len(hits)} test(s) fallido(s) ==")
    for idx, clean in hits:
        print(f"\nL{idx + 1}: {clean}")
        # contexto: hasta 12 lineas siguientes con pinta de causa
        shown = 0
        for follow in lines[idx + 1: idx + 40]:
            fclean = strip_ts(follow)
            if CAUSE.search(fclean):
                print(f"    {fclean.strip()}")
                shown += 1
                if shown >= 6:
                    break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
