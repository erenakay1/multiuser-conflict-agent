#!/usr/bin/env bash
# Dış benchmark repolarını external/ altına klonlar (external/ git tarafından yok sayılır).
# Kullanım: bash scripts/setup_external.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT="$ROOT/external"
mkdir -p "$EXT"

clone() {
  local url="$1" name="$2"
  if [ -d "$EXT/$name/.git" ]; then
    echo "[skip] $name zaten var ($EXT/$name)"
  else
    echo "[clone] $url -> $EXT/$name"
    git clone --depth 1 "$url" "$EXT/$name"
  fi
}

clone https://github.com/Kordi-AI/Multi-User-LLM-Agent.git Muses-Bench
clone https://github.com/YuanJrShiuan/Harness-MulUser.git Harness-MU

echo "Tamamlandı. Her reponun kendi README'sindeki kurulum adımlarını izleyin."
