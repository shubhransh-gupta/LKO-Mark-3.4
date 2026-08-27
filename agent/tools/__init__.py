from agent.tools.applescript import (
    send_slack_message,
    send_imessage,
    control_spotify,
    show_notification,
    run_applescript
)
from agent.tools.computer_use import (
    take_screenshot,
    click,
    double_click,
    right_click,
    mouse_move,
    type_text,
    press_key,
    hotkey,
    get_screen_size
)
from agent.tools.system import (
    open_application,
    open_url,
    get_system_info,
    set_volume,
    get_clipboard,
    set_clipboard,
    get_frontmost_app
)
from agent.tools.shell import run_shell_command

# List of all callable Python tool functions for Gemini Function Calling
ALL_TOOLS = [
    send_slack_message,
    send_imessage,
    control_spotify,
    show_notification,
    run_applescript,
    take_screenshot,
    click,
    double_click,
    right_click,
    mouse_move,
    type_text,
    press_key,
    hotkey,
    get_screen_size,
    open_application,
    open_url,
    get_system_info,
    set_volume,
    get_clipboard,
    set_clipboard,
    get_frontmost_app,
    run_shell_command,
]
