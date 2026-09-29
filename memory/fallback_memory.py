import json
import os
import datetime
import logging
from utils.config import DATA_DIR, HINDSIGHT_BANK_ID
from memory.hindsight_client import HindsightClient

logger = logging.getLogger("VAULTY.MemoryManager")

class MemoryManager:
    """
    Manages institutional memory lifecycle.
    Uses Hindsight as primary provider when available and reachable;
    transparently maintains local JSON storage as backing fallback.
    """

    def __init__(self):
        self.hindsight = HindsightClient()
        self.lessons_file = os.path.join(DATA_DIR, "lessons.json")

    def get_memory_mode(self) -> str:
        if self.hindsight.is_available():
            return "Hindsight"
        return "Local Development Fallback"

    def is_hindsight_active(self) -> bool:
        return self.hindsight.is_available()

    def get_all_lessons(self) -> list:
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

    def recall(self, query: str, vendor_id: str = None, top_k: int = 3, tags: list = None) -> list:
        """
        Recalls conceptually similar cases/lessons based on query, vendor, and tags.
        Uses Hindsight if available; otherwise uses local conceptual scoring.
        """
        if self.is_hindsight_active():
            hindsight_memories = self.hindsight.recall(
                bank_id=HINDSIGHT_BANK_ID,
                query=query,
                top_k=top_k,
                tags=tags
            )
            if hindsight_memories:
                normalized = []
                for m in hindsight_memories:
                    if isinstance(m, dict):
                        m["source"] = "hindsight"
                        normalized.append(m)
                    elif isinstance(m, str):
                        normalized.append({
                            "text": m,
                            "lesson": m,
                            "source": "hindsight",
                            "confidence_score": 0.95
                        })
                return normalized

        # Fallback Local Recall logic: Conceptual reasoning over stored JSON lessons
        all_lessons = self.get_all_lessons()
        query_terms = set(query.lower().split()) if query else set()
        scored_lessons = []

        for item in all_lessons:
            if vendor_id and item.get("vendor_id") != vendor_id:
                # Still allow matching if general AP principle or high query match
                pass

            match_score = 0
            if vendor_id and item.get("vendor_id") == vendor_id:
                match_score += 5

            lesson_text = (
                item.get("lesson", "") + " " +
                item.get("topic", "") + " " +
                item.get("vendor_name", "") + " " +
                item.get("source_case_id", "")
            ).lower()

            query_matched = False
            for term in query_terms:
                if len(term) > 3 and term in lesson_text:
                    match_score += 2
                    query_matched = True

            # If specific tags match
            if tags and item.get("tags"):
                for t in tags:
                    if t in item.get("tags", []):
                        match_score += 3
                        query_matched = True

            if query_terms and not query_matched and not (vendor_id and item.get("vendor_id") == vendor_id):
                continue

            score = match_score
            if item.get("human_feedback_type") in ("HUMAN_CORRECTION", "CORRECTED"):
                score += 3
            elif item.get("human_feedback_type") in ("HUMAN_APPROVAL", "APPROVED"):
                score += 2

            if score > 0:
                item_copy = dict(item)
                item_copy["source"] = "local_fallback"
                item_copy["text"] = item_copy.get("lesson", "")
                scored_lessons.append((score, item_copy))

        scored_lessons.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored_lessons[:top_k]]
        return results

    def retain(
        self,
        lesson_content: str,
        vendor_id: str = "",
        vendor_name: str = "",
        topic: str = "",
        source_case_id: str = "",
        human_feedback_type: str = "CASE_REFLECTION",
        document_id: str = None,
        tags: list = None,
        metadata: dict = None
    ) -> dict:
        """
        Persists a complete business experience into memory with stable document_id deduplication.
        """
        doc_id = document_id or (f"vaulty-case-{source_case_id}" if source_case_id else f"LES-{int(datetime.datetime.now().timestamp())}")
        default_tags = ["source:vaulty", "type:ap_exception"]
        if vendor_id:
            default_tags.append(f"vendor:{vendor_id}")
        if tags:
            default_tags.extend([t for t in tags if t not in default_tags])

        new_lesson = {
            "lesson_id": doc_id,
            "document_id": doc_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "topic": topic or f"AP Experience for {vendor_name or vendor_id}",
            "lesson": lesson_content,
            "text": lesson_content,
            "source_case_id": source_case_id,
            "human_feedback_type": human_feedback_type,
            "tags": default_tags,
            "metadata": metadata or {},
            "confidence_score": 0.95,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Save to Hindsight if available
        if self.is_hindsight_active():
            self.hindsight.retain(
                bank_id=HINDSIGHT_BANK_ID,
                content=lesson_content,
                metadata=new_lesson,
                document_id=doc_id,
                tags=default_tags
            )

        # Stable document_id deduplication in local storage
        all_lessons = self.get_all_lessons()
        updated = False
        for idx, existing in enumerate(all_lessons):
            if existing.get("document_id") == doc_id or (source_case_id and existing.get("source_case_id") == source_case_id):
                all_lessons[idx] = new_lesson
                updated = True
                break

        if not updated:
            all_lessons.insert(0, new_lesson)

        self._save_lessons(all_lessons)
        logger.info(f"Retained lesson {doc_id} for {vendor_name} ({human_feedback_type})")
        return new_lesson
