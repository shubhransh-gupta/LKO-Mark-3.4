import subprocess
import os

# Block list of potentially destructive commands for safety
BLOCKED_COMMANDS = [
    "rm -rf /",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",
    "> /dev/sda"
]

def run_shell_command(command: str) -> str:
    """
    Execute a shell/terminal command on macOS and return its stdout/stderr.
    Use for checking files, system stats, git, running scripts, etc.
    """
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return f"Security Error: Command blocked by safety policy: {command}"
            
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.expanduser("~")
        )
        out = proc.stdout
        err = proc.stderr
        
        result = []
        if out:
            result.append(f"Output:\n{out.strip()}")
        if err:
            result.append(f"Error:\n{err.strip()}")
        if not out and not err:
            result.append("Command completed with no output.")
            
        return "\n".join(result)
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Execution error: {str(e)}"
