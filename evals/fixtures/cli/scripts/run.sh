#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
deno run --allow-env src/main.ts "$@"
