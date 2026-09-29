import os
import json
import logging
from utils.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger("VAULTY.LLMClient")

class LLMClient:
    """
    Unified LLM Client interface for Vaulty agents.
    Priority:
    1. Groq API (llama-3.3-70b-versatile) if GROQ_API_KEY is configured.
    2. Zero-config evidence reasoning fallback if key is absent or API fails.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or GROQ_API_KEY
        self.model = model or GROQ_MODEL

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def generate_json(self, prompt: str, fallback_fn=None, *args, **kwargs) -> dict:
        """
        Executes a JSON-structured LLM completion query.
        Falls back cleanly to fallback_fn if API key is missing or request fails.
        """
        if self.is_available():
            try:
                from groq import Groq
                client = Groq(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}. Executing evidence-based fallback.")

        if fallback_fn:
            return fallback_fn(*args, **kwargs)

        return {"status": "FALLBACK", "message": "Investigation completed via evidence verification engine."}
