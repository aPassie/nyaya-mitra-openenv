"""http client for the nyaya mitra env. only allowed cross-track import for track b."""

from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel

from nyaya_mitra.interface import AdvisorAction, CitizenObservation

DEFAULT_URL = os.environ.get("NYAYA_ENV_URL", "http://localhost:8000")


class StepResultDTO(BaseModel):
    observation: CitizenObservation | None
    reward: float
    done: bool
    info: dict[str, Any]


class NyayaMitraClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = 30.0) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=timeout)

    def reset(self, seed: int = 0, difficulty: str | None = None) -> CitizenObservation:
        r = self._http.post("/reset", json={"seed": seed, "difficulty": difficulty})
        r.raise_for_status()
        return CitizenObservation.model_validate(r.json())

    def step(self, action: AdvisorAction) -> StepResultDTO:
        r = self._http.post("/step", json=action.model_dump())
        r.raise_for_status()
        return StepResultDTO.model_validate(r.json())

    def close(self) -> None:
        try:
            self._http.post("/close")
        finally:
            self._http.close()
