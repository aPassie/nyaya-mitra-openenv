"""applicability checker for the consumer protection act, 2019. pure python, no i/o."""

from __future__ import annotations

from nyaya_mitra.interface import CitizenProfile


def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    is_consumer = bool(profile.economic.get("is_consumer_disputant"))
    facts = profile.situation_specific.hidden_facts or {}
    has_grievance = bool(
        facts.get("defective_goods")
        or facts.get("deficient_service")
        or facts.get("unfair_trade_practice")
        or facts.get("misleading_ad")
    )

    if not is_consumer:
        return False, ["not a consumer with a paid transaction"]
    if not has_grievance:
        return False, ["no defect, deficiency, or unfair-practice grievance reported"]
    return True, ["consumer with defect or deficient service or unfair practice"]
