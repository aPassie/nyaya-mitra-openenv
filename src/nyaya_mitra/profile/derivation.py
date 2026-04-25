"""profile loader and ground-truth derivation. derive_ground_truth runs every kb checker against the profile."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from nyaya_mitra.interface import CitizenProfile, DerivedGroundTruth
from nyaya_mitra.knowledge.loader import KnowledgeBase

SEEDS_ROOT = Path(__file__).parent / "seeds"


def derive_ground_truth(profile: CitizenProfile, kb: KnowledgeBase) -> DerivedGroundTruth:
    eligible: list[str] = []
    for scheme_id in kb.scheme_ids():
        try:
            mod = importlib.import_module(f"nyaya_mitra.knowledge.eligibility.{scheme_id}")
        except ModuleNotFoundError:
            continue
        ok, _ = mod.check(profile)
        if ok:
            eligible.append(scheme_id)

    applicable: list[str] = []
    for framework_id in kb.framework_ids():
        try:
            mod = importlib.import_module(f"nyaya_mitra.knowledge.applicability.{framework_id}")
        except ModuleNotFoundError:
            continue
        ok, _ = mod.check(profile)
        if ok:
            applicable.append(framework_id)

    return DerivedGroundTruth(
        eligible_schemes=eligible,
        applicable_frameworks=applicable,
    )


def load_profile(seed: int, difficulty: str | None, kb: KnowledgeBase) -> CitizenProfile:
    diff_dir = difficulty or "easy"
    candidates = sorted((SEEDS_ROOT / diff_dir).glob("*.json"))
    if not candidates:
        candidates = sorted((SEEDS_ROOT / "easy").glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"no seed profiles in {SEEDS_ROOT}")
    chosen = candidates[seed % len(candidates)]
    raw = json.loads(chosen.read_text(encoding="utf-8"))
    profile = CitizenProfile.model_validate(raw)
    profile.derived_ground_truth = derive_ground_truth(profile, kb)
    return profile
