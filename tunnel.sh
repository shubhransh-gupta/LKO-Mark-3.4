#!/bin/bash
cd "$(dirname "$0")"

echo "🌐 Starting Cloudflare Secure Mobile Tunnel for LKO Mark 3.4..."
echo "📱 You can open the generated HTTPS link on your phone from anywhere!"
echo "---------------------------------------------------------------"
/opt/homebrew/bin/cloudflared tunnel --url http://localhost:8765
