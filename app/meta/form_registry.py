import json
import os
from functools import lru_cache

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ERP_META_LAYER", "form_registry.json")


@lru_cache(maxsize=1)
def _load_registry() -> dict:
    path = os.path.abspath(_REGISTRY_PATH)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_form_def(form_name: str) -> dict | None:
    registry = _load_registry()
    return registry.get("forms", {}).get(form_name)


def list_forms() -> list[str]:
    registry = _load_registry()
    return list(registry.get("forms", {}).keys())
