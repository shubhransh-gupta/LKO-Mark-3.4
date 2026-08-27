import os
import asyncio
import logging
from pathlib import Path
from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import Config
from agent.loop import AgentRunner

logger = logging.getLogger(__name__)

class TelegramBridge:
    def __init__(self, agent_runner: AgentRunner, on_activity_callback=None):
        self.agent_runner = agent_runner
        self.on_activity_callback = on_activity_callback
        self.app = None
        self.is_running = False
        self._task = None

    def _is_authorized(self, update: Update) -> bool:
        user = update.effective_user
        if not user:
            return False
        
        # If no whitelist is defined, warn and block for security
        if not Config.ALLOWED_TELEGRAM_USER_IDS:
            logger.warning("No ALLOWED_TELEGRAM_USER_IDS specified in .env! Blocking request for safety.")
            return False
            
        if user.id not in Config.ALLOWED_TELEGRAM_USER_IDS:
            logger.warning(f"Unauthorized access attempt from User ID: {user.id} (@{user.username})")
            return False
            
        return True

    def _notify_ui(self, msg: str):
        if self.on_activity_callback:
            try:
                self.on_activity_callback(msg)
            except Exception:
                pass

    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            await update.message.reply_text(
                f"⛔ Unauthorized. Your Telegram User ID is `{update.effective_user.id}`. Add this ID to `ALLOWED_TELEGRAM_USER_IDS` in `.env`.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        welcome_text = (
            "🤖 *MacRemote Agent Connected!*\n\n"
            "You can send me any instruction from your phone, and I'll execute it on your Mac.\n\n"
            "*Example Commands:*\n"
            "• `Send a message 'Hello team' to #general on Slack`\n"
            "• `Take a screenshot of my Mac`\n"
            "• `Play some jazz on Spotify and set volume to 50%`\n"
            "• `Open Safari to github.com`\n"
            "• `Check battery status and current app`\n\n"
            "*Control Commands:*\n"
            "/status - Check Mac & Agent status\n"
            "/screenshot - Take and receive instant screenshot\n"
            "/reset - Reset conversation memory\n"
            "/help - Show command list"
        )
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        from agent.tools.system import get_system_info
        info = get_system_info()
        msg = (
            "🍏 *Mac System Status:*\n"
            f"• *Active App:* `{info.get('active_application', 'Unknown')}`\n"
            f"• *Volume:* `{info.get('volume_percent', 'Unknown')}%`\n"
            f"• *Battery:* `{info.get('battery_info', 'Unknown')}`\n"
            f"• *Model:* `{Config.GEMINI_MODEL}`"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def reset_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        self.agent_runner.reset_chat()
        await update.message.reply_text("🔄 Conversation session reset.", parse_mode=ParseMode.MARKDOWN)

    async def screenshot_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
        from agent.tools.computer_use import take_screenshot
        res = take_screenshot()
        if res.get("success"):
            with open(res["filepath"], "rb") as photo:
                await update.message.reply_photo(photo=photo, caption="📸 Current Mac Screen")
        else:
            await update.message.reply_text(f"❌ Failed to take screenshot: {res.get('error')}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return

        text = update.message.text
        if not text:
            return

        self._notify_ui(f"Running: {text[:30]}...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # Run via Gemini agent
        loop = asyncio.get_running_loop()
        response_text, media_list = await loop.run_in_executor(
            None, self.agent_runner.run_instruction, text, None
        )

        self._notify_ui("Idle")

        # Reply with text
        try:
            await update.message.reply_text(response_text)
        except Exception:
            # Fallback if markdown parsing fails
            await update.message.reply_text(response_text)

        # Send any screenshots or images requested/produced
        for media_path in media_list:
            if os.path.exists(media_path):
                try:
                    with open(media_path, "rb") as photo:
                        await update.message.reply_photo(photo=photo)
                except Exception as e:
                    logger.error(f"Error sending photo {media_path}: {e}")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return

        voice = update.message.voice or update.message.audio
        if not voice:
            return

        await update.message.reply_text("🎙️ Processing voice instruction...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # Download voice file
        file = await context.bot.get_file(voice.file_id)
        voice_path = Config.SCREENSHOT_DIR / f"voice_{voice.file_id}.ogg"
        await file.download_to_drive(custom_path=voice_path)

        # Transcribe & process via Gemini
        prompt = "Listen to this audio note from my phone and execute the requested instructions on this Mac."
        loop = asyncio.get_running_loop()
        response_text, media_list = await loop.run_in_executor(
            None, self.agent_runner.run_instruction, prompt, str(voice_path)
        )

        # Cleanup voice file
        try:
            if voice_path.exists():
                voice_path.unlink()
        except Exception:
            pass

        await update.message.reply_text(response_text)
        for media_path in media_list:
            if os.path.exists(media_path):
                with open(media_path, "rb") as photo:
                    await update.message.reply_photo(photo=photo)

    def build_application(self):
        self.app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.app.add_handler(CommandHandler("start", self.start_cmd))
        self.app.add_handler(CommandHandler("help", self.start_cmd))
        self.app.add_handler(CommandHandler("status", self.status_cmd))
        self.app.add_handler(CommandHandler("reset", self.reset_cmd))
        self.app.add_handler(CommandHandler("screenshot", self.screenshot_cmd))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, self.handle_voice))

    def run_polling_sync(self):
        """Run bot polling synchronously (meant for background thread)."""
        self.build_application()
        self.is_running = True
        logger.info("Telegram Bot started polling...")
        self.app.run_polling(drop_pending_updates=True, close_loop=False)
