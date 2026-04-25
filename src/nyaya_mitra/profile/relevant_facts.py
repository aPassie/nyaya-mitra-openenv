"""facts referenced by the eligibility/applicability checkers for a profile's eligible items.
stub for hour 0-3; track A elaborates as the kb grows. used by track B's fact_coverage reward."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile
from nyaya_mitra.knowledge.loader import KnowledgeBase

_RELEVANT_BY_ID: dict[str, set[str]] = {
    "pm_kisan": {"occupation_farmer", "land_small"},
    "pmuy": {"gender_female", "bpl_household", "no_lpg"},
    "domestic_violence_act_2005": {"gender_female", "dv_present"},
}


def relevant_facts(profile: CitizenProfile, kb: KnowledgeBase) -> set[str]:
    out: set[str] = set()
    truth = profile.derived_ground_truth
    for sid in truth.eligible_schemes:
        out |= _RELEVANT_BY_ID.get(sid, set())
    for fid in truth.applicable_frameworks:
        out |= _RELEVANT_BY_ID.get(fid, set())
    return out
