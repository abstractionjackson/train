from __future__ import annotations
from jsonschema import Draft202012Validator, validators
import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_PATH = Path("schema.json")

with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    SCHEMA: Dict[str, Any] = json.load(f)

_validator = Draft202012Validator(SCHEMA)

def validate_instance(instance: Dict[str, Any]) -> None:
    _validator.validate(instance)

# Custom logical validation for displayName membership
class LogicalValidationError(ValueError):
    pass

def logical_validate(instance: Dict[str, Any]) -> None:
    for ex in instance.get("exercises", []):
        aliases = ex.get("aliases") or []
        dn = ex.get("displayName")
        if dn and dn not in aliases:
            raise LogicalValidationError(f"displayName '{dn}' not in aliases for exercise id {ex.get('id')}")
