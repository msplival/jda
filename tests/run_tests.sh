#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JDA="$ROOT/jda.py"

export PYTHONHASHSEED=0
export LC_ALL=C
export LANG=C

for input_file in "$ROOT"/tests/input/input-*.txt; do
  base="$(basename "$input_file")"
  num="${base#input-}"; num="${num%.txt}"
  exp="$ROOT/tests/output/output-$num.txt"

  [[ -f "$exp" ]] || { echo "Missing expected file: $exp" >&2; exit 1; }

  diff -u "$exp" <("$JDA" "$input_file" 2>/dev/null) || { echo "FAILED: $base" >&2; exit 1; }
done

echo "OK"
