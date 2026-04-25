"""canonical reward component names. track B owns weights and logic; track A only logs through."""

from __future__ import annotations

SCHEME_PRECISION = "scheme_precision"
SCHEME_RECALL = "scheme_recall"
LEGAL_PRECISION = "legal_precision"
LEGAL_RECALL = "legal_recall"
DOCUMENT_ACCURACY = "document_accuracy"
PROCEDURAL_CORRECTNESS = "procedural_correctness"
FACT_COVERAGE = "fact_coverage"
SENSITIVITY_CORRECTNESS = "sensitivity_correctness"
TURN_EFFICIENCY = "turn_efficiency"
INTEGRATION_BONUS = "integration_bonus"
DIGNITY_JUDGE = "dignity_judge"
HARM_PENALTY = "harm_penalty"

GATE_FORMAT_VIOLATION = "gate_format_violation"
GATE_HALLUCINATION = "gate_hallucination"
GATE_CONTRADICTION = "gate_contradiction"
GATE_SIM_LEAK = "gate_sim_leak"

SHAPING_ASK_FACT = "shaping_ask_fact"
SHAPING_PROBE_SENSITIVE = "shaping_probe_sensitive"
SHAPING_LATE_TURN = "shaping_late_turn"
SHAPING_JARGON = "shaping_jargon"

TOTAL = "total"

COMPONENT_KEYS: tuple[str, ...] = (
    SCHEME_PRECISION,
    SCHEME_RECALL,
    LEGAL_PRECISION,
    LEGAL_RECALL,
    DOCUMENT_ACCURACY,
    PROCEDURAL_CORRECTNESS,
    FACT_COVERAGE,
    SENSITIVITY_CORRECTNESS,
    TURN_EFFICIENCY,
    INTEGRATION_BONUS,
    DIGNITY_JUDGE,
    HARM_PENALTY,
)

GATE_KEYS: tuple[str, ...] = (
    GATE_FORMAT_VIOLATION,
    GATE_HALLUCINATION,
    GATE_CONTRADICTION,
    GATE_SIM_LEAK,
)

SHAPING_KEYS: tuple[str, ...] = (
    SHAPING_ASK_FACT,
    SHAPING_PROBE_SENSITIVE,
    SHAPING_LATE_TURN,
    SHAPING_JARGON,
)

ALL_KEYS: tuple[str, ...] = COMPONENT_KEYS + GATE_KEYS + SHAPING_KEYS + (TOTAL,)
