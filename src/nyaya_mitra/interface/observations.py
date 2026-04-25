"""citizen observation schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CitizenObservation(BaseModel):
    citizen_utterance: str
    language: Literal["en", "hi", "hinglish"]
    turn: int
    max_turns: int
    elicited_facts: list[str]
    facts_revealed_this_turn: list[str]
