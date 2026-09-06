#!/usr/bin/env bash
# 設計書どおりの順で全実験を走らせる。途中で止めても runs.jsonl は 1 セッションごとに追記済み。
# 使い方: bench/run_all.sh [tag]   （python3 を uv run で呼ぶ環境なら PY="uv run python3" bench/run_all.sh）
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-python3}"
TAG="${1:-$(date +%Y%m%d_%H%M%S)}"
JOBS="${JOBS:-2}"
run() { $PY bench/run.py run --tag "$TAG" --jobs "$JOBS" "$@"; }

run --exp base    --scale small --model sonnet -n 1
run --exp base    --scale large --model sonnet -n 1
run --exp base    --scale large --model haiku  -n 1
run --exp trap    --scale small --model sonnet -n 5
run --exp trap    --scale large --model sonnet -n 5
run --exp newtask --scale large --model sonnet -n 5
run --exp chain   --scale large --model sonnet -n 5
run --exp trap    --scale large --model haiku  -n 5
run --exp trap    --scale large --model sonnet -n 5 --delegate
$PY bench/run.py summary
$PY bench/run.py fig
