"""Crea el cli.config.json anti-crash para playwright-cli en entornos confinados.
Uso: python make_playwright_cli_config.py <output_dir>
Escribe <output_dir>/cli.config.json con launchOptions.args=['--no-sandbox'].
No hace red, no toca credenciales, no borra nada.
"""
import json
import os
import sys


def main():
    if len(sys.argv) < 2:
        print("uso: python make_playwright_cli_config.py <output_dir>")
        return 1
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    cfg = {
        "launchOptions": {
            "args": [
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
            ]
        }
    }
    path = os.path.join(out_dir, "cli.config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("escrito:", path)
    print(json.dumps(cfg, indent=2))
    print("\nRecorda: export PWTEST_SOCKETS_DIR=/tmp/pws antes de 'playwright-cli open'")
    print("y usar headless (sin --headed) con --browser chrome --config", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
