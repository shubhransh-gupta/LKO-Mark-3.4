import os
import sys
import re
import threading
import subprocess
import logging
from pathlib import Path

import objc
from Foundation import (
    NSObject,
    NSProcessInfo,
    NSURL,
    NSURLRequest,
    NSRect,
    NSPoint,
    NSSize
)
from AppKit import (
    NSApplication,
    NSApp,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSPopover,
    NSPopoverBehaviorTransient,
    NSViewController,
    NSApplicationActivationPolicyAccessory,
    NSMenu,
    NSMenuItem,
    NSImage,
    NSEvent,
    NSEventMaskLeftMouseDown,
    NSEventMaskRightMouseDown,
    NSRectEdgeMaxY
)
from WebKit import WKWebView, WKWebViewConfiguration

from config import Config
from agent.loop import AgentRunner
from bridge.telegram_bot import TelegramBridge
from server import start_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("LKO")

HUD_PORT = 8765
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / "com.lko.neuralcore.plist"

try:
    NSProcessInfo.processInfo().setProcessName_("LKO")
except Exception:
    pass

class LKOPopoverController(NSObject):
    def init(self):
        self = objc.super(LKOPopoverController, self).init()
        if self is None:
            return None
        
        self.agent_runner = AgentRunner()
        self.telegram_bridge = TelegramBridge(
            agent_runner=self.agent_runner,
            on_activity_callback=self.on_activity_update
        )
        self.tunnel_process = None
        self.public_tunnel_url = None
        
        # 1. Status Bar Item with Arc Reactor Bubble Icon
        self.status_bar = NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(NSVariableStatusItemLength)
        self.button = self.status_item.button()
        
        icon_path = str(Config.ROOT_DIR / "static" / "arc_reactor_icon.png")
        if os.path.exists(icon_path):
            image = NSImage.alloc().initWithContentsOfFile_(icon_path)
            if image:
                image.setSize_(NSSize(18, 18))
                self.button.setImage_(image)
                self.button.setTitle_("")
        else:
            self.button.setTitle_("⎊")
            
        self.button.setTarget_(self)
        self.button.setAction_("togglePopover:")
        self.button.sendActionOn_(NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown)
        
        # 2. Native Translucent Popover matching Aerolite dimensions
        self.popover = NSPopover.alloc().init()
        self.popover.setBehavior_(NSPopoverBehaviorTransient)
        self.popover.setAnimates_(True)
        
        # 3. Create WebKit View loading local Aerolite-styled menu (/menu)
        config = WKWebViewConfiguration.alloc().init()
        rect = NSRect(NSPoint(0, 0), NSSize(320, 600))
        self.webview = WKWebView.alloc().initWithFrame_configuration_(rect, config)
        self.webview.setValue_forKey_(False, "drawsBackground")
        
        url = NSURL.URLWithString_(f"http://127.0.0.1:{HUD_PORT}/menu")
        req = NSURLRequest.requestWithURL_(url)
        self.webview.loadRequest_(req)
        
        # 4. View Controller Container
        self.view_controller = NSViewController.alloc().init()
        self.view_controller.setView_(self.webview)
        self.popover.setContentViewController_(self.view_controller)
        self.popover.setContentSize_(NSSize(320, 600))
        
        # 5. Right Click Context Menu
        self.context_menu = NSMenu.alloc().init()
        
        m_title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("⎊ LKO MARK 3.4 // NEURAL AGENT", None, "")
        m_title.setEnabled_(False)
        self.context_menu.addItem_(m_title)
        self.context_menu.addItem_(NSMenuItem.separatorItem())
        
        self.m_dash = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🚀 Open Full Tactical HUD (Brave)", "openDashboard:", "d")
        self.m_dash.setTarget_(self)
        self.context_menu.addItem_(self.m_dash)
        
        self.m_url = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("📱 Copy Mobile Uplink...", "copyMobileUrl:", "")
        self.m_url.setTarget_(self)
        self.context_menu.addItem_(self.m_url)
        
        self.m_reload = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("🔄 Reload Menu Widget", "reloadHUD:", "r")
        self.m_reload.setTarget_(self)
        self.context_menu.addItem_(self.m_reload)
        
        self.context_menu.addItem_(NSMenuItem.separatorItem())
        
        self.m_autostart = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"🚀 24/7 Background Daemon: {'ON' if PLIST_PATH.exists() else 'OFF'}", "toggleAutostart:", ""
        )
        self.m_autostart.setTarget_(self)
        self.context_menu.addItem_(self.m_autostart)
        
        m_env = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("⚙️ Calibrate Systems (.env)", "openEnv:", "")
        m_env.setTarget_(self)
        self.context_menu.addItem_(m_env)
        
        self.context_menu.addItem_(NSMenuItem.separatorItem())
        
        m_quit = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("❌ Shutdown LKO", "quitApp:", "q")
        m_quit.setTarget_(self)
        self.context_menu.addItem_(m_quit)

        # 6. Start Background Threads
        self.start_background_services()
        
        return self

    def togglePopover_(self, sender):
        event = NSApp.currentEvent()
        if event and event.type() == NSEventMaskRightMouseDown:
            self.status_item.popUpStatusItemMenu_(self.context_menu)
            return

        if self.popover.isShown():
            self.popover.performClose_(sender)
        else:
            self.popover.showRelativeToRect_ofView_preferredEdge_(
                self.button.bounds(),
                self.button,
                NSRectEdgeMaxY
            )

    def on_activity_update(self, activity_text: str):
        if "Running" in activity_text or "Processing" in activity_text or "Order" in activity_text:
            self.button.setTitle_(" 🟡")
        else:
            self.button.setTitle_("")

    def start_background_services(self):
        # 1. Start Local HTTP Server
        threading.Thread(target=start_server, args=(HUD_PORT,), daemon=True).start()
        
        # 2. Validate Gemini Key
        threading.Thread(target=self._validate_key, daemon=True).start()
        
        # 3. Start Cloudflare Mobile Tunnel
        threading.Thread(target=self._run_tunnel, daemon=True).start()
        
        # 4. Start Telegram Bot if configured
        if Config.TELEGRAM_BOT_TOKEN and Config.ALLOWED_TELEGRAM_USER_IDS:
            def run_bot():
                try:
                    self.telegram_bridge.run_polling_sync()
                except Exception as e:
                    logger.exception("Error in Telegram polling")
            threading.Thread(target=run_bot, daemon=True).start()

    def _validate_key(self):
        val = self.agent_runner.validate_key()
        if not val.get("valid"):
            self.button.setTitle_(" 🔴")

    def _run_tunnel(self):
        cloudflared_bin = "/opt/homebrew/bin/cloudflared"
        if not os.path.exists(cloudflared_bin):
            cloudflared_bin = "cloudflared"

        try:
            self.tunnel_process = subprocess.Popen(
                [cloudflared_bin, "tunnel", "--url", f"http://127.0.0.1:{HUD_PORT}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in self.tunnel_process.stdout:
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    self.public_tunnel_url = match.group(0)
                    self.m_url.setTitle_(f"📱 Mobile: {self.public_tunnel_url}")
                    from server import set_tunnel_url
                    set_tunnel_url(self.public_tunnel_url)
                    break
        except Exception as e:
            logger.warning(f"Tunnel warning: {e}")

    def openDashboard_(self, sender):
        url = f"http://localhost:{HUD_PORT}"
        brave_app = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        if os.path.exists(brave_app):
            try:
                subprocess.Popen([brave_app, f"--app={url}"])
                return
            except Exception:
                pass
        try:
            subprocess.Popen(["open", "-a", "Brave Browser", url])
        except Exception:
            pass

    def copyMobileUrl_(self, sender):
        if self.public_tunnel_url:
            from agent.tools.system import set_clipboard
            set_clipboard(self.public_tunnel_url)
            try:
                subprocess.Popen(["open", "-a", "Brave Browser", self.public_tunnel_url])
            except Exception:
                pass

    def reloadHUD_(self, sender):
        url = NSURL.URLWithString_(f"http://127.0.0.1:{HUD_PORT}/menu")
        req = NSURLRequest.requestWithURL_(url)
        self.webview.loadRequest_(req)

    def toggleAutostart_(self, sender):
        if PLIST_PATH.exists():
            subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
            PLIST_PATH.unlink()
            self.m_autostart.setTitle_("🚀 24/7 Background Daemon: OFF")
        else:
            PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
            lko_bin = str(Config.ROOT_DIR / "LKO")
            work_dir = str(Config.ROOT_DIR)
            content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lko.neuralcore</string>
    <key>ProgramArguments</key>
    <array>
        <string>{lko_bin}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{work_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{work_dir}/lko_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{work_dir}/lko_stderr.log</string>
</dict>
</plist>"""
            with open(PLIST_PATH, "w") as f:
                f.write(content)
            subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=False)
            self.m_autostart.setTitle_("🚀 24/7 Background Daemon: ON")

    def openEnv_(self, sender):
        env_path = Config.ROOT_DIR / ".env"
        subprocess.run(["open", "-t", str(env_path)])

    def quitApp_(self, sender):
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
            except Exception:
                pass
        NSApp.terminate_(self)

global_controller = None

def main():
    global global_controller
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    global_controller = LKOPopoverController.alloc().init()
    app.run()

if __name__ == "__main__":
    main()
