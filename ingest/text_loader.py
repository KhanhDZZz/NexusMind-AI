from pathlib import Path


SUPPORTED = {".txt", ".md"}


def load_texts(folder):
    documents = []

    for path in Path(folder).rglob("*"):
        if path.suffix.lower() not in SUPPORTED:
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        ).strip()

        if not text:
            continue

        documents.append({
            "text": text,
            "source": path.name,
            "page": None,
            "type": "text"
        })

    return documents