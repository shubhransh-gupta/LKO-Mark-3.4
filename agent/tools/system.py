import subprocess
import json
from agent.tools.applescript import run_applescript

def open_application(app_name: str) -> str:
    """Open or focus a macOS application by name (e.g., 'Slack', 'Safari', 'Spotify', 'Finder')."""
    try:
        res = subprocess.run(["open", "-a", app_name], capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return f"Failed to open {app_name}: {res.stderr.strip()}"
        return f"Opened application {app_name}"
    except Exception as e:
        return f"Error opening application: {str(e)}"

def open_url(url: str) -> str:
    """Open a URL in Brave Browser (or default browser)."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        subprocess.run(["open", "-a", "Brave Browser", url], check=True, timeout=10)
        return f"Opened URL {url} in Brave Browser"
    except Exception:
        try:
            subprocess.run(["open", url], check=True, timeout=10)
            return f"Opened URL {url}"
        except Exception as e:
            return f"Error opening URL: {str(e)}"

def get_frontmost_app() -> str:
    """Get the name of the currently active/frontmost application."""
    script = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
    end tell
    return frontApp
    '''
    return run_applescript(script)

def get_system_info() -> dict:
    """Get system battery, current volume, and active frontmost application."""
    active_app = get_frontmost_app()
    volume_res = run_applescript("output volume of (get volume settings)")
    
    # Battery status
    try:
        pm = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True).stdout
    except Exception:
        pm = "Unknown"
        
    return {
        "active_application": active_app,
        "volume_percent": volume_res,
        "battery_info": pm.strip()
    }

def set_volume(level: int) -> str:
    """Set system output volume from 0 to 100."""
    level = max(0, min(100, level))
    script = f"set volume output volume {level}"
    return run_applescript(script)

def get_clipboard() -> str:
    """Read the current text content from the macOS clipboard."""
    try:
        res = subprocess.run(["pbpaste"], capture_output=True, text=True)
        return res.stdout
    except Exception as e:
        return f"Clipboard error: {str(e)}"

def set_clipboard(text: str) -> str:
    """Copy text to the macOS clipboard."""
    try:
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=text)
        return f"Copied to clipboard: {text[:50]}..."
    except Exception as e:
        return f"Clipboard error: {str(e)}"
