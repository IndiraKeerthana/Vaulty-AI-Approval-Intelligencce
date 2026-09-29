import logging
import datetime
import json
import os
from utils.config import DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VAULTY")

def log_audit_event(case_id: str, agent: str, action: str, details: dict = None):
    audit_file = os.path.join(DATA_DIR, "audit_log.json")
    logs = []
    if os.path.exists(audit_file):
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    event = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "case_id": case_id,
        "agent": agent,
        "action": action,
        "details": details or {}
    }
    logs.insert(0, event)
    try:
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump(logs[:200], f, indent=2)
    except Exception as e:
        logger.error(f"Error saving audit log: {e}")

    logger.info(f"[{case_id}] {agent} -> {action}")
    return event

def get_audit_logs(case_id: str = None):
    audit_file = os.path.join(DATA_DIR, "audit_log.json")
    if not os.path.exists(audit_file):
        return []
    try:
        with open(audit_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
            if case_id:
                return [l for l in logs if l.get("case_id") == case_id]
            return logs
    except Exception:
        return []
