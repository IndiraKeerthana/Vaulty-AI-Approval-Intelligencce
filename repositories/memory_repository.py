import os
import json
import datetime
import logging
from abc import ABC, abstractmethod
from utils.config import DATA_DIR
from memory.hindsight_client import HindsightClient

logger = logging.getLogger("VAULTY.MemoryRepository")

class AbstractMemoryRepository(ABC):
    @abstractmethod
    def remember(
        self,
        lesson_content: str,
        vendor_id: str = "",
        vendor_name: str = "",
        topic: str = "",
        source_case_id: str = "",
        human_feedback_type: str = "CASE_REFLECTION"
    ) -> dict:
        pass

    @abstractmethod
    def recall(self, query: str, vendor_id: str = None, top_k: int = 3) -> list:
        pass

    @abstractmethod
    def get_vendor_memory(self, vendor_id: str) -> list:
        pass

    @abstractmethod
    def reflect(
        self,
        case_id: str,
        human_outcome: str,
        vendor_id: str = "",
        vendor_name: str = "",
        discrepancy_type: str = "",
        agent_recommendation: str = "",
        human_notes: str = ""
    ) -> dict:
        pass

    @abstractmethod
    def get_memory_mode(self) -> str:
        pass


class LocalMemoryRepository(AbstractMemoryRepository):
    """Local JSON backing store for Hindsight memory fallback."""

    def __init__(self):
        self.lessons_file = os.path.join(DATA_DIR, "lessons.json")

    def _load_lessons(self) -> list:
        if not os.path.exists(self.lessons_file):
            return []
        try:
            with open(self.lessons_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading lessons: {e}")
            return []

    def _save_lessons(self, lessons: list):
        try:
            with open(self.lessons_file, "w", encoding="utf-8") as f:
                json.dump(lessons, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving lessons: {e}")

    def remember(
        self,
        lesson_content: str,
        vendor_id: str = "",
        vendor_name: str = "",
        topic: str = "",
        source_case_id: str = "",
        human_feedback_type: str = "CASE_REFLECTION"
    ) -> dict:
        new_lesson = {
            "lesson_id": f"LES-{int(datetime.datetime.now().timestamp())}",
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "topic": topic or "General AP Exception Lesson",
            "lesson": lesson_content,
            "source_case_id": source_case_id,
            "human_feedback_type": human_feedback_type,
            "confidence_score": 0.95,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        all_lessons = self._load_lessons()
        all_lessons.insert(0, new_lesson)
        self._save_lessons(all_lessons)
        return new_lesson

    def recall(self, query: str, vendor_id: str = None, top_k: int = 3) -> list:
        all_lessons = self._load_lessons()
        if not query and not vendor_id:
            return all_lessons[:top_k]

        query_terms = set(query.lower().split()) if query else set()
        scored_lessons = []

        for item in all_lessons:
            if vendor_id and item.get("vendor_id") != vendor_id:
                continue

            match_score = 0
            if vendor_id and item.get("vendor_id") == vendor_id:
                match_score += 5

            lesson_text = (item.get("lesson", "") + " " + item.get("topic", "") + " " + item.get("vendor_name", "")).lower()
            query_matched = False
            for term in query_terms:
                if len(term) > 3 and term in lesson_text:
                    match_score += 2
                    query_matched = True

            if query_terms and not query_matched and not (vendor_id and item.get("vendor_id") == vendor_id):
                continue

            score = match_score
            if item.get("human_feedback_type") == "HUMAN_CORRECTION":
                score += 3
            elif item.get("human_feedback_type") == "SECURITY_POLICY":
                score += 2

            if score > 0:
                scored_lessons.append((score, item))

        scored_lessons.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored_lessons[:top_k]]
        return results

    def get_vendor_memory(self, vendor_id: str) -> list:
        return self.recall(query="", vendor_id=vendor_id, top_k=10)

    def reflect(
        self,
        case_id: str,
        human_outcome: str,
        vendor_id: str = "",
        vendor_name: str = "",
        discrepancy_type: str = "",
        agent_recommendation: str = "",
        human_notes: str = ""
    ) -> dict:
        topic = f"Lesson on {vendor_name} ({discrepancy_type})"
        if human_outcome == "CORRECTED":
            lesson_text = (
                f"HUMAN CORRECTION LESSON for {vendor_name}: On case {case_id}, agent recommended '{agent_recommendation}', "
                f"but human supervisor CORRECTED it with notes: '{human_notes}'. Future investigations must verify physical goods "
                f"receipts and explicit approval before recommending resolution."
            )
            feedback_type = "HUMAN_CORRECTION"
        elif human_outcome == "APPROVED":
            lesson_text = (
                f"CONFIRMED RESOLUTION LESSON for {vendor_name}: Payment approval on case {case_id} confirmed that "
                f"line-item verification and amendment validation was accurate. Retain this evidence-checking pattern."
            )
            feedback_type = "HUMAN_APPROVAL"
        else:
            lesson_text = (
                f"REJECTED CASE REFLECTION for {vendor_name}: Human supervisor rejected recommendation '{agent_recommendation}' "
                f"on case {case_id} ({human_notes}). Future cases must check for updated contract clauses."
            )
            feedback_type = "HUMAN_REJECTION"

        saved_memory = self.remember(
            lesson_content=lesson_text,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            topic=topic,
            source_case_id=case_id,
            human_feedback_type=feedback_type
        )
        return {
            "case_id": case_id,
            "human_outcome": human_outcome,
            "topic": topic,
            "lesson": lesson_text,
            "saved_memory": saved_memory,
            "memory_mode": self.get_memory_mode()
        }

    def get_memory_mode(self) -> str:
        return "Local mode"


class HindsightMemoryRepository(AbstractMemoryRepository):
    """Hindsight Institutional Memory Service implementation."""

    def __init__(self, fallback_repo: LocalMemoryRepository = None):
        self.client = HindsightClient()
        self.fallback = fallback_repo or LocalMemoryRepository()

    def is_available(self) -> bool:
        return self.client.is_available()

    def remember(
        self,
        lesson_content: str,
        vendor_id: str = "",
        vendor_name: str = "",
        topic: str = "",
        source_case_id: str = "",
        human_feedback_type: str = "CASE_REFLECTION"
    ) -> dict:
        saved_local = self.fallback.remember(
            lesson_content=lesson_content,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            topic=topic,
            source_case_id=source_case_id,
            human_feedback_type=human_feedback_type
        )
        if self.is_available():
            try:
                self.client.retain(
                    bank_id="vaulty_ap",
                    content=lesson_content,
                    metadata=saved_local
                )
            except Exception as e:
                logger.warning(f"Hindsight retain failed: {e}")
        return saved_local

    def recall(self, query: str, vendor_id: str = None, top_k: int = 3) -> list:
        if self.is_available():
            try:
                memories = self.client.recall(bank_id="vaulty_ap", query=query, top_k=top_k)
                if memories:
                    return memories
            except Exception as e:
                logger.warning(f"Hindsight recall failed: {e}")
        return self.fallback.recall(query=query, vendor_id=vendor_id, top_k=top_k)

    def get_vendor_memory(self, vendor_id: str) -> list:
        return self.recall(query=f"vendor {vendor_id}", vendor_id=vendor_id, top_k=10)

    def reflect(
        self,
        case_id: str,
        human_outcome: str,
        vendor_id: str = "",
        vendor_name: str = "",
        discrepancy_type: str = "",
        agent_recommendation: str = "",
        human_notes: str = ""
    ) -> dict:
        return self.fallback.reflect(
            case_id=case_id,
            human_outcome=human_outcome,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            discrepancy_type=discrepancy_type,
            agent_recommendation=agent_recommendation,
            human_notes=human_notes
        )

    def get_memory_mode(self) -> str:
        if self.is_available():
            return "Hindsight"
        return "Local Development Fallback"


def get_memory_repository() -> AbstractMemoryRepository:
    """Selects active MemoryRepository implementation based on Hindsight availability."""
    hs = HindsightMemoryRepository()
    if hs.is_available():
        return hs
    return hs.fallback
