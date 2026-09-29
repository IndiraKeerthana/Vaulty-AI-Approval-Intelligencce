import json
import os
import datetime
import logging
from utils.config import DATA_DIR, HINDSIGHT_API_KEY
from memory.hindsight_client import HindsightClient

logger = logging.getLogger("VAULTY.MemoryManager")

class MemoryManager:
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

    def recall(self, query: str, vendor_id: str = None, top_k: int = 3) -> list:
        """
        Recalls conceptually similar cases/lessons based on query, vendor, discrepancy, and context.
        Uses Hindsight if available, otherwise fallback smart conceptual search.
        """
        if self.is_hindsight_active():
            hindsight_memories = self.hindsight.recall(bank_id="vaulty_ap", query=query, top_k=top_k)
            if hindsight_memories:
                return hindsight_memories

        # Fallback Local Recall logic: Conceptual reasoning over stored JSON lessons
        all_lessons = self.get_all_lessons()
        query_terms = set(query.lower().split())
        scored_lessons = []

        for item in all_lessons:
            score = 0
            # Vendor exact match boost
            if vendor_id and item.get("vendor_id") == vendor_id:
                score += 5

            # Textual and conceptual keyword matching
            lesson_text = (item.get("lesson", "") + " " + item.get("topic", "") + " " + item.get("vendor_name", "")).lower()
            for term in query_terms:
                if len(term) > 3 and term in lesson_text:
                    score += 2

            # Boost human corrections and security policies
            if item.get("human_feedback_type") == "HUMAN_CORRECTION":
                score += 3
            if item.get("human_feedback_type") == "SECURITY_POLICY":
                score += 2

            if score > 0:
                scored_lessons.append((score, item))

        scored_lessons.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored_lessons[:top_k]]
        return results

    def retain(self, lesson_content: str, vendor_id: str = "", vendor_name: str = "", topic: str = "", source_case_id: str = "", human_feedback_type: str = "CASE_REFLECTION") -> dict:
        """
        Persists a new reflection/lesson into memory (Hindsight or Fallback).
        """
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

        # Save to Hindsight if available
        if self.is_hindsight_active():
            self.hindsight.retain(
                bank_id="vaulty_ap",
                content=lesson_content,
                metadata=new_lesson
            )

        # Always save to local storage as fallback / backing cache
        all_lessons = self.get_all_lessons()
        all_lessons.insert(0, new_lesson)
        with open(self.lessons_file, "w", encoding="utf-8") as f:
            json.dump(all_lessons, f, indent=2)

        logger.info(f"Retained new lesson {new_lesson['lesson_id']} for {vendor_name} ({human_feedback_type})")
        return new_lesson
