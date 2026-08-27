#!/bin/bash
cd "$(dirname "$0")"
DIR="$(pwd)"

PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.lko.neuralcore.plist"

mkdir -p "$PLIST_DIR"

cat <<EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lko.neuralcore</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DIR/LKO</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$DIR/lko_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$DIR/lko_stderr.log</string>
</dict>
</plist>
EOF

# Unload previous instance if any and load fresh service
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo "✅ LKO Mark 3.4 is now installed as a native 'LKO' macOS background application!"
echo "⚡ In System Settings > Login Items, it will appear cleanly as 'LKO'."
