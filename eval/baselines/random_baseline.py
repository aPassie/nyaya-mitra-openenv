"""random advisor: picks actions uniformly at random and finalizes with a
random plan. acts as the ABSOLUTE FLOOR for the eval — every other baseline
must beat this, otherwise we don't have a learnable signal.

NOT a learned policy; deterministic per (seed, turn) so the random baseline
itself is reproducible.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from nyaya_mitra.interface import (
    ActionPlan,
    ApplicationPath,
    Ask,
    Explain,
    Finalize,
    FreeLegalAidContact,
    LegalRouteRecommendation,
    PlainSummary,
    Probe,
    SchemeRecommendation,
)

KNOWN_SCHEMES = ["pm_kisan", "pmuy", "ayushman_bharat", "mgnrega", "pm_awas_grameen", "pmsby"]
KNOWN_FRAMEWORKS = [
    "domestic_violence_act_2005",
    "consumer_protection_act_2019",
    "maternity_benefit_act_1961",
    "minimum_wages_act_1948",
]
KNOWN_CONTACTS = [
    ("DLSA", "dlsa_ludhiana"),
    ("DLSA", "dlsa_muzaffarpur"),
    ("DLSA", "dlsa_lucknow"),
    ("NALSA", "nalsa_central"),
]
TOPICS = ["caste", "dv", "disability", "immigration", "hiv_status", "sexual_orientation", "mental_health"]


def _random_plan(rng: random.Random) -> ActionPlan:
    """build a random plan that satisfies the schema (so format gate doesn't fire).
    plans are deliberately shallow but valid."""
    n_schemes = rng.randint(0, 2)
    n_legal = rng.randint(1, 2)  # at least 1 so plan is non-empty

    schemes = []
    for _ in range(n_schemes):
        sid = rng.choice(KNOWN_SCHEMES)
        schemes.append(
            SchemeRecommendation(
                scheme_id=sid,
                rationale_facts=[],
                required_documents=["Aadhaar"],
                application_path=ApplicationPath(),
            )
        )

    legal_routes = []
    for _ in range(n_legal):
        fid = rng.choice(KNOWN_FRAMEWORKS)
        auth, cid = rng.choice(KNOWN_CONTACTS)
        legal_routes.append(
            LegalRouteRecommendation(
                framework_id=fid,
                applicable_situation="random",
                forum="appropriate forum",
                procedural_steps=["file a written complaint"],
                free_legal_aid_contact=FreeLegalAidContact(
                    authority=auth,  # type: ignore[arg-type]
                    contact_id=cid,
                ),
                required_documents=["Identity proof"],
            )
        )

    return ActionPlan(
        schemes=schemes,
        legal_routes=legal_routes,
        most_important_next_step="random next step",
        plain_summary=PlainSummary(language="en", text="random plan"),
    )


def build_random_baseline(*, seed: int = 42, finalize_at: int = 3) -> Callable[..., Any]:
    """random advisor. seed makes results reproducible.

    on each call rolls one of {ASK, PROBE, EXPLAIN, FINALIZE}. once turn_index
    crosses finalize_at, always FINALIZE so we don't truncate. this gives the
    scripted baseline a fair fight (both finalize ~turn 3-5).
    """

    def advisor(observation, state):
        rng = random.Random((seed * 9973 + state.turn_index * 31) & 0xFFFFFFFF)
        if state.turn_index >= finalize_at:
            return Finalize(plan=_random_plan(rng))

        choice = rng.random()
        if choice < 0.4:
            return Ask(question="random question", language="en")
        if choice < 0.7:
            return Probe(
                question="random probe",
                sensitive_topic=rng.choice(TOPICS),  # type: ignore[arg-type]
                language="en",
            )
        if choice < 0.9:
            return Explain(
                content="random explanation",
                target_literacy=rng.choice(["low", "medium", "high"]),  # type: ignore[arg-type]
                language="en",
            )
        return Finalize(plan=_random_plan(rng))

    return advisor


__all__ = ["build_random_baseline"]
