"""citizen profile schema. track A authors content; this defines the shape."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

TrustLevel = Literal["wary", "neutral", "open"]
Verbosity = Literal["low", "med", "high"]
Language = Literal["en", "hi", "hinglish"]
Literacy = Literal["low", "medium", "high"]


class Behavior(BaseModel):
    trust_level: TrustLevel
    verbosity: Verbosity
    language_preference: Language
    literacy: Literacy
    initial_vague_query: str


class SituationSpecific(BaseModel):
    presenting_issue: str
    hidden_facts: dict[str, Any] = Field(default_factory=dict)
    sensitive_facts: dict[str, Any] = Field(default_factory=dict)


class DerivedGroundTruth(BaseModel):
    eligible_schemes: list[str] = []
    applicable_frameworks: list[str] = []


class CitizenProfile(BaseModel):
    seed: int
    demographics: dict[str, Any] = Field(default_factory=dict)
    economic: dict[str, Any] = Field(default_factory=dict)
    family: dict[str, Any] = Field(default_factory=dict)
    situation_specific: SituationSpecific
    behavior: Behavior
    derived_ground_truth: DerivedGroundTruth = Field(default_factory=DerivedGroundTruth)
