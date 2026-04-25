"""advisor action schema. shared seam — both tracks import."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from nyaya_mitra.interface.plan import ActionPlan

Language = Literal["en", "hi", "hinglish"]
Literacy = Literal["low", "medium", "high"]
SensitiveTopic = Literal[
    "caste",
    "dv",
    "disability",
    "immigration",
    "hiv_status",
    "sexual_orientation",
    "mental_health",
]


class Ask(BaseModel):
    type: Literal["ASK"] = "ASK"
    question: str
    language: Language


class Probe(BaseModel):
    type: Literal["PROBE"] = "PROBE"
    question: str
    sensitive_topic: SensitiveTopic
    language: Language


class Explain(BaseModel):
    type: Literal["EXPLAIN"] = "EXPLAIN"
    content: str
    target_literacy: Literacy
    language: Language


class Finalize(BaseModel):
    type: Literal["FINALIZE"] = "FINALIZE"
    plan: ActionPlan


AdvisorAction = Annotated[
    Ask | Probe | Explain | Finalize,
    Field(discriminator="type"),
]
