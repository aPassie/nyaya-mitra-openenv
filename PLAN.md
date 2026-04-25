# Nyaya Mitra — Two-Track Build Plan

A paralegal-cum-welfare-advisor RL environment for vulnerable Indian citizens. OpenEnv-compliant, GRPO-trained, adversarially self-improving.

**Themes:** 3.2 (Personalized) + 4 (Self-Improvement) + 2 (Long-Horizon).

This document splits the work into two parallel tracks with a clean interface contract. Time is not the constraint; correctness, anti-reward-hacking, and demo quality are.

---

## Track ownership (horizontal split)

- **Track A — Data + World.** Owns everything the agent acts *on*: knowledge base, eligibility/applicability checkers, citizen simulator, profile generator inputs, demo cases, world dynamics. The "ground truth" of the environment lives here.
- **Track B — Agent + Learning.** Owns everything that *acts and learns*: advisor model, reward functions, GRPO training pipeline, adversarial case generator, eval harness, plots, demo recording. The "verification and optimization" of the environment lives here.

**The seam between them is the OpenEnv environment interface plus the KB JSON schemas.** Both tracks build to that contract. Neither track imports the other's internals; they communicate only through the env API and the KB files.

---

# The interface contract (read first, both tracks)

This is the immutable seam. Both tracks must agree before either starts coding.

## I.1 OpenEnv environment API

Standard Gym-style, OpenEnv `Environment` base class. FastAPI wrapper.

```
reset(seed: int, difficulty: str | None) -> CitizenObservation
step(action: AdvisorAction) -> StepResult(observation, reward, done, info)
state() -> PublicState   # debug only; locked behind env var NYAYA_DEBUG=1
close() -> None
```

`info` dict on every step contains: `elicited_facts: list[str]`, `turn: int`, `max_turns: int`, `phase: "ongoing" | "terminal"`. On terminal step (when `done=True`), `info` additionally contains `reward_breakdown: dict[str, float]` with every named component (Track B will name them; Track A logs them through).

## I.2 AdvisorAction (the only thing the agent emits)

Discriminated union, JSON-serializable. Pydantic on the server, plain dicts on the wire.

- `ASK { question: str, language: "en" | "hi" | "hinglish" }`
- `PROBE { question: str, sensitive_topic: str, language: ... }` — `sensitive_topic` ∈ {caste, dv, disability, immigration, hiv_status, sexual_orientation, mental_health}
- `EXPLAIN { content: str, target_literacy: "low" | "medium" | "high", language: ... }`
- `FINALIZE { plan: ActionPlan }` — ends episode

The schema is enforced server-side. Malformed actions return `done=True, reward=-1`, breakdown logs `format_violation`.

## I.3 ActionPlan (the structural anti-liability constraint)

```
ActionPlan {
  schemes: list[SchemeRecommendation]
  legal_routes: list[LegalRouteRecommendation]   # NB: "routes," not "advice"
  most_important_next_step: str
  plain_summary: { language: str, text: str }
}

SchemeRecommendation {
  scheme_id: str          # MUST exist in KB; hard gate
  rationale_facts: list[str]   # IDs of citizen facts this is grounded in; gate-checked
  required_documents: list[str]
  application_path: { online_url: str | null, offline_office: str | null, offline_steps: list[str] }
}

LegalRouteRecommendation {
  framework_id: str       # MUST exist in KB; hard gate
  applicable_situation: str
  forum: str
  procedural_steps: list[str]
  free_legal_aid_contact: { authority: "NALSA" | "SLSA" | "DLSA", contact_id: str }   # MUST exist in DLSA directory
  required_documents: list[str]
  limitation_period_note: str | null
}
```

**Hard structural rule (drives Track B's gate logic):** every `LegalRouteRecommendation` must include `free_legal_aid_contact`. There is no path for the agent to give standalone "advice." The schema makes routing the only legal output.

**Hard structural rule:** `rationale_facts` must reference fact IDs from `info.elicited_facts` accumulated over the episode. Citizen-contradiction gate (Track B) checks that no rationale fact contradicts what the citizen actually said.

## I.4 CitizenObservation

```
CitizenObservation {
  citizen_utterance: str
  language: "en" | "hi" | "hinglish"
  turn: int
  max_turns: int
  elicited_facts: list[str]      # fact IDs accumulated so far
  facts_revealed_this_turn: list[str]   # NEW IDs added this turn (may be empty)
}
```

`elicited_facts` is the **extractor's** output (see I.6), not the citizen sim's self-report.

## I.5 KB JSON schemas (Track A authors, Track B reads)

Both schemes and legal frameworks live in `src/nyaya_mitra/knowledge/data/`. Track A owns content; Track B writes a thin loader and validators.

```
schemes/<scheme_id>.json
{
  scheme_id: "pm_kisan",            # snake_case, immutable, KB-unique
  name: { en: "...", hi: "..." },
  category: "agriculture_rural" | "women_child" | "education" | "health" | "labor_livelihood",
  ministry: str,
  benefit: { en: "...", hi: "..." },
  eligibility_rules_human: str,     # for the README/demos
  required_documents: list[str],
  application_paths: { online_url: str | null, offline_office_pattern: str | null, offline_steps: list[str] },
  source: { url: str, verified_on: "YYYY-MM-DD" }
}
```

```
frameworks/<framework_id>.json
{
  framework_id: "domestic_violence_act_2005",
  name: { en, hi },
  category: "labor" | "women_protection" | "tenancy_property" | "consumer" | "police_procedure" | "civil_rights",
  applicable_situations: list[str],
  forum: str,
  limitation_period_note: str | null,
  procedural_steps: list[str],
  required_documents: list[str],
  legal_aid_authority: "NALSA" | "SLSA" | "DLSA",
  source: { url: str, verified_on: "YYYY-MM-DD" }
}
```

```
dlsa_directory.json
{
  NALSA: { contact_id, ... },
  SLSAs: { <state>: { contact_id, ... } },
  DLSAs: { <state>.<district>: { contact_id, ... } },
  qualifying_categories: list[str]   # who gets free legal aid
}
```

**Eligibility/applicability functions** (Track A): pure Python, importable, no I/O.

```python
# nyaya_mitra/knowledge/eligibility/<scheme_id>.py
def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    """Returns (eligible, list of human-readable reasons)."""
```

```python
# nyaya_mitra/knowledge/applicability/<framework_id>.py
def check(profile: CitizenProfile) -> tuple[bool, list[str]]:
    """Returns (applies, list of human-readable reasons)."""
```

Both are deterministic, side-effect-free, fully unit-tested by Track A.

## I.6 Fact extractor (Track A authors, both depend on)

Critical anti-reward-hacking component. The citizen sim is **not trusted** to self-report which facts it revealed.

```python
# nyaya_mitra/citizen/extractor.py
def extract_revealed_facts(
    profile: CitizenProfile,
    utterance: str,
    prior_elicited: set[str],
) -> list[str]:
    """
    Inspect the citizen's utterance and return the list of profile fact IDs
    that the utterance actually reveals. Deterministic (regex + classifier),
    not LLM-judged.
    """
```

Implementation: regex/keyword rules per fact ID, plus a small zero-shot classifier as a backstop for paraphrase. Never an LLM that can be prompted by the advisor's questions. Track A owns this.

The env's `step()` calls this extractor on the citizen's utterance and that determines `elicited_facts` — *not* whatever the sim claims.

## I.7 Profile and difficulty

Track A defines:

```python
CitizenProfile {
  demographics: {...}
  economic: {...}
  family: {...}
  situation_specific: { presenting_issue: str, hidden_facts: dict, sensitive_facts: dict }
  behavior: { trust_level: "wary"|"neutral"|"open", verbosity: "low"|"med"|"high",
              language_preference: "en"|"hi"|"hinglish", literacy: "low"|"medium"|"high",
              initial_vague_query: str }
  derived_ground_truth: {
    eligible_schemes: list[str],          # computed from KB checkers, never hand-set
    applicable_frameworks: list[str],
  }
  seed: int
}
```

`derived_ground_truth` is computed at profile-creation time by running every scheme/framework checker against the profile. It is the regression test for both the KB and the rewards: if a scheme checker says "eligible" but the profile author thought it shouldn't be, exactly one of them is wrong.

Difficulty levels: `easy | medium | hard | adaptive` (the last is generator-driven). `easy` profiles have ≥3 eligible schemes and verbose, open citizens. `hard` profiles have integrated scheme+legal applicability, sensitive facts, wary citizens, low literacy.

## I.8 Determinism contract

- Citizen sim runs at temperature 0 with a fixed seed derived from `(profile_seed, turn)`.
- Track A publishes a `tests/test_determinism.py` that asserts: same seed → same conversation transcript across two runs on the same hardware. Hash-check the full transcript.
- Cross-hardware drift is acknowledged in README; W&B logs the hash so divergence is detectable.

## I.9 Rewards contract (Track B authors, Track A consumes only the `info.reward_breakdown` dict)

Track B owns the reward function entirely. Track A's only obligation is to call `compute_reward(profile, plan, transcript, elicited_facts) -> RewardBreakdown` from inside the env's terminal step and emit the breakdown into `info`.

The `RewardBreakdown` is a flat `dict[str, float]` plus a `total: float`. Track B publishes the full key list in `src/nyaya_mitra/rewards/keys.py`; Track A imports nothing else.

---

# Track A — Data + World

You own the environment, the knowledge base, and the citizen simulator. Your output is a runnable OpenEnv server that other people can `reset/step/close` against, with deterministic ground-truth profiles and a citizen sim that can't be tricked into volunteering facts.

## A.1 Repository scaffolding (do this first, hour 0)

```
nyaya-mitra/
  openenv.yaml
  pyproject.toml
  README.md
  src/nyaya_mitra/
    env/
      __init__.py
      models.py           # AdvisorAction, ActionPlan, CitizenObservation, EpisodeState
      environment.py      # OpenEnv Environment subclass
      server.py           # FastAPI wrapper
      client.py           # thin HTTP client (no server imports)
    citizen/
      __init__.py
      simulator.py        # frozen LLM wrapper
      extractor.py        # deterministic fact extractor (I.6)
      prompts/            # system-prompt templates
    knowledge/
      __init__.py
      loader.py
      validators.py
      data/
        schemes/          # 30 JSON files
        frameworks/       # 15 JSON files
        dlsa_directory.json
      eligibility/        # 30 .py files, one per scheme
      applicability/      # 15 .py files, one per framework
    profile/
      __init__.py
      profile.py          # CitizenProfile + derive_ground_truth
      seeds/              # hand-authored seed profiles for tests + warmup curriculum
  tests/
    test_kb_loaders.py
    test_eligibility_each_scheme.py
    test_applicability_each_framework.py
    test_extractor.py
    test_determinism.py
    test_env_loop.py
```

## A.2 Hard rules

1. **Build the env skeleton before the KB.** Hour 0–3 deliverable: a runnable env loop with 2 fake schemes, 1 fake framework, a stub citizen sim that returns canned strings, and a hand-coded "advisor" script that calls `FINALIZE` immediately. Track B unblocks the moment this runs end-to-end.
2. **Use OpenEnv's `Environment` base class.** Do not reinvent the API. Read the Wordle GRPO reference example before writing `environment.py`.
3. **Client/server separation.** `client.py` may import models, nothing else. Run a CI check.
4. **No reserved tool names** (`reset`, `step`, `state`, `close`) for any MCP-style tools you add.
5. **`state()` is debug-only.** Wrap it in `if not os.environ.get("NYAYA_DEBUG"): raise RuntimeError(...)`. Document this in `state()`'s docstring.
6. **Every JSON entry in `data/` has a `source.verified_on` date.** Stale entries fail a CI check after 90 days. Snapshot date this April 2026.
7. **`derive_ground_truth(profile)` is the only way to set `eligible_schemes` and `applicable_frameworks`.** No hand-authoring of these fields. If a profile's intended scheme/framework isn't computed by the checkers, the bug is in the checker.
8. **Citizen sim never receives ground-truth fact IDs.** It receives the profile (so it can roleplay consistently) but never the *list of fact IDs the env tracks*. Otherwise it learns to align its language to the IDs and the agent learns to extract IDs by pattern-matching.
9. **Fact extractor is the source of truth for `elicited_facts`**, not the sim's claims. See I.6.
10. **Server-side max_turns is enforced.** The env terminates the episode at turn 20 regardless of advisor action; logs `truncated_by_env: true` in the breakdown.
11. **Determinism hash-checks** in `test_determinism.py`. CI runs them.

## A.3 Knowledge base content

30 schemes + 15 legal frameworks + DLSA directory, as in the spec. For each entry:

- Fetch from the canonical source (`myScheme.gov.in` for schemes; bare-acts/NALSA portal for frameworks).
- Encode `eligibility_rules_human` verbatim from the source for traceability.
- Write the checker function to match. Unit-test with at least:
  - 3 positive cases (eligible)
  - 3 negative cases (not eligible)
  - 2 edge cases (boundary income, boundary age, etc.)
- Stamp `source.verified_on`.

The 30 + 15 list is in the original spec. Do not deviate from those IDs without coordinating with Track B (who is keying their reward keys to these IDs).

**Output of A.3:** a CSV at `docs/kb_coverage.md` listing each entry with `verified_on`, test count, and a one-line summary. Track B uses this to generate eval cases.

## A.4 Citizen simulator

Frozen Qwen 2.5 3B Instruct (or Llama 3.2 3B — pick one and document the choice). System-prompt template lives in `citizen/prompts/`.

System prompt encodes:
- Hidden profile facts (full profile minus `derived_ground_truth`).
- Hard rules:
  - Never volunteer caste, disability, DV history, immigration, HIV status, sexual orientation, mental health unless directly and respectfully probed via a `PROBE` action.
  - Speak at the encoded literacy level. No legal jargon ever from the citizen.
  - Wary citizens require ≥2 trust-building turns before sensitive disclosure.
  - Mention 1–2 irrelevant details per turn (force the agent to filter).
  - Never contradict previously revealed facts (track a small "claimed-facts" list in the prompt).
  - If asked something the profile doesn't specify, answer with "I'm not sure" or a plausible non-commitment — never invent a new fact.

Output schema from the sim is just a string utterance. The fact extractor (I.6) determines what was revealed.

**Anti-leak audit (Track A's local check, mirrored as a reward gate by Track B):** after every turn, if the extractor reports a sensitive fact ID was revealed, check the prior advisor action. If it wasn't a `PROBE` with the matching `sensitive_topic`, log `sim_leak: true`. Track B will gate this in rewards. Track A also surfaces it in `state()` for debugging.

## A.5 Profile authoring

Hand-author **60 seed profiles** in `profile/seeds/`:
- 20 easy (single scheme, open citizen, no sensitive facts)
- 20 medium (2–3 schemes OR a single legal framework, neutral citizen)
- 20 hard (integrated scheme+legal, sensitive fact, wary citizen, Hindi/Hinglish)

Stratify by language (en/hi/hinglish), state (5+ states represented), and category (each scheme category and each framework category appears in ≥3 profiles).

Each seed profile is its own JSON in `profile/seeds/` with the schema from I.7. `derive_ground_truth` is run as a CI check; if a checker says "eligible" but the profile authoring intent disagrees, that's a flagged conflict to resolve by hand.

## A.6 Tests Track A owns

- `test_kb_loaders.py` — every JSON in `data/` parses, every checker imports, every framework references a valid `legal_aid_authority`.
- `test_eligibility_each_scheme.py` — parametrized over all 30 schemes; each has ≥8 test cases.
- `test_applicability_each_framework.py` — same, all 15 frameworks.
- `test_extractor.py` — golden-file tests on 200+ utterance/fact-ID pairs, including paraphrases, negations, and adversarial phrasings ("I'm not disabled" must NOT mark `disability=true`).
- `test_determinism.py` — same seed → same transcript hash, run twice.
- `test_env_loop.py` — full episode with a stub advisor; assert reward shape and gate behavior.

CI runs all of these on every push.

## A.7 Deployment

- HF Space packaging — Dockerfile in repo root, runs the FastAPI server.
- Push early (hour ~24, after A.1–A.4 are done) so Track B can hit the remote env from Colab.
- `client.py` works against both `localhost:8000` and the deployed Space URL via env var.

## A.8 Track A deliverables checklist

- [ ] Runnable env loop in hour 3 with toy KB
- [ ] All 30 schemes encoded, tested, verified-on stamped
- [ ] All 15 frameworks encoded, tested, verified-on stamped
- [ ] DLSA directory complete
- [ ] Citizen sim with prompt template, anti-leak rules, deterministic at temp 0
- [ ] Fact extractor with 200+ golden tests
- [ ] 60 seed profiles, ground-truth derived not hand-set
- [ ] Full test suite green in CI
- [ ] HF Space deployed, remote roundtrip verified
- [ ] `docs/kb_coverage.md` published for Track B
- [ ] `state()` access locked behind env var

---

# Track B — Agent + Learning

You own the advisor model, the reward function (the hardest part of this project), the GRPO training pipeline, the adversarial case generator, the eval harness, and all demo deliverables. Your output is a trained model that measurably outperforms the baseline on Track A's env.

## B.1 Repository scaffolding

```
src/nyaya_mitra/
  rewards/
    __init__.py
    keys.py             # canonical reward component names (Track A imports this)
    components/
      scheme_precision.py
      scheme_recall.py
      legal_precision.py
      legal_recall.py
      document_accuracy.py
      procedural_correctness.py
      wrong_suggestion_penalty.py
      fact_coverage.py
      sensitivity_correctness.py
      turn_efficiency.py
      integration_bonus.py
      dignity_judge.py     # capped at 5%
    gates/
      format_validity.py
      hallucination.py
      contradiction.py
      sim_leak_passthrough.py
    aggregator.py
  case_gen/
    __init__.py
    generator.py
    validator.py        # rejects degenerate profiles
    diversity.py        # similarity penalty
training/
  train_grpo.py
  train_grpo_colab.ipynb
  train_generator.py
  configs/
    advisor_warmup.yaml
    advisor_phase2.yaml
    generator.yaml
  rollout.py
eval/
  eval_harness.py
  eval_cases/           # 30 held-out, never-seen-during-training
  baselines/
    vanilla_baseline.py
    prompted_baseline.py
  plot.py
  report.md             # generated, committed
demo/
  demo_cases.json
  transcripts/          # baseline_vs_trained_*.md
  plots/                # PNGs, committed
tests/
  test_reward_components.py
  test_gates.py
  test_aggregator.py
  test_rollout.py
```

## B.2 Hard rules

1. **No reward component dominates.** Cap any single LLM-judge component at 5%. Any deterministic component caps at 15%.
2. **Hard gates short-circuit to total = -1.** No negotiation. `format_validity`, `hallucination` (any unknown scheme_id, framework_id, contact_id), and `contradiction` (any rationale_fact contradicts the citizen's actual utterances) all gate to -1.
3. **The reward overlap fix:** `scheme_precision + wrong_suggestion_penalty` was double-counting in the original spec. New decomposition (sums to 100% of soft budget; gates are separate):
   - Scheme precision 10% + Scheme recall 10%
   - Legal precision 10% + Legal recall 10%
   - Document accuracy 10%
   - Procedural correctness 10%
   - Fact coverage 12%
   - Integration bonus 15% (scoped: only awarded on profiles where both apply)
   - Sensitivity correctness 5%
   - Turn efficiency 3%
   - Dignity judge 5% (capped, LLM-judged)
   - **Wrong-suggestion penalty:** removed as a top-level component. Subsumed into precision. Instead, add a per-suggestion `harm_score` (0/1) applied as a small additive penalty (-0.05 per harmful suggestion, max -0.20) — captures "wasted citizen's time/money" without double-counting precision.
4. **Per-turn shaping rewards** (additive, capped at +0.4 per episode to prevent loop farming):
   - +0.02 when an `ASK` causes the extractor to add a fact ID to `elicited_facts`
   - +0.05 when a `PROBE` correctly elicits a sensitive fact relevant to a ground-truth scheme/framework
   - -0.03 per turn after turn 15
   - -0.10 for an `EXPLAIN` flagged jargon-heavy by the literacy checker
5. **Sim-leak gate (passthrough from Track A):** if `info.sim_leak == true` for any turn, zero out the elicitation credit for that turn (don't reward the agent for the sim's mistake) but don't gate the whole episode. Log `sim_leak_count` for monitoring.
6. **Citizen-contradiction gate.** For every fact in `plan.schemes[].rationale_facts ∪ plan.legal_routes[].* `, that fact must be present in `info.elicited_facts` for the episode AND must not have been negated by any citizen utterance. Use a deterministic checker, not an LLM. Hard gate to -1.
7. **No merged 4-bit→16-bit saves.** Save LoRA adapters only. Test post-training inference within 30 min of the run completing.
8. **Log per-component breakdown to W&B AND commit PNGs.** Use `wandb.log` for streaming and `eval/plot.py` to render committed PNGs from W&B exports.
9. **Inspect generations every 100 steps.** `rollout.py` dumps 5 full transcripts to `training/dumps/step_<N>/` automatically. Track B reviews them by hand at least 3 times during training.
10. **Inference uses Unsloth's fast inference path** for rollouts. Per the guide, inference dominates RL runtime.

## B.3 Reward components — design notes

For each component file, the function signature is:

```python
def compute(
    profile: CitizenProfile,
    plan: ActionPlan,
    transcript: list[Turn],
    elicited_facts: set[str],
    breakdown: dict[str, float],   # mutated; for cross-component reads
) -> float:
    """Returns the component's contribution. Range documented per component."""
```

**Scheme/legal precision and recall:** standard set-based on `plan.schemes` ∪ `plan.legal_routes` vs. `profile.derived_ground_truth.*`. Deterministic.

**Document accuracy:** for each suggested item, compute Jaccard between `plan.<item>.required_documents` and the KB-canonical document list for that scheme/framework. Average.

**Procedural correctness:** check `plan.legal_routes[].forum`, `procedural_steps`, and `legal_aid_authority` against the framework's KB entry. Step order matters (Levenshtein on the step list).

**Fact coverage:** `|elicited_facts ∩ relevant_ground_truth_facts| / |relevant_ground_truth_facts|`, where `relevant_ground_truth_facts` is the union of facts referenced by the eligibility checkers for the profile's eligible schemes and applicable frameworks. Track A exposes this via `profile.relevant_facts()`.

**Sensitivity correctness:** of profiles with `sensitive_facts` non-empty, was each sensitive fact elicited via a `PROBE` with matching `sensitive_topic`? Heuristic, but the structural action-type discrimination makes this checkable.

**Turn efficiency:** `max(0, 1 - turns/max_turns) * coverage_factor` where `coverage_factor` zeroes out efficiency rewards when fact_coverage < 0.5. Prevents "FINALIZE early with no info" gaming.

**Integration bonus:** only on profiles where `len(eligible_schemes) > 0 AND len(applicable_frameworks) > 0`. Awarded if both components have precision ≥ 0.5 AND recall ≥ 0.5. Otherwise 0. Steep but the right shape.

**Dignity judge:** small LLM (GPT-4o-mini class or Claude Haiku) with a tight rubric: tone respectful? Did the agent avoid blaming the citizen? Did the agent explain at the right literacy level? Output 0–1. Capped at 5% weight.

## B.4 Tests Track B owns

- `test_reward_components.py` — for each component, ≥5 hand-crafted (profile, plan, expected_score) golden tests.
- `test_gates.py` — every gate triggers correctly on a malformed plan; doesn't trigger on a valid one. Includes a "sneaky" test where the plan is valid but rationale_facts contradict the transcript — must gate.
- `test_aggregator.py` — weighted sum matches hand calculation; gate behavior wins over component sums.
- `test_rollout.py` — full GRPO rollout against a stub env runs without error and produces a valid loss.

## B.5 Training pipeline

**Stack:** TRL `GRPOTrainer` + Unsloth 4-bit + Qwen 2.5 7B Instruct (advisor), Qwen 2.5 3B Instruct (frozen citizen sim, separate process), Qwen 2.5 3B Instruct (case generator).

**Phases:**

- **Phase 1 — Warmup, advisor only, hand-authored curriculum.** ~500 episodes. Use Track A's 60 seed profiles, weighted toward easy. No generator. Goal: rolling-100 mean reward > 0.3. The guide is explicit: ensure P(success) > 0 before scaling. If after 500 episodes mean reward is still ≤0.1, stop and inspect — likely a reward-shape bug, not a learning problem.
- **Phase 2 — Co-trained adversarial.** Generator enabled, both updated via GRPO. Generator's reward is `-1 * advisor_reward` plus diversity penalty plus realism gate (the validator). ~2000 episodes. **Co-training is unstable; alternate updates** (advisor 100 episodes, generator 50 episodes, repeat) rather than fully simultaneous.
- **Phase 3 — Frozen-generator eval.** Snapshot the generator at the end of phase 2. Generate 100 hard cases with it. Run eval-only rollouts against the frozen advisor on those + the 30 held-out cases.

**Logging (mandatory):**
- W&B project `nyaya-mitra-grpo`
- Per-step total reward, all 11 named components, all 4 gates' trigger frequency, mean episode length, sim_leak_count, format_violation_count
- Per-100-steps: 5 full transcript dumps to disk
- Per-200-steps: snapshot LoRA adapter

**Compute target:** A100 or H100 for the actual training runs. T4 only for the Colab reproducibility notebook (which uses 3B advisor and a tiny config so judges can replay it on free Colab).

## B.6 Adversarial case generator

3B model, GRPO-trained, outputs constrained JSON profiles.

- **Validator (hard gate before reward):** generated profile must pass Track A's profile schema, derive_ground_truth must produce ≥1 eligible scheme OR ≥1 applicable framework, all field combinations internally consistent (e.g., age ≥ 18 if marital_status="married"). Invalid → generator gets -1, no advisor rollout wasted.
- **Diversity penalty:** sentence-embed the profile's "presenting_issue + situation_specific" string and compute mean similarity to the last 50 generated profiles. Penalty = -0.5 × max_similarity.
- **Realism check:** small classifier (or rule-based) flags impossible combos (rural Punjab + occupation="software engineer" + monthly_income=8000). Optional but valuable.
- **Reward = -advisor_reward - 0.5 × max_similarity - 1.0 × (1 if invalid else 0)`.

If the generator collapses to a single mode in monitoring, halt phase 2 and inspect.

## B.7 Eval harness

`eval/eval_cases/` contains 30 hand-authored profiles never seen in training. Composition:
- 10 welfare-only
- 10 legal-only
- 10 integrated

Stratified across language, literacy, sensitivity. Track A produces these in close coordination with Track B (it's the one cross-track artifact other than the interface).

`eval_harness.py` runs:
- Vanilla baseline (Qwen 2.5 7B Instruct, no fine-tuning, minimal system prompt)
- Prompted baseline (same model, hand-tuned strong system prompt with KB excerpts in context — this is the *honest* comparison)
- Trained model (your submission)

Outputs:
- Mean total reward per cohort
- Per-component bars
- % all-gates-passed
- % integrated cases solved (the headline number)
- Mean turns to resolution
- Sensitivity F1
- Side-by-side transcripts on the 3 demo cases

`eval/report.md` is generated and committed.

## B.8 Plots and demo

Committed PNGs in `demo/plots/`:
- `total_reward_curve.png` — phase 1 + phase 2, both axes labeled, units stated
- `reward_components_stacked.png` — stacked area chart of all 11 components over training
- `gate_trigger_frequency.png` — line per gate, log-scale y
- `baseline_vs_trained_bars.png` — eval cohort × model, headline metric
- `integration_solve_rate.png` — the headline number
- `sim_leak_over_training.png` — should trend down as the agent learns to PROBE rather than fish

`demo/transcripts/`: 3 cases (welfare-only migrant, legal-only DV, integrated migrant+wages), baseline-vs-trained side-by-side in markdown.

`<2 min YouTube video`: scripted around the integrated migrant case in Hindi. Baseline fails → trained agent succeeds → cut to plots → cut to README. Linked from README, NOT bundled.

`HF blog post` or slide deck: explains the env, the reward design (esp. the gates and the sim-leak audit), and the adversarial generator. Emphasize anti-reward-hacking; that's the technical story.

`HF Space` Gradio UI: a minimal "chat with the trained advisor as a synthetic citizen" interface. Pulls a random profile from the eval set, lets the visitor watch the advisor work.

## B.9 Track B deliverables checklist

- [ ] Reward components implemented, each with golden tests
- [ ] All 4 gates implemented and tested
- [ ] Aggregator with weight sanity check (sums to 100%, gates dominate)
- [ ] Phase 1 training run complete; rolling-100 mean reward ≥ 0.3
- [ ] Phase 2 co-training run complete; integration solve rate up vs. baseline
- [ ] Phase 3 frozen-generator eval complete
- [ ] Vanilla + prompted baselines run on the 30 eval cases
- [ ] LoRA adapters saved (no merged 4-bit→16-bit)
- [ ] All committed PNGs rendered with axis labels and units
- [ ] 3 demo case transcripts side-by-side
- [ ] `eval/report.md` with headline numbers
- [ ] HF Space Gradio UI deployed
- [ ] <2 min YouTube video published, linked from README
- [ ] HF blog post / slide deck published, linked from README
- [ ] README rewritten with impact framing and "what this is not" section

---

# Cross-track integration checkpoints

Hard checkpoints at which both tracks must sync. The merge contract is the interface (sections I.1–I.9); these checkpoints verify it holds.

**Checkpoint 1 — End-to-end skeleton runs.** Track A has a runnable env with toy KB and stub citizen. Track B has a stub reward function (returns random scalar) and runs a 1-episode GRPO step against the env. Goal: prove the wire works.

**Checkpoint 2 — KB v1 + reward v1.** Track A has 12 schemes + 6 frameworks fully tested. Track B has all reward components implemented (against the partial KB). They run a full episode end-to-end with real reward, real citizen sim, hand-coded advisor that always FINALIZEs. Goal: prove the reward is computable and reasonable.

**Checkpoint 3 — Phase 1 training feasibility.** Full KB done by Track A. Phase 1 training run started by Track B. After 100 steps, both inspect transcripts together. If the advisor is doing something obviously wrong (always FINALIZE turn 1, hallucinating IDs, etc.), debug before running the full 500.

**Checkpoint 4 — Phase 2 readiness.** Phase 1 mean reward ≥ 0.3. Generator validator working. Both agree on the 30 eval cases (Track A authors, Track B reviews). Co-training begins.

**Checkpoint 5 — Eval and demo.** All training complete. Eval run. Track A finalizes Space deployment with trained model. Track B finalizes plots and demo. Both review README + video together.

---

# What you should *not* do (both tracks)

- Do not deviate from the interface (I.1–I.9) without a coordinated change to both tracks.
- Do not let the citizen sim self-report fact IDs.
- Do not allow `state()` to be called from training rollouts.
- Do not save merged 4-bit→16-bit checkpoints.
- Do not let any single LLM-judge component exceed 5% weight.
- Do not commit huge video files; link from README.
- Do not stamp `verified_on` without actually verifying.
- Do not skip the prompted baseline — the vanilla-only comparison is weak and judges will notice.
- Do not run training without per-component logging; aggregate reward alone hides everything.
- Do not assume cross-hardware determinism; hash-check transcripts and log the hash.

---

# Open questions to resolve in your sync (before either track starts coding)

1. **Citizen sim model:** Qwen 2.5 3B Instruct vs Llama 3.2 3B Instruct. Pick by Hindi quality on a 5-prompt smoke test.
2. **Advisor model:** Qwen 2.5 7B Instruct (per spec) is the default. If A100 isn't available, fall back to 3B and document the choice.
3. **Demo language:** Hindi recommended for the migrant case, but verify both models speak it well enough on day 1 before committing the video script.
4. **Eval set authorship:** Track A drafts, Track B reviews and signs off. Don't let Track A also be the eval author of last resort — Track B's review is the check on KB quality.
5. **Compute:** A100 vs H100 vs HF ZeroGPU vs Colab Pro. Decide before phase 2 (when wall-clock matters).
6. **State coverage in seed profiles:** which 5 Indian states get represented? Pick early so Track A doesn't redo profile demographics.

Resolve these in the kickoff call. Everything else is in the interface.
