import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from PIL import Image
import pyautogui
from config import Config

# Safety settings for PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

def get_screen_size() -> dict:
    """Get the current screen width and height."""
    w, h = pyautogui.size()
    return {"width": w, "height": h}

def take_screenshot(filename: str = "") -> dict:
    """
    Capture the entire screen and save it as an image.
    Returns path and dimensions for vision analysis.
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
    
    filepath = Config.SCREENSHOT_DIR / filename
    
    try:
        # Use native macOS screencapture for high fidelity
        subprocess.run(["screencapture", "-x", str(filepath)], check=True)
        
        # Optimize size for Gemini Vision if needed
        with Image.open(filepath) as img:
            w, h = img.size
            if w > Config.SCREENSHOT_MAX_WIDTH:
                ratio = Config.SCREENSHOT_MAX_WIDTH / float(w)
                new_h = int(float(h) * ratio)
                resized = img.resize((Config.SCREENSHOT_MAX_WIDTH, new_h), Image.Resampling.LANCZOS)
                resized.save(filepath, optimize=True)
                w, h = Config.SCREENSHOT_MAX_WIDTH, new_h

        return {
            "success": True,
            "filepath": str(filepath),
            "width": w,
            "height": h,
            "message": f"Screenshot saved to {filepath.name}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """
    Click at specific (x, y) screen coordinates.
    button can be 'left', 'right', or 'middle'.
    """
    try:
        pyautogui.click(x=x, y=y, clicks=clicks, button=button)
        return f"Clicked {button} at ({x}, {y}) {clicks} time(s)"
    except Exception as e:
        return f"Click failed: {str(e)}"

def double_click(x: int, y: int) -> str:
    """Double click at specific (x, y) coordinates."""
    return click(x, y, clicks=2)

def right_click(x: int, y: int) -> str:
    """Right click at specific (x, y) coordinates."""
    return click(x, y, button="right")

def mouse_move(x: int, y: int) -> str:
    """Move the mouse cursor to (x, y)."""
    try:
        pyautogui.moveTo(x, y, duration=0.2)
        return f"Moved cursor to ({x}, {y})"
    except Exception as e:
        return f"Move failed: {str(e)}"

def type_text(text: str) -> str:
    """Type arbitrary text using the keyboard."""
    try:
        pyautogui.write(text, interval=0.02)
        return f"Typed: {text}"
    except Exception as e:
        return f"Type failed: {str(e)}"

def press_key(key: str) -> str:
    """Press a single key (e.g., 'enter', 'tab', 'esc', 'space', 'backspace', 'up', 'down')."""
    try:
        pyautogui.press(key.lower())
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Press key failed: {str(e)}"

def hotkey(*keys: str) -> str:
    """
    Press a combination of keys simultaneously (e.g. 'command', 'space' or 'ctrl', 'c').
    """
    try:
        pyautogui.hotkey(*[k.lower() for k in keys])
        return f"Pressed shortcut: {'+'.join(keys)}"
    except Exception as e:
        return f"Hotkey failed: {str(e)}"
