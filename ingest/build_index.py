from pathlib import Path
import chromadb
import ollama

from pdf_loader import load_pdfs
from text_loader import load_texts

BASE = Path(r"D:\GemmaTraining")

KNOWLEDGE = BASE / "gems" / "technical_gem" / "knowledge"

DB_PATH = BASE / "database" / "chroma"

EMBED_MODEL = "embeddinggemma:latest"


def chunk_text(text, chunk_size=1200, overlap=200):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

def main():

    print("Loading documents...")

    pdf_docs = load_pdfs(KNOWLEDGE / "pdf")
    text_docs = load_texts(KNOWLEDGE / "text")

    documents = pdf_docs + text_docs

    print(f"Loaded documents: {len(documents)}")

    chunks = []

    for doc in documents:

        parts = chunk_text(doc["text"])

        for index, part in enumerate(parts):

            chunks.append({
                "text": part,
                "source": doc["source"],
                "page": doc["page"],
                "type": doc["type"],
                "chunk": index
            })

    print(f"Total chunks: {len(chunks)}")

    client = chromadb.PersistentClient(
        path=str(DB_PATH)
    )

    collection = client.get_or_create_collection(
        name="technical_gem"
    )

    # Xóa index cũ để build lại sạch
    try:
        client.delete_collection("technical_gem")
    except Exception:
        pass

    collection = client.create_collection(
        name="technical_gem"
    )

    batch_size = 4

    for i in range(0, len(chunks), batch_size):

        batch = chunks[i:i + batch_size]

        texts = [x["text"] for x in batch]

        print(
            f"Embedding {i + 1} - "
            f"{min(i + batch_size, len(chunks))}"
        )

        result = ollama.embed(
            model=EMBED_MODEL,
            input=texts
        )

        embeddings = result["embeddings"]

        ids = [
            f"chunk_{i + j}"
            for j in range(len(batch))
        ]

        metadatas = [
            {
                "source": x["source"],
                "page": x["page"] or 0,
                "type": x["type"],
                "chunk": x["chunk"]
            }
            for x in batch
        ]

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

    print()
    print("================================")
    print("KNOWLEDGE BASE READY")
    print("================================")


if __name__ == "__main__":
    main()