"""
Feedback storage for product-learning loops.

This uses JSONL so the app can collect real-world corrections without needing
database setup during early startup validation. It can later be migrated to
Postgres or BigQuery with the same event schema.
"""

import json
import os
import time
import uuid
from typing import Dict, Any


FEEDBACK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.jsonl")


class FeedbackStore:
    def __init__(self, path: str = FEEDBACK_PATH):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def record(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "created_at": int(time.time()),
            **payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")
        return event
