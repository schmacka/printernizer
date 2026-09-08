#!/bin/sh
# S8 probe: record what PrusaSlicer hands a post-processing script.
# Always exits 0 so a failure here never breaks the user's export.
OUT="$HOME/printernizer-spike-postprocess.txt"
{
  echo "=== invoked $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo "ARGC=$#"
  i=1
  for a in "$@"; do echo "ARGV$i=$a"; i=$((i+1)); done
  echo "PWD=$(pwd)"
  echo "--- environment (SLIC3R_* first) ---"
  env | grep '^SLIC3R_' | sort
  echo "--- all other variables ---"
  env | grep -v '^SLIC3R_' | sort
  echo "--- what it was handed (may be binary .bgcode) ---"
  if [ -n "${1:-}" ] && [ -f "$1" ]; then
    file "$1"
    head -c 512 "$1" | od -c | head -20
  fi
  echo
} >> "$OUT" 2>&1
exit 0
