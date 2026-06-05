import json
import os
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session


class ModelRegistry:
    def __init__(self, db: Session | None = None, storage_path: str | None = None):
        self.db = db
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "models", "neural_models"
        )
        os.makedirs(self.storage_path, exist_ok=True)

    def save_model(self, organ: str, cell: str, version: str, model_data: dict) -> dict:
        filename = f"{organ}_{cell}_v{version}.json"
        filepath = os.path.join(self.storage_path, filename)
        record = {
            "organ": organ,
            "cell": cell,
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metrics": model_data.get("metrics", {}),
            "feature_count": model_data.get("feature_count", 0),
            "training_samples": model_data.get("training_samples", 0),
            "filepath": filepath,
        }
        with open(filepath, "w") as f:
            json.dump(model_data.get("serialized", {}), f)
        metadata_path = filepath.replace(".json", "_meta.json")
        with open(metadata_path, "w") as f:
            json.dump(record, f, indent=2)
        return record

    def load_model(self, organ: str, cell: str, version: str | None = None) -> dict | None:
        if version:
            filename = f"{organ}_{cell}_v{version}.json"
        else:
            versions = self.list_versions(organ, cell)
            if not versions:
                return None
            filename = f"{organ}_{cell}_v{versions[-1]['version']}.json"
        filepath = os.path.join(self.storage_path, filename)
        if not os.path.exists(filepath):
            return None
        with open(filepath) as f:
            return json.load(f)

    def list_versions(self, organ: str, cell: str) -> list[dict]:
        import glob
        pattern = os.path.join(self.storage_path, f"{organ}_{cell}_v*_meta.json")
        files = sorted(glob.glob(pattern))
        versions = []
        for fpath in files:
            with open(fpath) as f:
                versions.append(json.load(f))
        return versions

    def cleanup_old_versions(self, organ: str, cell: str, keep_last: int = 3) -> int:
        versions = self.list_versions(organ, cell)
        if len(versions) <= keep_last:
            return 0
        versions.sort(key=lambda v: v["created_at"])
        removed = 0
        for v in versions[:-keep_last]:
            for ext in [".json", "_meta.json"]:
                fpath = v["filepath"].replace(".json", ext)
                if os.path.exists(fpath):
                    os.remove(fpath)
                    removed += 1
        return removed

    def get_registry_summary(self) -> dict:
        import glob
        meta_files = glob.glob(os.path.join(self.storage_path, "*_meta.json"))
        models = []
        for fpath in meta_files:
            with open(fpath) as f:
                models.append(json.load(f))
        summary = {
            "total_models": len(models),
            "models": models,
            "storage_path": self.storage_path,
        }
        return summary
