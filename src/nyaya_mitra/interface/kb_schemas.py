"""json-schema definitions for kb files. track A owns content; both validate against these."""

from __future__ import annotations

from typing import Any

SCHEME_CATEGORIES = (
    "agriculture_rural",
    "women_child",
    "education",
    "health",
    "labor_livelihood",
)

FRAMEWORK_CATEGORIES = (
    "labor",
    "women_protection",
    "tenancy_property",
    "consumer",
    "police_procedure",
    "civil_rights",
)

LEGAL_AID_AUTHORITIES = ("NALSA", "SLSA", "DLSA")

_BILINGUAL = {
    "type": "object",
    "required": ["en", "hi"],
    "properties": {
        "en": {"type": "string"},
        "hi": {"type": "string"},
    },
}

_SOURCE = {
    "type": "object",
    "required": ["url", "verified_on"],
    "properties": {
        "url": {"type": "string"},
        "verified_on": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
    },
}

SCHEME_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "scheme_id",
        "name",
        "category",
        "ministry",
        "benefit",
        "eligibility_rules_human",
        "required_documents",
        "application_paths",
        "source",
    ],
    "properties": {
        "scheme_id": {"type": "string", "pattern": r"^[a-z][a-z0-9_]*$"},
        "name": _BILINGUAL,
        "category": {"enum": list(SCHEME_CATEGORIES)},
        "ministry": {"type": "string"},
        "benefit": _BILINGUAL,
        "eligibility_rules_human": {"type": "string"},
        "required_documents": {"type": "array", "items": {"type": "string"}},
        "application_paths": {
            "type": "object",
            "required": ["online_url", "offline_office_pattern", "offline_steps"],
            "properties": {
                "online_url": {"type": ["string", "null"]},
                "offline_office_pattern": {"type": ["string", "null"]},
                "offline_steps": {"type": "array", "items": {"type": "string"}},
            },
        },
        "source": _SOURCE,
    },
}

FRAMEWORK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "framework_id",
        "name",
        "category",
        "applicable_situations",
        "forum",
        "procedural_steps",
        "required_documents",
        "legal_aid_authority",
        "source",
    ],
    "properties": {
        "framework_id": {"type": "string", "pattern": r"^[a-z][a-z0-9_]*$"},
        "name": _BILINGUAL,
        "category": {"enum": list(FRAMEWORK_CATEGORIES)},
        "applicable_situations": {"type": "array", "items": {"type": "string"}},
        "forum": {"type": "string"},
        "limitation_period_note": {"type": ["string", "null"]},
        "procedural_steps": {"type": "array", "items": {"type": "string"}},
        "required_documents": {"type": "array", "items": {"type": "string"}},
        "legal_aid_authority": {"enum": list(LEGAL_AID_AUTHORITIES)},
        "source": _SOURCE,
    },
}

DLSA_DIRECTORY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["NALSA", "SLSAs", "DLSAs", "qualifying_categories"],
    "properties": {
        "NALSA": {"type": "object", "required": ["contact_id"]},
        "SLSAs": {"type": "object"},
        "DLSAs": {"type": "object"},
        "qualifying_categories": {"type": "array", "items": {"type": "string"}},
    },
}
