#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../backend"

mkdir -p uploads logs

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
