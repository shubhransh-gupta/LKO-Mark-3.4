import os
import sys
import json
import logging
import subprocess
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from config import Config
from agent.loop import AgentRunner
from agent.tools.system import get_system_info, set_volume, get_clipboard, set_clipboard
from agent.tools.computer_use import take_screenshot

logger = logging.getLogger("LKO_SERVER")
ROOT_DIR = Path(__file__).parent.resolve()
STATIC_DIR = ROOT_DIR / "static"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / "com.lko.neuralcore.plist"

agent_runner = AgentRunner()
PUBLIC_TUNNEL_URL = ""

class LKOMark34Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/" or path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(STATIC_DIR / "index.html", "rb") as f:
                    self.wfile.write(f.read())
                return

            elif path in ["/landing", "/landing.html", "/marketing"]:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                docs_index = ROOT_DIR / "docs" / "index.html"
                if docs_index.exists():
                    with open(docs_index, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    with open(STATIC_DIR / "index.html", "rb") as f:
                        self.wfile.write(f.read())
                return

            elif path.startswith("/docs/"):
                file_path = ROOT_DIR / path.lstrip("/")
                if file_path.exists() and file_path.is_file():
                    self.send_response(200)
                    if file_path.suffix == ".css":
                        self.send_header("Content-Type", "text/css")
                    elif file_path.suffix == ".js":
                        self.send_header("Content-Type", "application/javascript")
                    elif file_path.suffix in [".png", ".jpg", ".jpeg"]:
                        self.send_header("Content-Type", "image/png")
                    elif file_path.suffix == ".html":
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                    return


            elif path.startswith("/static/"):
                file_path = STATIC_DIR / path.replace("/static/", "")
                if file_path.exists():
                    self.send_response(200)
                    if file_path.suffix == ".css":
                        self.send_header("Content-Type", "text/css")
                    elif file_path.suffix == ".js":
                        self.send_header("Content-Type", "application/javascript")
                    elif file_path.suffix in [".png", ".jpg", ".jpeg"]:
                        self.send_header("Content-Type", "image/png")
                    self.end_headers()
                    with open(file_path, "rb") as f:
                        self.wfile.write(f.read())
                    return
                else:
                    self.send_error(404, "Asset not found")
                    return

            elif path == "/api/system-status":
                info = get_system_info()
                info["clipboard"] = get_clipboard()
                info["model"] = agent_runner.active_model
                info["daemon_active"] = PLIST_PATH.exists()
                info["tunnel_url"] = PUBLIC_TUNNEL_URL or "http://localhost:8765"
                self._send_json(info)
                return

            elif path == "/api/validate-key":
                val_res = agent_runner.validate_key()
                self._send_json(val_res)
                return

            elif path == "/api/daemon-status":
                self._send_json({"active": PLIST_PATH.exists()})
                return

            elif path == "/api/screenshot":
                res = take_screenshot()
                if res.get("success") and os.path.exists(res["filepath"]):
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    with open(res["filepath"], "rb") as f:
                        self.wfile.write(f.read())
                    return
                else:
                    self.send_error(500, "Screenshot capture failed")
                    return

            super().do_GET()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            logger.warning(f"GET exception handled: {e}")

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"

            try:
                data = json.loads(body)
            except Exception:
                data = {}

            if path == "/api/open-hud":
                url = "http://localhost:8765"
                brave_app = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
                if os.path.exists(brave_app):
                    try:
                        subprocess.Popen([brave_app, f"--app={url}"])
                        self._send_json({"success": True, "launched": "Brave App Mode"})
                        return
                    except Exception:
                        pass
                try:
                    subprocess.Popen(["open", "-a", "Brave Browser", url])
                    self._send_json({"success": True, "launched": "Brave Browser"})
                    return
                except Exception:
                    webbrowser.open(url)
                    self._send_json({"success": True, "launched": "Default Browser"})
                    return

            elif path == "/api/open-env":
                env_file = ROOT_DIR / ".env"
                subprocess.Popen(["open", "-t", str(env_file)])
                self._send_json({"success": True})
                return

            elif path == "/api/open-captures":
                subprocess.Popen(["open", str(Config.SCREENSHOT_DIR)])
                self._send_json({"success": True})
                return

            elif path == "/api/copy-tunnel":
                url_to_copy = PUBLIC_TUNNEL_URL or "http://localhost:8765"
                set_clipboard(url_to_copy)
                self._send_json({"success": True, "url": url_to_copy})
                return

            elif path == "/api/toggle-daemon":
                if PLIST_PATH.exists():
                    try:
                        subprocess.run(["launchctl", "unload", str(PLIST_PATH)], check=False)
                        PLIST_PATH.unlink()
                        self._send_json({"success": True, "active": False})
                        return
                    except Exception as e:
                        self._send_json({"success": False, "error": str(e)})
                        return
                else:
                    try:
                        PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
                        lko_bin = str(ROOT_DIR / "LKO")
                        work_dir = str(ROOT_DIR)
                        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
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
                            f.write(plist_content)
                        subprocess.run(["launchctl", "load", str(PLIST_PATH)], check=False)
                        self._send_json({"success": True, "active": True})
                        return
                    except Exception as e:
                        self._send_json({"success": False, "error": str(e)})
                        return

            elif path == "/api/chat" or path == "/api/remote":
                message = data.get("message", "").strip()
                if not message:
                    self._send_json({"success": False, "error": "Command string cannot be empty"}, status=400)
                    return

                response_text, media = agent_runner.run_instruction(message)
                self._send_json({
                    "success": True,
                    "response": response_text,
                    "media": media
                })
                return

            elif path == "/api/set-volume":
                level = int(data.get("level", 50))
                res = set_volume(level)
                self._send_json({"success": True, "result": res})
                return

            elif path == "/api/reset":
                agent_runner.reset_chat()
                self._send_json({"success": True, "message": "Neural memory reset completed"})
                return

            elif path == "/api/config":
                env_file = ROOT_DIR / ".env"
                lines = []
                for k, v in data.items():
                    if v:
                        lines.append(f"{k}={v}")
                with open(env_file, "w") as f:
                    f.write("\n".join(lines) + "\n")
                
                Config.is_configured()
                val_res = agent_runner.validate_key()
                self._send_json({"success": True, "validation": val_res})
                return

            self.send_error(404, "Endpoint not found")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            logger.warning(f"POST exception handled: {e}")

    def _send_json(self, obj, status=200):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(obj).encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            pass

    def log_message(self, format, *args):
        pass

def set_tunnel_url(url: str):
    global PUBLIC_TUNNEL_URL
    PUBLIC_TUNNEL_URL = url

def start_server(port=8765):
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), LKOMark34Handler)
        logger.info(f"LKO Mark 3.4 Multi-Threaded Server online at http://0.0.0.0:{port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Server start error: {e}")

if __name__ == "__main__":
    start_server()
