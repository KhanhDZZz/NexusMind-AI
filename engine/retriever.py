from pathlib import Path
import chromadb
import ollama


BASE = Path(r"D:\GemmaTraining")
DB_PATH = BASE / "database" / "chroma"

EMBED_MODEL = "embeddinggemma:latest"


class Retriever:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(DB_PATH)
        )

        self.collection = self.client.get_collection(
            name="technical_gem"
        )

    def search(self, query, top_k=6):

        result = ollama.embed(
            model=EMBED_MODEL,
            input=query
        )

        query_embedding = result["embeddings"][0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        output = []

        if not results["documents"]:
            return output

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for i in range(len(documents)):

            output.append({
                "text": documents[i],
                "metadata": metadatas[i],
                "distance": distances[i]
            })

        return output