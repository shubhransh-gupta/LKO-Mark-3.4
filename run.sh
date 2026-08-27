#!/bin/bash
cd "$(dirname "$0")"

echo "⚡ Launching LKO Mark 3.4..."
if [ -f ".venv/bin/python3" ]; then
    exec .venv/bin/python3 app.py
else
    exec python3 app.py
fi
