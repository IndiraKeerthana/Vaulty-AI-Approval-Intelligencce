import os
import json
import datetime
import logging
from abc import ABC, abstractmethod
from utils.config import DATA_DIR, HINDSIGHT_BANK_ID
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
        human_feedback_type: str = "CASE_REFLECTION",
        metadata: dict = None,
        document_id: str = None,
        tags: list = None
    ) -> dict:
        pass

    @abstractmethod
    def recall(self, query: str, vendor_id: str = None, top_k: int = 3, tags: list = None) -> list:
        pass

    @abstractmethod
    def get_vendor_memory(self, vendor_id: str) -> list:
        pass

    @abstractmethod
    def reflect(self, query: str, context: dict = None, case_id: str = "") -> dict:
        pass

    @abstractmethod
    def get_memory_mode(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class LocalMemoryRepository(AbstractMemoryRepository):
    """Local JSON backing store for Hindsight memory fallback with stable document deduplication."""

    def __init__(self):
        self.lessons_file = os.path.join(DATA_DIR, "lessons.json")

    def is_available(self) -> bool:
        return True

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
        human_feedback_type: str = "CASE_REFLECTION",
        metadata: dict = None,
        document_id: str = None,
        tags: list = None
    ) -> dict:
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

        all_lessons = self._load_lessons()
        updated = False
        for idx, existing in enumerate(all_lessons):
            if existing.get("document_id") == doc_id or (source_case_id and existing.get("source_case_id") == source_case_id):
                all_lessons[idx] = new_lesson
                updated = True
                break

        if not updated:
            all_lessons.insert(0, new_lesson)

        self._save_lessons(all_lessons)
        return new_lesson

    def recall(self, query: str, vendor_id: str = None, top_k: int = 3, tags: list = None) -> list:
        all_lessons = self._load_lessons()
        if not query and not vendor_id and not tags:
            return all_lessons[:top_k]

        query_terms = set(query.lower().split()) if query else set()
        scored_lessons = []

        for item in all_lessons:
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

    def get_vendor_memory(self, vendor_id: str) -> list:
        return self.recall(query=f"vendor {vendor_id}", vendor_id=vendor_id, top_k=10)

    def reflect(self, query: str, context: dict = None, case_id: str = "") -> dict:
        """Local fallback reasoning reflection."""
        ctx = context or {}
        vname = ctx.get("vendor_name") or ctx.get("vendor_id", "Vendor")
        exc = ctx.get("exception_type", "discrepancy")
        recalled = ctx.get("recalled_memories", [])
        evidence = ctx.get("current_evidence", [])
        evidence_str_list = []
        for e in evidence:
            if isinstance(e, str):
                evidence_str_list.append(e)
            elif isinstance(e, dict):
                evidence_str_list.append(json.dumps(e))
        evidence_summary = "; ".join(evidence_str_list[:2]) if evidence_str_list else "primary documents"

        synthesis = (
            f"Vaulty evaluated {len(recalled)} past experiences for {vname} regarding {exc}. "
            f"Prior resolutions emphasized verifying primary evidence records before proceeding. "
            f"Current operational evidence contains: {evidence_summary}."
        )
        guidance = "Memory provides context on prior outcomes; verify current primary documents before final action."
        return {
            "synthesis": synthesis,
            "guidance": guidance,
            "relevant_memory_count": len(recalled)
        }

    def get_memory_mode(self) -> str:
        return "Local mode"


class HindsightMemoryRepository(AbstractMemoryRepository):
    """Hindsight Institutional Memory Service implementation with transparent fallback."""

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
        human_feedback_type: str = "CASE_REFLECTION",
        metadata: dict = None,
        document_id: str = None,
        tags: list = None
    ) -> dict:
        doc_id = document_id or (f"vaulty-case-{source_case_id}" if source_case_id else f"LES-{int(datetime.datetime.now().timestamp())}")
        default_tags = ["source:vaulty", "type:ap_exception"]
        if vendor_id:
            default_tags.append(f"vendor:{vendor_id}")
        if tags:
            default_tags.extend([t for t in tags if t not in default_tags])

        saved_local = self.fallback.remember(
            lesson_content=lesson_content,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            topic=topic,
            source_case_id=source_case_id,
            human_feedback_type=human_feedback_type,
            metadata=metadata,
            document_id=doc_id,
            tags=default_tags
        )

        logger.info(f"[HINDSIGHT] retain case {source_case_id or doc_id}")
        if self.is_available():
            try:
                self.client.retain(
                    bank_id=HINDSIGHT_BANK_ID,
                    content=lesson_content,
                    metadata=saved_local,
                    document_id=doc_id,
                    tags=default_tags
                )
                logger.info(f"[HINDSIGHT] human decision retained for case {source_case_id or doc_id}")
            except Exception as e:
                logger.warning(f"[HINDSIGHT] retain failed (falling back to local memory): {e}")
        else:
            logger.info(f"[HINDSIGHT] human decision retained (via local storage)")

        return saved_local

    def recall(self, query: str, vendor_id: str = None, top_k: int = 3, tags: list = None) -> list:
        logger.info(f"[HINDSIGHT] recall query for case {vendor_id or 'general'}: {query[:100]}")
        if self.is_available():
            try:
                memories = self.client.recall(bank_id=HINDSIGHT_BANK_ID, query=query, top_k=top_k, tags=tags)
                if memories:
                    logger.info(f"[HINDSIGHT] recalled {len(memories)} memories")
                    normalized = []
                    for m in memories:
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
            except Exception as e:
                logger.warning(f"[HINDSIGHT] recall failed: {e}")

        # Fallback to local memory repository
        fb_memories = self.fallback.recall(query=query, vendor_id=vendor_id, top_k=top_k, tags=tags)
        logger.info(f"[HINDSIGHT] recalled {len(fb_memories)} memories (via local fallback)")
        return fb_memories

    def get_vendor_memory(self, vendor_id: str) -> list:
        return self.recall(query=f"vendor {vendor_id}", vendor_id=vendor_id, top_k=10)

    def reflect(self, query: str, context: dict = None, case_id: str = "") -> dict:
        if self.is_available():
            try:
                res = self.client.reflect(bank_id=HINDSIGHT_BANK_ID, query=query, context=context)
                if res:
                    logger.info("[HINDSIGHT] reflection generated")
                    return res
            except Exception as e:
                logger.warning(f"[HINDSIGHT] reflect failed: {e}")

        res = self.fallback.reflect(query=query, context=context, case_id=case_id)
        logger.info("[HINDSIGHT] reflection generated")
        return res

    def get_memory_mode(self) -> str:
        if self.is_available():
            return "Hindsight"
        return "Local mode"


def get_memory_repository() -> AbstractMemoryRepository:
    """Returns the unified memory repository (Hindsight with local fallback)."""
    hs = HindsightMemoryRepository()
    if hs.is_available():
        return hs
    return hs.fallback
