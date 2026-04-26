"""baseline advisors used in the eval harness as comparison floors.

four baselines, in order from weakest to strongest:

- random_baseline: picks actions uniformly at random; the absolute floor.
  every other baseline must beat this for the env to be learnable.

- scripted_baseline: deterministic, no LLM, no GPU. uses the env's elicited_facts
  directly to produce plans. acts as the strong-non-LLM ceiling.

- vanilla_baseline: LLM with minimal system prompt. honest "what does the base
  model do without any context?" comparison.

- prompted_baseline: same LLM with hand-tuned system prompt + KB excerpts in
  context. the *honest* comparison — what a non-RL approach can extract from
  the same model. RL must beat this to be a meaningful win.

all baselines implement the rollout.Advisor signature so they're swappable.
"""

from eval.baselines.prompted_baseline import build_prompted_baseline
from eval.baselines.random_baseline import build_random_baseline
from eval.baselines.scripted_baseline import build_scripted_baseline
from eval.baselines.vanilla_baseline import build_vanilla_baseline

__all__ = [
    "build_prompted_baseline",
    "build_random_baseline",
    "build_scripted_baseline",
    "build_vanilla_baseline",
]
