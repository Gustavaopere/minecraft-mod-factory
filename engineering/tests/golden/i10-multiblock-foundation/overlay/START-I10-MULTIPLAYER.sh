#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export GRADLE_USER_HOME="$PWD/.i10-gradle-user-home"
mkdir -p "$GRADLE_USER_HOME"

if [[ ! -f I10-SOURCE-COMMIT.txt ]]; then
  echo "ERROR: I10-SOURCE-COMMIT.txt is missing." >&2
  exit 1
fi

commit="$(tr -d '\r\n' < I10-SOURCE-COMMIT.txt)"
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]]; then
  echo "ERROR: I10-SOURCE-COMMIT.txt must contain one full lowercase Git commit SHA." >&2
  exit 1
fi

chmod +x gradlew
exec python3 run-i10-multiplayer-acceptance.py --commit "$commit"
