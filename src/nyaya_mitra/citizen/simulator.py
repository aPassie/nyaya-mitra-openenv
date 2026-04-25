"""stub citizen sim that returns canned strings. real frozen-llm version lands in track A.4."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nyaya_mitra.interface import AdvisorAction, Ask, Explain, Probe

if TYPE_CHECKING:
    from nyaya_mitra.env.episode_state import TurnRecord
    from nyaya_mitra.interface import CitizenProfile


class CitizenSimulator:
    def initial_utterance(self, profile: CitizenProfile) -> str:
        return profile.behavior.initial_vague_query

    def respond(
        self,
        profile: CitizenProfile,
        prior_transcript: list[TurnRecord],
        advisor_action: AdvisorAction,
    ) -> str:
        if isinstance(advisor_action, Probe):
            facts = profile.situation_specific.sensitive_facts
            if facts:
                return "haan, kuch baat hai jo main kehna chahti hoon..."
            return "nahi, aisa kuch nahi hai."
        if isinstance(advisor_action, Ask):
            return "main kuch aur bata sakti hoon... kya aap mujhe specific batayenge?"
        if isinstance(advisor_action, Explain):
            return "samajh gayi, aage kya karna hai?"
        return "..."
