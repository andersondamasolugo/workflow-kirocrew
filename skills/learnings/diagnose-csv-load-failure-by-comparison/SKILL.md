---
name: auto/diagnose-csv-load-failure-by-comparison
description: Diagnose why one delimited file fails to load by byte-comparing it against a working file to find field-count anomalies
triggers: CSV no carga, carga masiva falla, archivo falla vs carga bien, separador interno, delimiter field count, CRLF encoding, RFC-4180 comillas
source: auto
session_key: dashboard:chat-25-1793384836
created_at: 2026-11-03T13:25:19+00:00
---

## When to use
A delimited file (CSV/semicolon/pipe) fails to import while a similar file loads fine, and you need the root cause. Classic symptoms: wrong column count on one row, parser rejects the file, data shifts into the wrong column.

## Steps
1. Compare both files at the byte level, not just visually. On macOS `cat -A` is unavailable — use `cat -v` and `hexdump -C`.
2. Get size and line counts for both: `wc -l -c file`. A mismatch between `wc -l` and visible lines hints at odd line terminators (CR-only, missing final newline).
3. Dump the first bytes with `hexdump -C` to inspect the BOM, encoding, and line endings (`\r\n` CRLF vs `\n` LF vs `\r` CR).
4. Count delimiters per row with awk to find the anomalous row:
   `awk -F';' '{print "fila "NR": "(NF-1)" separadores, "NF" campos"}' file`
   The row whose field count differs from the rest is the culprit.
5. Inspect that row's raw content. Common root cause: a delimiter character appears INSIDE a quoted field (`"text ; more"`), so a naive split-by-delimiter parser over-counts columns while an RFC-4180-aware parser would not.
6. Also note secondary issues: missing final newline, mojibake bytes (Latin-1 vs UTF-8) — flag them but do not change them unless they affect the column count.

## Fix options to offer
- Quick unblock: produce a corrected copy replacing the in-field delimiter with a safe char (comma/dash) and adding the missing final newline; leave unrelated encoding bytes untouched to avoid altering data.
- Root fix: make the backend parser respect RFC-4180 quoting so quoted fields are not split on the inner delimiter — this prevents all future files with the same pattern from failing.

## Gotchas
- macOS `cat` has no `-A`; use `cat -v` plus `hexdump -C`. In Windows PowerShell use `Format-Hex <file>` to see the bytes and `Get-Content -Raw <file> | Select-String "`r`n"` to check CRLF.
- `wc -l` counts newline bytes, so CR-only or missing-terminator files mislead it; trust the delimiter-count-per-row check over line counts.
- Do not blame encoding/CRLF first — if BOTH files have it, it is not the differentiator. The field-count anomaly is the real signal.
- Only change the minimum needed; a corrected copy unblocks now but the parser fix is the durable root cause.
