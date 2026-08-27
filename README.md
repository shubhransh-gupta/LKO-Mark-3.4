# ⚡ LKO Mark 3.4 // Neural macOS Assistant & Remote Control System

**LKO Mark 3.4** is an autonomous, real-time macOS Neural Assistant with a **Tony Stark Holographic Web HUD**, an **Aerolite Obsidian Menu Bar Widget**, native macOS **AppleScript automation**, **Computer Use screen vision**, and **automatic mobile remote access**.

---

## ✨ Features

- **⎊ Menu Bar Popover Widget (Aerolite Obsidian Theme)**:
  - Concentric Arc Reactor status bar icon.
  - Quick action pills for 1-click HUD launch, inline Slack message dispatcher, optical screen analysis, and LaunchAgent daemon controls.
  - Live **Tracked Systems Radar Map** with active macOS application node, battery reserve, volume slider, and smooth 360° rotating radar sweep.

- **🦾 Holographic Tactical Web HUD (`http://localhost:8765`)**:
  - Full-screen futuristic cyberpunk flight deck featuring 3D animated Arc Reactor (`3.4 GW Nominal`), quantum audio waveforms, and retina screen vision feeds.
  - Integrated speech-to-text and synthesized British/AI voice responses.

- **🌐 Automatic Mobile Gateway (Cloudflare HTTPS Tunnel)**:
  - Instant encrypted public mobile tunnel (`https://*.trycloudflare.com`) generated on launch. Control your Mac from anywhere on mobile cellular 5G/4G or remote Wi-Fi.

- **💬 Native AppleScript & System Automations**:
  - Send messages to any Slack channel or user (`#general`, `@teammate`) via Quick Switcher.
  - Capture full-screen screenshots, manage volume, inspect clipboard, open URLs, and launch applications.

- **⚡ Gemini Flash-Lite Neural Engine**:
  - Powered by `gemini-flash-lite-latest` with automatic multi-model failover for high availability and zero rate-limiting delays.

---

## 🚀 Getting Started

### 1. Prerequisites
- macOS 12+ (Monterey, Ventura, Sonoma, Sequoia)
- Python 3.10+
- [Cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/) (optional, for remote mobile access):
  ```bash
  brew install cloudflared
  ```

### 2. Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shubhransh-gupta/LKO-Mark-3.4.git
   cd LKO-Mark-3.4
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API Key**:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and insert your [Google Gemini API Key](https://aistudio.google.com):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-flash-lite-latest
   ```

---

## 🏃‍♂️ Running LKO

### Start LKO Interactive Mode:
```bash
./run.sh
```

### Install as 24/7 Always-On Background Daemon:
```bash
./install_autostart.sh
```
*(To uninstall auto-start at any time, run `./uninstall_autostart.sh`)*

---

## 🔒 Security & Privacy

- All API keys and credentials are stored strictly in local `.env` files (gitignored).
- Local screenshot captures and system telemetry are processed locally on your Mac.
- Tunnels are created on-demand and fully encrypted.

---

## 📄 License
MIT License. Created with ❤️ for autonomous AI pair programming.
