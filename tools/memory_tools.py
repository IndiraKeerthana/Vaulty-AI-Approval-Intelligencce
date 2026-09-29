import logging
from repositories.memory_repository import get_memory_repository

logger = logging.getLogger("VAULTY.MemoryTools")

def get_similar_resolutions(query: str, vendor_id: str = None) -> list:
    """
    Recalls conceptually relevant historical cases, human corrections, and lessons learned.
    Returns plain-English memories and reflections to inform current investigation.
    """
    memory_repo = get_memory_repository()
    memories = memory_repo.recall(query=query, vendor_id=vendor_id, top_k=3)
    return memories
