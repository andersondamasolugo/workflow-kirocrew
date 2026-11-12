#!/usr/bin/env python3
"""Print a secret from the environment or the OS secret store (cross-platform).

Lookup order:
  1. Environment variable (works on Windows, macOS and Linux).
  2. macOS Keychain (`security find-generic-password -s <service>`).
  3. Linux Secret Service (`secret-tool lookup service <service>`).

Usage:
    python3 read_secret.py <service-name> <ENV_VAR_NAME>

Example:
    python3 read_secret.py sonar-local-token SONAR_TOKEN

The secret is written to stdout only; pipe it, never paste it in a chat or log.
Exit code 1 means the secret was not found.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys


def from_environment(env_var: str) -> str:
    """Return the environment variable value, trimmed, or ''."""
    return os.environ.get(env_var, "").strip()


def from_command(cmd: list[str]) -> str:
    """Run a lookup command and return its trimmed stdout, or '' on any failure."""
    if not shutil.which(cmd[0]):
        return ""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def read_secret(service: str, env_var: str) -> str:
    """Resolve a secret from the environment first, then the OS secret store."""
    value = from_environment(env_var)
    if value:
        return value
    if sys.platform == "darwin":
        return from_command(["security", "find-generic-password", "-s", service, "-w"])
    if sys.platform.startswith("linux"):
        return from_command(["secret-tool", "lookup", "service", service])
    return ""


def main() -> int:
    """Print the secret or explain how to provide it."""
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    service, env_var = sys.argv[1], sys.argv[2]
    value = read_secret(service, env_var)
    if not value:
        print(f"Secret not found. Set the environment variable {env_var} (Windows: user variable) "
              f"or store it in the OS secret store under '{service}'.", file=sys.stderr)
        return 1
    print(value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
