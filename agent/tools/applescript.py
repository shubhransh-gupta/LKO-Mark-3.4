import subprocess
import time
import json

def run_applescript(script: str) -> str:
    """Execute an AppleScript snippet and return stdout or stderr."""
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=25
        )
        if proc.returncode != 0:
            return f"AppleScript Error: {proc.stderr.strip()}"
        return proc.stdout.strip() if proc.stdout.strip() else "Success"
    except subprocess.TimeoutExpired:
        return "Error: AppleScript execution timed out."
    except Exception as e:
        return f"Error executing AppleScript: {str(e)}"

def send_slack_message(target: str, message: str) -> str:
    """
    Send a message to a specific person or channel on Slack.
    Uses macOS UI automation to activate Slack, jump to conversation (Cmd+K), and send.
    """
    # Escape quotes for AppleScript
    safe_target = target.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    
    script = f'''
    tell application "Slack"
        activate
    end tell
    delay 0.5
    tell application "System Events"
        tell process "Slack"
            -- Open Quick Switcher (Cmd + K)
            keystroke "k" using {{command down}}
            delay 0.4
            -- Type target channel/person
            keystroke "{safe_target}"
            delay 0.6
            -- Select first match
            key code 36 -- Enter
            delay 0.5
            -- Type and send message
            keystroke "{safe_msg}"
            delay 0.2
            key code 36 -- Enter
        end tell
    end tell
    return "Message sent to " & "{safe_target}" & " on Slack"
    '''
    return run_applescript(script)

def send_imessage(recipient: str, message: str) -> str:
    """Send an iMessage / SMS via the macOS Messages app."""
    safe_rec = recipient.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    script = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{safe_rec}" of targetService
        send "{safe_msg}" to targetBuddy
    end tell
    return "iMessage sent to {safe_rec}"
    '''
    return run_applescript(script)

def control_spotify(action: str) -> str:
    """Control Spotify (play, pause, next, previous, status)."""
    action = action.lower().strip()
    if action == "playpause":
        script = 'tell application "Spotify" to playpause'
    elif action == "play":
        script = 'tell application "Spotify" to play'
    elif action == "pause":
        script = 'tell application "Spotify" to pause'
    elif action == "next":
        script = 'tell application "Spotify" to next track'
    elif action == "previous":
        script = 'tell application "Spotify" to previous track'
    elif action == "status":
        script = '''
        tell application "Spotify"
            if player state is playing then
                return "Playing: " & name of current track & " by " & artist of current track
            else
                return "Spotify is paused"
            end if
        end tell
        '''
    else:
        return f"Unknown Spotify action: {action}"
    return run_applescript(script)

def show_notification(title: str, message: str) -> str:
    """Display a native macOS notification banner."""
    safe_title = title.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "{safe_title}"'
    return run_applescript(script)
