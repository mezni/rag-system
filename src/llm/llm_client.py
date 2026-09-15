from typing import Optional

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Client for interacting with LLM providers via OpenRouter."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self.base_url = self.config.get("api", {}).get("base_url", "https://openrouter.ai/api/v1")
        self.model = self.config.get("models", {}).get("chat", {}).get(
        "model", "openai/gpt-4o-mini"
    )
        self.temperature = self.config.get("models", {}).get("chat", {}).get("temperature", 0.3)
        self.max_tokens = self.config.get("models", {}).get("chat", {}).get("max_tokens", 4096)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        import httpx

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def _get_api_key(self) -> str:
        """Get the API key from environment."""
        import os

        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")
        return key