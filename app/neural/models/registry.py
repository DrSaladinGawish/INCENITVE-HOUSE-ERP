import json
import os
import pickle


class ModelRegistry:
    def __init__(self, storage_dir="data/models"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _path(self, name):
        return os.path.join(self.storage_dir, f"{name}.pkl")

    def _meta_path(self, name):
        return os.path.join(self.storage_dir, f"{name}.json")

    def save(self, name, model_obj, metadata=None):
        with open(self._path(name), "wb") as f:
            pickle.dump(model_obj, f)
        if metadata:
            with open(self._meta_path(name), "w") as f:
                json.dump(metadata, f)

    def load(self, name):
        path = self._path(name)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return pickle.load(f)

    def list_models(self):
        models = []
        for f in os.listdir(self.storage_dir):
            if f.endswith(".pkl"):
                name = f[:-4]
                meta = {}
                meta_path = self._meta_path(name)
                if os.path.exists(meta_path):
                    with open(meta_path) as mf:
                        meta = json.load(mf)
                models.append({"name": name, **meta})
        return models
