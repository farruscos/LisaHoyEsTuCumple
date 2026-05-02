#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ -x "venv/bin/python" ]; then
    venv/bin/python extract_audio.py
else
    python3 extract_audio.py
fi
