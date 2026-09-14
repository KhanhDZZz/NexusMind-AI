import os
import glob

class KnowledgeManager:
    def __init__(self, gem_id: str = "default_gem"):
        self.gem_id = gem_id
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.kb_dir = os.path.join(self.base_dir, "gems", gem_id, "knowledge")
        os.makedirs(self.kb_dir, exist_ok=True)

    def add_document(self, file_path: str):
        """Thêm file tài liệu vào Knowledge Base của Gem"""
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.kb_dir, filename)
            with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            return True
        return False

    def add_file(self, file_path: str):
        return self.add_document(file_path)

    def ingest(self, file_path: str):
        return self.add_document(file_path)

    def ingest_file(self, file_path: str):
        return self.add_document(file_path)

    def add_texts(self, texts: list, metadatas: list = None):
        """Lưu văn bản trực tiếp vào file txt"""
        for idx, text in enumerate(texts):
            filename = metadatas[idx].get("filename", f"doc_{idx}.txt") if metadatas else f"doc_{idx}.txt"
            dest_path = os.path.join(self.kb_dir, filename)
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(text)

    def list_files(self):
        """Lấy danh sách các file trong kho tri thức"""
        if not os.path.exists(self.kb_dir):
            return []
        files = os.listdir(self.kb_dir)
        return [{"filename": f} for f in files if os.path.isfile(os.path.join(self.kb_dir, f))]

    def get_all_documents(self):
        return self.list_files()