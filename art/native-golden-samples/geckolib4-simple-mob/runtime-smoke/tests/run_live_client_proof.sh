#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <generated-project>" >&2
  exit 2
fi

repo_root="$(pwd)"
project="$(realpath "$1")"
client_project="${project}-client"
smoke_root="$repo_root/art/native-golden-samples/geckolib4-simple-mob/runtime-smoke"
contract="$smoke_root/client-contract.json"
gradle_home="$repo_root/.factory-ci/geckolib4/gradle-home"
server_log="$repo_root/.factory-ci/geckolib4/live-client-server.log"
client_log="$repo_root/.factory-ci/geckolib4/live-client-client.log"

host="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["connection"]["host"])' "$contract")"
port="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["connection"]["port"])' "$contract")"
mechanism="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["connection"]["mechanism"])' "$contract")"

[[ "$host" == "127.0.0.1" ]]
[[ "$port" == "25565" ]]
[[ "$mechanism" == "ConnectScreen.startConnecting@TitleScreen" ]]
command -v xvfb-run >/dev/null
command -v setsid >/dev/null

rm -rf "$client_project"
python3 - "$project" "$client_project" <<'PY'
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
shutil.copytree(
    source,
    target,
    ignore=shutil.ignore_patterns('.gradle', 'build', 'run'),
)
PY
chmod +x "$project/gradlew" "$client_project/gradlew"

mkdir -p "$project/run/server" "$client_project/run/client"
printf 'eula=true\n' > "$project/run/server/eula.txt"
cat > "$project/run/server/server.properties" <<EOF
online-mode=false
server-port=$port
spawn-protection=0
view-distance=4
simulation-distance=4
motd=Factory GeckoLib live-client proof
EOF
rm -f "$client_project/run/client/client-runtime-proof.json"

server_pid=""
client_pid=""
stop_group() {
  local pid="$1"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill -TERM -- "-$pid" 2>/dev/null || true
    sleep 1
    kill -KILL -- "-$pid" 2>/dev/null || true
  fi
}
cleanup() {
  stop_group "$client_pid"
  stop_group "$server_pid"
}
print_proof_markers() {
  echo "--- live-client proof server markers ---"
  grep -F '[GECKOLIB_CLIENT_PROOF]' "$server_log" || true
  echo "--- live-client proof client markers ---"
  grep -F '[GECKOLIB_CLIENT_PROOF]' "$client_log" || true
}
trap cleanup EXIT

setsid bash -c 'cd "$1" && exec env GRADLE_USER_HOME="$2" ./gradlew runServer --no-daemon' \
  _ "$project" "$gradle_home" >"$server_log" 2>&1 &
server_pid=$!

server_ready=0
for _ in $(seq 1 180); do
  if grep -Fq 'Done (' "$server_log"; then
    server_ready=1
    break
  fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    cat "$server_log"
    echo "live-client proof server exited before readiness" >&2
    exit 1
  fi
  sleep 1
done
if [[ "$server_ready" -ne 1 ]]; then
  cat "$server_log"
  echo "live-client proof server did not become ready" >&2
  exit 1
fi

setsid bash -c 'cd "$1" && exec env GRADLE_USER_HOME="$2" LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a ./gradlew runClient --no-daemon' \
  _ "$client_project" "$gradle_home" >"$client_log" 2>&1 &
client_pid=$!

evidence="$client_project/run/client/client-runtime-proof.json"
evidence_ready=0
for _ in $(seq 1 420); do
  if [[ -s "$evidence" ]]; then
    evidence_ready=1
    break
  fi
  if ! kill -0 "$client_pid" 2>/dev/null; then
    cat "$client_log"
    print_proof_markers
    echo "live client exited before producing runtime proof" >&2
    exit 1
  fi
  sleep 1
done
if [[ "$evidence_ready" -ne 1 ]]; then
  cat "$client_log"
  print_proof_markers
  echo "live client did not produce runtime proof" >&2
  exit 1
fi

python3 - "$evidence" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
evidence = json.loads(path.read_text(encoding='utf-8'))
required = (
    'renderer_invoked',
    'baked_model_observed',
    'texture_resolved',
    'animation_motion_observed',
)
for key in required:
    if evidence.get(key) is not True:
        raise SystemExit(f'missing live-client proof flag: {key}={evidence.get(key)!r}')
if evidence.get('texture') != 'i3_golden_mod:textures/entity/golden_sample_mob.png':
    raise SystemExit(f'unexpected live-client texture: {evidence.get("texture")!r}')
rotation = evidence.get('head_rotation_y')
if not isinstance(rotation, (int, float)):
    raise SystemExit(f'invalid head rotation evidence: {rotation!r}')
print(json.dumps(evidence, sort_keys=True))
PY

cp "$evidence" "$project/run/client-runtime-proof.json"
print_proof_markers
cat "$project/run/client-runtime-proof.json"
