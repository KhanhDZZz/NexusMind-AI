import os
import yaml
import ollama

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Gem:
    def __init__(self, gem_id: str = "default_gem"):
        self.gem_id = gem_id
        self.model = "gemma4:e2b"  # Model mặc định
        self.instructions = ""
        self._load_config()

    def _load_config(self):
        """Đọc file cấu hình gem.yaml của Gem tương ứng nếu có"""
        config_path = os.path.join(BASE_DIR, "gems", self.gem_id, "gem.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if config:
                        self.model = config.get("model", self.model)
                        self.instructions = config.get("instructions", "")
            except Exception as e:
                print(f"Lỗi đọc config Gem '{self.gem_id}': {e}")

    def ask(self, message: str, custom_system_instruction: str = "") -> str:
        """Gửi yêu cầu tới Ollama với cửa sổ ngữ cảnh mở rộng (num_ctx=8192)"""
        system_content = custom_system_instruction if custom_system_instruction else self.instructions

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": message}
                ],
                options={
                    "num_ctx": 8192,      # Mở rộng cửa sổ ngữ cảnh lên 8,192 tokens
                    "temperature": 0.7,   # Giữ độ sáng tạo vừa phải để bám sát KB
                    "top_p": 0.9
                }
            )
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Lỗi khi gọi mô hình Ollama ({self.model}): {str(e)}")