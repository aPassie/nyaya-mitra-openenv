"""deterministic fact extractor. NEVER an llm — citizen sim must not be tricked into volunteering ids."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nyaya_mitra.interface import CitizenProfile


_NEGATION = re.compile(r"\b(not|nahi|kabhi nahi|never|no\b)", re.IGNORECASE)

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(farmer|kisan|kheti|farming)\b", re.IGNORECASE), "occupation_farmer"),
    (re.compile(r"\b(woman|women|girl|mahila|aurat|female)\b", re.IGNORECASE), "gender_female"),
    (re.compile(r"\b(bpl|below poverty)\b", re.IGNORECASE), "bpl_household"),
    (
        re.compile(r"\b(small holding|small plot|chhota khet|marginal)\b", re.IGNORECASE),
        "land_small",
    ),
    (
        re.compile(
            r"\b(domestic violence|husband hits|husband beats|ghar mein maar|pati maarta)\b",
            re.IGNORECASE,
        ),
        "dv_present",
    ),
    (re.compile(r"\bpunjab\b", re.IGNORECASE), "state_punjab"),
    (re.compile(r"\bbihar\b", re.IGNORECASE), "state_bihar"),
    (re.compile(r"\b(no lpg|no gas connection|chulha|wood stove)\b", re.IGNORECASE), "no_lpg"),
]


class FactExtractor:
    def extract(
        self,
        profile: CitizenProfile,
        utterance: str,
        prior_elicited: set[str],
    ) -> list[str]:
        out: list[str] = []
        for pattern, fact_id in _PATTERNS:
            if fact_id in prior_elicited:
                continue
            if not pattern.search(utterance):
                continue
            window_start = max(pattern.search(utterance).start() - 20, 0)
            window = utterance[window_start : pattern.search(utterance).end()]
            if _NEGATION.search(window):
                continue
            out.append(fact_id)
        return out
