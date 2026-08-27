#!/bin/bash
PLIST_FILE="$HOME/Library/LaunchAgents/com.lko.neuralcore.plist"

if [ -f "$PLIST_FILE" ]; then
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    rm "$PLIST_FILE"
    echo "✅ LKO Mark 3.4 auto-start removed."
else
    echo "⚪ Auto-start is not installed."
fi
