# Architecture

Jointly authored by both tracks. Edit via `[S]` PR.

The system has three layers:

1. **Environment (Track A)** — OpenEnv-compliant FastAPI server. Owns world dynamics, the citizen simulator, the knowledge base, and ground-truth derivation. Exposes `reset/step/state/close` over HTTP.
2. **Interface (Shared)** — `src/nyaya_mitra/interface/` defines every JSON-serializable schema crossing the seam: `AdvisorAction`, `ActionPlan`, `CitizenObservation`, `CitizenProfile`, reward keys, and KB JSON schemas. Neither track owns it; both import from it.
3. **Agent + Learning (Track B)** — Advisor model (Qwen 2.5 7B + LoRA), reward components and gates, GRPO trainer, adversarial case generator, eval harness, demo. Talks to the env only via the `nyaya_mitra.env.client` HTTP wrapper.

The integration contract test (`tests/integration/test_interface_contract.py`) mechanically asserts that schemas line up across the seam and that no module on one side imports the other side's internals (the only allowed cross-track import is `nyaya_mitra.env.client`, which is intentionally a thin wrapper around `interface/`).

See `PLAN.md` sections I.1–I.9 for the full interface contract.
