"""action plan schema. structural anti-liability rules baked in."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

LegalAidAuthority = Literal["NALSA", "SLSA", "DLSA"]


class ApplicationPath(BaseModel):
    online_url: str | None = None
    offline_office: str | None = None
    offline_steps: list[str] = []


class FreeLegalAidContact(BaseModel):
    authority: LegalAidAuthority
    contact_id: str


class SchemeRecommendation(BaseModel):
    scheme_id: str
    rationale_facts: list[str]
    required_documents: list[str]
    application_path: ApplicationPath


class LegalRouteRecommendation(BaseModel):
    framework_id: str
    applicable_situation: str
    forum: str
    procedural_steps: list[str]
    free_legal_aid_contact: FreeLegalAidContact
    required_documents: list[str]
    limitation_period_note: str | None = None


class PlainSummary(BaseModel):
    language: str
    text: str


class ActionPlan(BaseModel):
    schemes: list[SchemeRecommendation] = []
    legal_routes: list[LegalRouteRecommendation] = []
    most_important_next_step: str
    plain_summary: PlainSummary
