#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export GRADLE_USER_HOME="$PWD/.i10-gradle-user-home"
mkdir -p "$GRADLE_USER_HOME"

if [[ ! -f I10-SOURCE-COMMIT.txt ]]; then
  echo "ERROR: I10-SOURCE-COMMIT.txt is missing." >&2
  exit 1
fi

chmod +x gradlew
exec python3 run-i10-manual-process.py server
