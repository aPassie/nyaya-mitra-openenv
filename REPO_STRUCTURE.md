# Nyaya Mitra — Repo Structure & Git Workflow

A conflict-resistant layout for parallel work across two tracks.

## Core principle

**Each file has exactly one owner.** Folders are not enough — shared files (pyproject.toml, README, configs) cause 80% of merge conflicts in projects like this. This layout names every shared file's owner explicitly.

Ownership tags throughout this doc:
- `[A]` = Track A (Data + World)
- `[B]` = Track B (Agent + Learning)
- `[S]` = Shared interface — changes only via PR with both tracks' review

---

## Repository layout

```
nyaya-mitra/
├── README.md                          [B]  written last; impact framing + links
├── pyproject.toml                     [S]  see "Shared file rules" below
├── uv.lock / poetry.lock              [S]  regenerated, never hand-edited
├── .python-version                    [S]
├── .gitignore                         [S]  initial commit, rarely touched
├── .pre-commit-config.yaml            [S]  initial commit, rarely touched
├── openenv.yaml                       [A]
├── Dockerfile                         [A]  HF Space deployment
├── PLAN.md                            [S]  the spec; immutable once kickoff done
├── REPO_STRUCTURE.md                  [S]  this file
│
├── .github/
│   ├── CODEOWNERS                     [S]  auto-assigns reviewers
│   └── workflows/
│       ├── ci-track-a.yml             [A]  runs A's tests only
│       ├── ci-track-b.yml             [B]  runs B's tests only
│       └── ci-integration.yml         [S]  runs the cross-track integration test
│
├── src/nyaya_mitra/
│   │
│   ├── interface/                     [S]  ━━━ THE SEAM ━━━
│   │   ├── __init__.py                     reset/step/state/close signatures,
│   │   ├── actions.py                      AdvisorAction discriminated union,
│   │   ├── observations.py                 CitizenObservation,
│   │   ├── plan.py                         ActionPlan + sub-models,
│   │   ├── profile.py                      CitizenProfile schema (NOT logic),
│   │   ├── reward_keys.py                  canonical reward component names,
│   │   └── kb_schemas.py                   JSON-schema for schemes/frameworks
│   │
│   ├── env/                           [A]  OpenEnv environment
│   │   ├── __init__.py
│   │   ├── environment.py                  Environment subclass, reset/step/state
│   │   ├── server.py                       FastAPI wrapper
│   │   ├── client.py                       HTTP client (no server imports)
│   │   └── episode_state.py
│   │
│   ├── citizen/                       [A]  citizen sim + extractor
│   │   ├── __init__.py
│   │   ├── simulator.py
│   │   ├── extractor.py                    deterministic fact extractor
│   │   └── prompts/
│   │       ├── system_template.txt
│   │       └── persona_modifiers.txt
│   │
│   ├── knowledge/                     [A]  KB content + checkers
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── validators.py
│   │   ├── data/
│   │   │   ├── schemes/                    30 JSON files, one per scheme
│   │   │   │   ├── pm_kisan.json
│   │   │   │   └── ...
│   │   │   ├── frameworks/                 15 JSON files, one per framework
│   │   │   │   ├── domestic_violence_act_2005.json
│   │   │   │   └── ...
│   │   │   └── dlsa_directory.json
│   │   ├── eligibility/                    one .py per scheme
│   │   │   ├── __init__.py
│   │   │   ├── pm_kisan.py
│   │   │   └── ...
│   │   └── applicability/                  one .py per framework
│   │       ├── __init__.py
│   │       ├── domestic_violence_act_2005.py
│   │       └── ...
│   │
│   ├── profile/                       [A]  profile derivation + seed bank
│   │   ├── __init__.py
│   │   ├── derivation.py                   derive_ground_truth()
│   │   ├── relevant_facts.py
│   │   └── seeds/                          60 seed profile JSONs
│   │       ├── easy/
│   │       ├── medium/
│   │       └── hard/
│   │
│   ├── rewards/                       [B]  reward components + gates
│   │   ├── __init__.py
│   │   ├── aggregator.py
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── scheme_precision.py
│   │   │   ├── scheme_recall.py
│   │   │   ├── legal_precision.py
│   │   │   ├── legal_recall.py
│   │   │   ├── document_accuracy.py
│   │   │   ├── procedural_correctness.py
│   │   │   ├── fact_coverage.py
│   │   │   ├── sensitivity_correctness.py
│   │   │   ├── turn_efficiency.py
│   │   │   ├── integration_bonus.py
│   │   │   └── dignity_judge.py
│   │   └── gates/
│   │       ├── __init__.py
│   │       ├── format_validity.py
│   │       ├── hallucination.py
│   │       ├── contradiction.py
│   │       └── sim_leak_passthrough.py
│   │
│   ├── case_gen/                      [B]  adversarial generator
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── validator.py
│   │   └── diversity.py
│   │
│   └── advisor/                       [B]  advisor model wrapper
│       ├── __init__.py
│       ├── model.py                        Unsloth load + LoRA setup
│       ├── inference.py                    fast rollout path
│       └── prompts/
│           └── system_template.txt
│
├── training/                          [B]
│   ├── __init__.py
│   ├── train_grpo.py
│   ├── train_grpo_colab.ipynb
│   ├── train_generator.py
│   ├── rollout.py
│   ├── configs/
│   │   ├── advisor_warmup.yaml
│   │   ├── advisor_phase2.yaml
│   │   └── generator.yaml
│   └── dumps/                              gitignored; transcript dumps go here
│
├── eval/                              [B]
│   ├── __init__.py
│   ├── eval_harness.py
│   ├── plot.py
│   ├── report.md                           generated, committed
│   ├── eval_cases/                         30 held-out profiles
│   │   ├── welfare_only/
│   │   ├── legal_only/
│   │   └── integrated/
│   └── baselines/
│       ├── vanilla_baseline.py
│       └── prompted_baseline.py
│
├── demo/                              [B]
│   ├── demo_cases.json
│   ├── transcripts/
│   │   ├── case_01_migrant_baseline.md
│   │   ├── case_01_migrant_trained.md
│   │   └── ...
│   └── plots/                              committed PNGs
│       ├── total_reward_curve.png
│       ├── reward_components_stacked.png
│       ├── gate_trigger_frequency.png
│       ├── baseline_vs_trained_bars.png
│       ├── integration_solve_rate.png
│       └── sim_leak_over_training.png
│
├── docs/
│   ├── kb_coverage.md                 [A]  generated, committed
│   ├── reward_design.md               [B]
│   ├── architecture.md                [S]  jointly authored, rarely changed
│   └── what_this_is_not.md            [B]  liability/scope framing
│
├── tests/
│   ├── conftest.py                    [S]  shared fixtures only
│   ├── track_a/                       [A]
│   │   ├── test_kb_loaders.py
│   │   ├── test_eligibility_each_scheme.py
│   │   ├── test_applicability_each_framework.py
│   │   ├── test_extractor.py
│   │   ├── test_determinism.py
│   │   └── test_env_loop.py
│   ├── track_b/                       [B]
│   │   ├── test_reward_components.py
│   │   ├── test_gates.py
│   │   ├── test_aggregator.py
│   │   └── test_rollout.py
│   └── integration/                   [S]  cross-track contract tests
│       └── test_interface_contract.py
│
└── scripts/
    ├── deploy_space.sh                [A]
    ├── verify_kb_sources.py           [A]
    ├── render_plots.py                [B]
    └── run_eval.sh                    [B]
```

---

## Shared file rules

These are the files most likely to cause conflicts. Each has a specific protocol.

### `pyproject.toml`  [S]

The single most conflict-prone file. Rule: **never edit directly during day-to-day work.**

- Initial setup commits a complete `pyproject.toml` with all dependencies for both tracks listed up front (overestimate; cull at the end).
- If you genuinely need a new dep mid-project: open a PR with **only** the pyproject change, get a one-line approval from the other track, merge fast.
- Use dependency groups to keep tracks visually separate inside the file:
  ```toml
  [project.optional-dependencies]
  track_a = ["fastapi", "uvicorn", "pydantic", ...]
  track_b = ["trl", "unsloth", "wandb", "matplotlib", ...]
  dev = ["pytest", "ruff", "pre-commit"]
  ```
- Lock file is regenerated by whoever ran `uv lock` / `poetry lock`. Commit alongside the pyproject change in the same PR.

### `README.md`  [B writes, A reviews]

Track B owns the final README. **Do not start writing it until phase 1 training is underway** — most "early READMEs" get rewritten anyway. Track A contributes content via `docs/kb_coverage.md` which Track B links from the README.

### `src/nyaya_mitra/interface/`  [S]

The interface is the bedrock. Once both tracks have signed off in the kickoff:

- Any change requires a PR labelled `interface-change`.
- CODEOWNERS (below) auto-requests review from both tracks.
- Merging requires approval from a member of *each* track.
- The PR must update `tests/integration/test_interface_contract.py` in the same commit.

In practice you should rarely change this. If you find yourself wanting to, that's usually a sign the change should live on one side of the seam, not in the interface itself.

### `openenv.yaml`  [A]

Track A owns. Track B never edits.

### `.github/workflows/`  [split]

Three separate workflow files so each track's CI is independent:
- `ci-track-a.yml` — runs `pytest tests/track_a/` only. Owned by A.
- `ci-track-b.yml` — runs `pytest tests/track_b/` only. Owned by B.
- `ci-integration.yml` — runs `tests/integration/` and lint. Shared.

This means a flaky B test never blocks A's PR and vice versa.

### `.gitignore`  [S]

Set up once at kickoff:
```
__pycache__/
*.pyc
.venv/
.env
training/dumps/
training/checkpoints/
*.log
.pytest_cache/
.ruff_cache/
wandb/
```

Don't tweak per-track. If you need to ignore something track-specific, add a `.gitignore` inside the relevant subfolder.

---

## CODEOWNERS file

`.github/CODEOWNERS`:

```
# Default: both tracks review
*                                           @<a-handle> @<b-handle>

# Track A exclusive ownership
/src/nyaya_mitra/env/                       @<a-handle>
/src/nyaya_mitra/citizen/                   @<a-handle>
/src/nyaya_mitra/knowledge/                 @<a-handle>
/src/nyaya_mitra/profile/                   @<a-handle>
/openenv.yaml                               @<a-handle>
/Dockerfile                                 @<a-handle>
/tests/track_a/                             @<a-handle>
/.github/workflows/ci-track-a.yml           @<a-handle>
/scripts/deploy_space.sh                    @<a-handle>
/scripts/verify_kb_sources.py               @<a-handle>
/docs/kb_coverage.md                        @<a-handle>

# Track B exclusive ownership
/src/nyaya_mitra/rewards/                   @<b-handle>
/src/nyaya_mitra/case_gen/                  @<b-handle>
/src/nyaya_mitra/advisor/                   @<b-handle>
/training/                                  @<b-handle>
/eval/                                      @<b-handle>
/demo/                                      @<b-handle>
/tests/track_b/                             @<b-handle>
/.github/workflows/ci-track-b.yml           @<b-handle>
/scripts/render_plots.py                    @<b-handle>
/scripts/run_eval.sh                        @<b-handle>
/docs/reward_design.md                      @<b-handle>
/docs/what_this_is_not.md                   @<b-handle>
/README.md                                  @<b-handle>

# Shared interface — both must approve
/src/nyaya_mitra/interface/                 @<a-handle> @<b-handle>
/PLAN.md                                    @<a-handle> @<b-handle>
/pyproject.toml                             @<a-handle> @<b-handle>
/tests/integration/                         @<a-handle> @<b-handle>
/tests/conftest.py                          @<a-handle> @<b-handle>
/.github/workflows/ci-integration.yml       @<a-handle> @<b-handle>
/docs/architecture.md                       @<a-handle> @<b-handle>
```

Replace `<a-handle>` and `<b-handle>` with actual GitHub usernames before first commit.

---

## Branch strategy

**Two long-lived branches:**

```
main                  protected; only PRs from track-a, track-b, or interface-change can merge
track-a               Track A's working branch
track-b               Track B's working branch
```

- Each track works on its own long-lived branch and rebases onto `main` daily.
- PRs from `track-a` → `main` and `track-b` → `main` happen 1–2× per day, *small and frequent*.
- Feature branches off `track-a` / `track-b` are fine for in-track multi-step work.
- Never PR `track-a` → `track-b` or vice versa. They only meet through `main`.

**Day-to-day flow per track:**

```bash
# morning
git checkout track-a
git fetch origin
git rebase origin/main           # pull in B's merged work
# ...do work on a feature branch off track-a...
git checkout -b track-a/scheme-pm-kisan
# work, commit
git push -u origin track-a/scheme-pm-kisan
# open PR: track-a/scheme-pm-kisan → main
# CI runs track-a workflow only
# merge after green; delete branch
git checkout track-a
git rebase origin/main
git push --force-with-lease       # only because nobody else commits to track-a
```

The `--force-with-lease` is fine on a single-owner branch but **never on `main`**.

**Rebase, don't merge.** History stays clean and the integration test runs against a linear history that's easy to reason about.

---

## The integration contract test

`tests/integration/test_interface_contract.py` is the single most important file in the repo. It runs in `ci-integration.yml` on every PR to `main`.

Skeleton:

```python
"""
Verifies the seam between Track A and Track B holds.
If this passes, both tracks can integrate cleanly.
If it fails, the interface has drifted — STOP and re-sync.
"""

def test_advisor_action_schema_matches():
    """The action schema Track A's env accepts is what Track B's advisor emits."""

def test_action_plan_schema_matches():
    """The plan schema Track A's env validates is what Track B's reward consumes."""

def test_reward_keys_complete():
    """Every key Track B's aggregator produces is in interface/reward_keys.py."""

def test_kb_schema_compliance():
    """Every JSON in knowledge/data/ matches interface/kb_schemas.py."""

def test_full_episode_with_stub_advisor():
    """End-to-end: env reset → 3 steps → finalize → reward computed → all keys present."""

def test_state_locked_without_debug_env():
    """state() raises without NYAYA_DEBUG=1 set."""

def test_no_cross_track_imports():
    """Track A modules don't import from rewards/, case_gen/, advisor/, training/, eval/.
       Track B modules don't import from env/, citizen/, knowledge/, profile/.
       Both may import from interface/."""
```

The last test is critical — it mechanically prevents the cross-track imports that cause silent coupling.

---

## PR conventions

**Title prefix tells everyone the blast radius:**
- `[A] ...` — Track A only, no shared files touched
- `[B] ...` — Track B only, no shared files touched
- `[S] ...` — touches a shared file; both tracks must review
- `[interface] ...` — touches `src/nyaya_mitra/interface/`; mandatory both-track review + integration test update

**Size:** keep PRs small. <400 lines changed is ideal. If you find yourself in a 1000-line PR, it's almost certainly mixing track work with shared changes — split it.

**Description template:**

```markdown
## What
<one paragraph>

## Touches shared files?
[yes/no — if yes, list them]

## Interface change?
[yes/no — if yes, link to updated integration test]

## Tests added/changed
- ...
```

---

## What to do at kickoff (in order)

1. Both teammates create their GitHub handles, share, and one of you bootstraps the repo with this exact structure.
2. Commit `PLAN.md`, `REPO_STRUCTURE.md`, `.gitignore`, `pyproject.toml` with all dependencies, `.github/CODEOWNERS`.
3. Stub out `src/nyaya_mitra/interface/` with the schema definitions from PLAN.md sections I.2–I.7. Both review and sign off.
4. Stub out `tests/integration/test_interface_contract.py` with `pytest.skip` placeholders that you'll fill in.
5. Set up the three CI workflows. Verify all three run green on a no-op PR.
6. Push `main`, branch off `track-a` and `track-b`, push both.
7. Both tracks start working in their own lanes.

After that initial setup, you should never need to coordinate on file ownership again — CODEOWNERS, the workflow split, and the linter on cross-track imports all enforce the boundary mechanically.

---

## What this prevents

- ✅ Two people editing `pyproject.toml` at the same time (single-PR rule + groups)
- ✅ Two people editing the same Python file (CODEOWNERS at directory level)
- ✅ Track A breaking Track B's tests (separate CI workflows)
- ✅ Silent coupling via cross-track imports (mechanical test)
- ✅ Interface drift between what env emits and what reward expects (integration contract test)
- ✅ A bad merge to `main` blocking both tracks (small frequent PRs, rebase workflow)

## What this does NOT prevent

- A logical interface change that *passes* the contract test but is wrong. Both tracks must still talk during the cross-track checkpoints in PLAN.md.
- One track being faster than the other and sitting idle. That's a coordination problem, not a git problem.
- Forgetting to run pre-commit. Use `pre-commit install` after first clone.
