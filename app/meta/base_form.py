import json
from typing import Any
from app.meta.form_registry import get_form_def


class MetaForm:
    def __init__(self, form_name: str, data: dict | None = None):
        self.defn = get_form_def(form_name)
        if not self.defn:
            raise ValueError(f"Unknown form: {form_name}")
        self.form_name = form_name
        self.data = data or {}

    @property
    def title(self) -> str:
        return self.defn.get("title", self.form_name)

    @property
    def sections(self) -> list:
        return self.defn.get("sections", [{"id": "main", "title": self.title}])

    @property
    def fields(self) -> list:
        return self.defn.get("fields", [])

    @property
    def endpoints(self) -> dict:
        return self.defn.get("endpoints", {})

    @property
    def auto_calc_rules(self) -> list:
        return self.defn.get("autoCalcRules", [])

    def fields_by_section(self, section_id: str) -> list:
        return [f for f in self.fields if f.get("section", "main") == section_id]

    def get_field(self, name: str) -> dict | None:
        for f in self.fields:
            if f["name"] == name:
                return f
        return None

    def is_readonly(self, field_name: str) -> bool:
        field = self.get_field(field_name)
        return field.get("readonly", False) if field else False

    def render_context(self) -> dict:
        sections = []
        for sec in self.sections:
            sec_id = sec["id"]
            sections.append({
                "id": sec_id,
                "title": sec["title"],
                "fields": self.fields_by_section(sec_id),
            })
        return {
            "form_name": self.form_name,
            "title": self.title,
            "sections": sections,
            "all_fields": self.fields,
            "data": self.data,
            "endpoints": self.endpoints,
            "auto_calc_rules": json.dumps(self.auto_calc_rules),
        }
