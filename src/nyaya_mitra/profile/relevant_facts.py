"""facts referenced by eligibility/applicability checkers for a profile's eligible items.
used by track B's fact_coverage reward. expand as the kb grows."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile
from nyaya_mitra.knowledge.loader import KnowledgeBase

_RELEVANT_BY_ID: dict[str, set[str]] = {
    "pm_kisan": {"occupation_farmer", "land_small"},
    "pmuy": {"gender_female", "bpl_household", "no_lpg"},
    "mgnrega": {"residence_rural", "age_adult", "willing_unskilled_work"},
    "pm_awas_grameen": {"residence_rural", "secc_listed", "kuccha_or_houseless"},
    "ayushman_bharat": {"secc_listed_or_urban_occ"},
    "pmsby": {"age_18_to_70", "has_bank_account"},
    "domestic_violence_act_2005": {"gender_female", "dv_present"},
    "minimum_wages_act_1948": {"is_wage_worker", "wages_below_minimum"},
    "maternity_benefit_act_1961": {
        "gender_female",
        "formally_employed",
        "pregnant_or_postpartum",
        "denied_maternity_benefit",
    },
    "consumer_protection_act_2019": {"is_consumer_disputant", "defect_or_deficiency"},
}


def relevant_facts(profile: CitizenProfile, kb: KnowledgeBase) -> set[str]:
    out: set[str] = set()
    truth = profile.derived_ground_truth
    for sid in truth.eligible_schemes:
        out |= _RELEVANT_BY_ID.get(sid, set())
    for fid in truth.applicable_frameworks:
        out |= _RELEVANT_BY_ID.get(fid, set())
    return out
