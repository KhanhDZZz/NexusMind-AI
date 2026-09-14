import json
from pathlib import Path


MEMORY_DIR = Path(r"D:\GemmaTraining\gems\technical_gem\memory")
HISTORY_FILE = MEMORY_DIR / "conversation.json"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history():
    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )