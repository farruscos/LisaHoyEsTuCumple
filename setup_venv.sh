#!/bin/bash
cd "$(dirname "$0")"
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo ""
echo "Virtual environment created and dependencies installed!"
echo "To activate the environment, run: source venv/bin/activate"
