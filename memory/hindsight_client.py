import requests
import json
import logging
from utils.config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL

logger = logging.getLogger("VAULTY.HindsightClient")

class HindsightClient:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or HINDSIGHT_API_KEY
        self.base_url = (base_url or HINDSIGHT_BASE_URL).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            res = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=2)
            return res.status_code == 200
        except Exception:
            return False

    def retain(self, bank_id: str, content: str, metadata: dict = None) -> bool:
        """Stores a lesson, experience, or reflection in Hindsight memory bank."""
        if not self.is_available():
            return False
        try:
            url = f"{self.base_url}/banks/{bank_id}/memories"
            payload = {
                "content": content,
                "metadata": metadata or {}
            }
            res = requests.post(url, headers=self.headers, json=payload, timeout=5)
            return res.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Hindsight retain failed: {e}")
            return False

    def recall(self, bank_id: str, query: str, top_k: int = 3) -> list:
        """Recalls conceptually relevant memories from Hindsight bank."""
        if not self.is_available():
            return []
        try:
            url = f"{self.base_url}/banks/{bank_id}/recall"
            payload = {"query": query, "top_k": top_k}
            res = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return data.get("memories", [])
            return []
        except Exception as e:
            logger.error(f"Hindsight recall failed: {e}")
            return []

    def reflect(self, bank_id: str, query: str) -> dict:
        """Reflects across Hindsight memory bank to produce a grounded reasoning response."""
        if not self.is_available():
            return {}
        try:
            url = f"{self.base_url}/banks/{bank_id}/reflect"
            payload = {"query": query}
            res = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if res.status_code == 200:
                return res.json()
            return {}
        except Exception as e:
            logger.error(f"Hindsight reflect failed: {e}")
            return {}

