import os
import logging
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types

from config import Config
from agent.prompts import SYSTEM_PROMPT
from agent.tools import ALL_TOOLS

logger = logging.getLogger(__name__)

# Lightweight, ultra-fast, high-availability model cascade
FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash"
]

class AgentRunner:
    def __init__(self):
        self.client = None
        self.chat = None
        self.active_model = Config.GEMINI_MODEL or "gemini-flash-lite-latest"
        self._init_client()

    def _init_client(self):
        Config.is_configured()
        if not Config.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY is not configured.")
            return False
        
        try:
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            self.reset_chat()
            logger.info(f"LKO AgentRunner initialized with model {self.active_model}.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            return False

    def validate_key(self) -> dict:
        """Validate key with fastest lightweight model."""
        self._init_client()
        if not self.client:
            return {"valid": False, "error": "No API Key provided in .env"}

        for model in [self.active_model] + FALLBACK_MODELS:
            try:
                res = self.client.models.generate_content(
                    model=model,
                    contents="LKO Mark 3.4 test. Reply with OK."
                )
                if res and res.text:
                    self.active_model = model
                    return {
                        "valid": True,
                        "model": model,
                        "message": f"Online with {model}"
                    }
            except Exception as e:
                logger.warning(f"Validation attempt failed on {model}: {str(e)[:80]}")
                continue

        return {"valid": False, "error": "API key invalid or rate limited across all lite models."}

    def _create_chat_session(self, model_name: str):
        return self.client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=ALL_TOOLS,
                temperature=0.2,
            )
        )

    def reset_chat(self):
        """Reset conversation session history with fallback."""
        if not self.client:
            return
        
        models_to_try = [self.active_model] + [m for m in FALLBACK_MODELS if m != self.active_model]
        
        for model in models_to_try:
            try:
                self.chat = self._create_chat_session(model)
                self.active_model = model
                return
            except Exception as e:
                logger.warning(f"Could not create chat with model {model}: {e}")

    def run_instruction(self, instruction: str, image_path: str = None) -> tuple[str, list[str]]:
        """
        Execute an instruction with automatic fallback across low-level lite models if 503/429 occurs.
        """
        if not self.client or not self.chat:
            success = self._init_client()
            if not success or not self.chat:
                return ("LKO Error: Gemini API key is missing or invalid. Check .env configuration.", [])

        media_to_send: list[str] = []
        contents = []

        if image_path and os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                contents.append(img)
            except Exception as e:
                logger.warning(f"Could not load input image: {e}")
                
        contents.append(instruction)

        # Try active model first, then fallback through lite models if 503/429 occurs
        models_to_try = [self.active_model] + [m for m in FALLBACK_MODELS if m != self.active_model]
        last_error = ""

        for model in models_to_try:
            try:
                if self.active_model != model or not self.chat:
                    self.chat = self._create_chat_session(model)
                    self.active_model = model

                response = self.chat.send_message(contents)
                response_text = response.text if response.text else "Command executed successfully by LKO."
                
                if "screenshot" in instruction.lower() or "see" in instruction.lower():
                    screenshots = sorted(
                        Config.SCREENSHOT_DIR.glob("screenshot_*.png"),
                        key=os.path.getmtime,
                        reverse=True
                    )
                    if screenshots:
                        media_to_send.append(str(screenshots[0]))

                return response_text, media_to_send
            except Exception as e:
                err_str = str(e)
                last_error = err_str
                logger.warning(f"Model {model} failed with: {err_str[:90]}. Trying next fallback model...")
                # Reset chat on error so next model has a clean session
                self.chat = None
                continue

        return f"Execution Error: {last_error}", []
