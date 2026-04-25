"""json-schema validators for kb files."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError, validate

from nyaya_mitra.interface import (
    DLSA_DIRECTORY_SCHEMA,
    FRAMEWORK_SCHEMA,
    SCHEME_SCHEMA,
)
from nyaya_mitra.knowledge.loader import DATA_ROOT


def validate_kb(data_root: Path = DATA_ROOT) -> list[str]:
    errors: list[str] = []
    for f in sorted((data_root / "schemes").glob("*.json")):
        try:
            validate(instance=json.loads(f.read_text(encoding="utf-8")), schema=SCHEME_SCHEMA)
        except (ValidationError, json.JSONDecodeError) as e:
            errors.append(f"{f.name}: {e}")
    for f in sorted((data_root / "frameworks").glob("*.json")):
        try:
            validate(instance=json.loads(f.read_text(encoding="utf-8")), schema=FRAMEWORK_SCHEMA)
        except (ValidationError, json.JSONDecodeError) as e:
            errors.append(f"{f.name}: {e}")
    dlsa_path = data_root / "dlsa_directory.json"
    if dlsa_path.exists():
        try:
            validate(
                instance=json.loads(dlsa_path.read_text(encoding="utf-8")),
                schema=DLSA_DIRECTORY_SCHEMA,
            )
        except (ValidationError, json.JSONDecodeError) as e:
            errors.append(f"dlsa_directory.json: {e}")
    return errors
