import requests
import json
import logging
from utils.config import HINDSIGHT_API_KEY, HINDSIGHT_BANK_ID, HINDSIGHT_API_URL

logger = logging.getLogger("VAULTY.HindsightClient")

class HindsightClient:
    def __init__(self, api_key: str = None, base_url: str = None, bank_id: str = None):
        self.api_key = api_key or HINDSIGHT_API_KEY
        self.base_url = (base_url or HINDSIGHT_API_URL).rstrip("/")
        self.bank_id = bank_id or HINDSIGHT_BANK_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._availability_cache = None

    def is_available(self) -> bool:
        """Checks if Hindsight API is reachable and authorized. Never logs API keys."""
        if not self.api_key:
            return False
        if self._availability_cache is not None:
            return self._availability_cache
        try:
            res = requests.get(f"{self.base_url}/health", headers=self.headers, timeout=1.5)
            self._availability_cache = (res.status_code == 200)
            return self._availability_cache
        except Exception:
            self._availability_cache = False
            return False

    def retain(
        self,
        bank_id: str = None,
        content: str = "",
        metadata: dict = None,
        document_id: str = None,
        tags: list = None
    ) -> bool:
        """
        Stores an experience in the Hindsight memory bank.
        Uses stable document_id to avoid duplicate memories.
        """
        b_id = bank_id or self.bank_id
        cid = (metadata or {}).get("case_id") or document_id or "case"
        if not self.is_available():
            logger.info(f"[HINDSIGHT] retain skipped (service unavailable) for {cid}")
            return False
        try:
            url = f"{self.base_url}/banks/{b_id}/memories"
            payload = {
                "content": content,
                "metadata": metadata or {},
                "document_id": document_id,
                "tags": tags or []
            }
            logger.info(f"[HINDSIGHT] retain case {cid}")
            res = requests.post(url, headers=self.headers, json=payload, timeout=4)
            if res.status_code in (200, 201):
                logger.info(f"[HINDSIGHT] human decision retained for case {cid}")
                return True
            logger.warning(f"[HINDSIGHT] retain failed with status code {res.status_code}")
            return False
        except Exception as e:
            logger.error(f"[HINDSIGHT] retain error: {e}")
            return False

    def recall(
        self,
        bank_id: str = None,
        query: str = "",
        top_k: int = 3,
        tags: list = None
    ) -> list:
        """
        Recalls conceptually relevant memories from the Hindsight memory bank.
        """
        b_id = bank_id or self.bank_id
        if not self.is_available():
            logger.info(f"[HINDSIGHT] recall skipped (service unavailable)")
            return []
        try:
            logger.info(f"[HINDSIGHT] recall query: {query[:100]}")
            url = f"{self.base_url}/banks/{b_id}/recall"
            payload = {"query": query, "top_k": top_k}
            if tags:
                payload["tags"] = tags
            res = requests.post(url, headers=self.headers, json=payload, timeout=4)
            if res.status_code == 200:
                data = res.json()
                memories = data.get("memories", [])
                logger.info(f"[HINDSIGHT] recalled {len(memories)} memories")
                return memories
            logger.warning(f"[HINDSIGHT] recall failed with status {res.status_code}")
            return []
        except Exception as e:
            logger.error(f"[HINDSIGHT] recall error: {e}")
            return []

    def reflect(
        self,
        bank_id: str = None,
        query: str = "",
        context: dict = None
    ) -> dict:
        """
        Reflects across the Hindsight memory bank to synthesize higher-level reasoning.
        """
        b_id = bank_id or self.bank_id
        if not self.is_available():
            logger.info("[HINDSIGHT] reflect skipped (service unavailable)")
            return {}
        try:
            logger.info(f"[HINDSIGHT] reflect query: {query[:100]}")
            url = f"{self.base_url}/banks/{b_id}/reflect"
            payload = {"query": query, "context": context or {}}
            res = requests.post(url, headers=self.headers, json=payload, timeout=5)
            if res.status_code == 200:
                logger.info("[HINDSIGHT] reflection generated")
                return res.json()
            logger.warning(f"[HINDSIGHT] reflect failed with status {res.status_code}")
            return {}
        except Exception as e:
            logger.error(f"[HINDSIGHT] reflect error: {e}")
            return {}
