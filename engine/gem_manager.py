import os
import yaml

class GemManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.gems_dir = os.path.join(self.base_dir, "gems")
        os.makedirs(self.gems_dir, exist_ok=True)

    def list_gems(self):
        gems = []
        if not os.path.exists(self.gems_dir):
            return gems

        for folder in os.listdir(self.gems_dir):
            folder_path = os.path.join(self.gems_dir, folder)
            if os.path.isdir(folder_path):
                config_path = os.path.join(folder_path, "gem.yaml")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f) or {}
                            data["id"] = folder
                            gems.append(data)
                    except Exception:
                        gems.append({"id": folder, "name": folder, "model": "gemma4:e2b"})
                else:
                    gems.append({"id": folder, "name": folder, "model": "gemma4:e2b"})
        return gems