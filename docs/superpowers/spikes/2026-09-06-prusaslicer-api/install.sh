#!/bin/sh
# Copy the spike bundle into PrusaSlicer's user plugin folder.
set -eu
DATADIR="${PRUSA_DATADIR:-$HOME/Library/Application Support/PrusaSlicer3-dev}"
DEST="$DATADIR/lua/com.printernizer.spike"
if [ ! -d "$DATADIR" ]; then
  echo "Data directory not found: $DATADIR" >&2
  echo "Set PRUSA_DATADIR to override." >&2
  exit 1
fi
mkdir -p "$DEST"
cp "$(dirname "$0")"/bundle/* "$DEST/"
echo "Installed to: $DEST"
ls -1 "$DEST"
