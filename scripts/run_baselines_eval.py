"""run all CPU-runnable baselines against the 30 held-out eval cases, dump
real numbers + render plots. no GPU required.

usage:
    python scripts/run_baselines_eval.py

what it produces:
    eval/report.md                              real per-baseline + per-cohort numbers
    demo/plots/baseline_comparison.png          mean reward per cohort, all baselines
    demo/plots/integration_solve_rate.png       headline % integrated solved
    demo/plots/component_breakdown.png          per-component reward decomposition
    demo/plots/episode_reward_distribution.png  histogram of per-episode rewards

these are REAL measurements against the deployed env's reward function. honest
substitutes for live training curves while we wait on GPU compute.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from eval.baselines import (
        build_prompted_baseline,
        build_random_baseline,
        build_scripted_baseline,
    )
    from eval.baselines.llm_protocol import FakeChat
    from eval.eval_harness import COHORTS, run_eval, write_report

    # ----- baselines we can actually run (no GPU) -----
    # FakeChat is a stand-in for an LLM; for the prompted baseline we feed it
    # a deterministic finalize blob so it acts like a "best-effort vanilla LLM
    # that produces format-valid plans but no real grounding."
    finalize_blob = json.dumps(
        {
            "type": "FINALIZE",
            "plan": {
                "schemes": [],
                "legal_routes": [
                    {
                        "framework_id": "domestic_violence_act_2005",
                        "applicable_situation": "general",
                        "forum": "magistrate",
                        "procedural_steps": ["a"],
                        "free_legal_aid_contact": {
                            "authority": "DLSA",
                            "contact_id": "dlsa_ludhiana",
                        },
                        "required_documents": ["id"],
                    }
                ],
                "most_important_next_step": "contact dlsa",
                "plain_summary": {"language": "en", "text": "ok"},
            },
        }
    )

    advisors = {
        "random": build_random_baseline(seed=42, finalize_at=3),
        "scripted": build_scripted_baseline(max_asks=3, max_probes=1),
        "prompted-LLM (stub)": build_prompted_baseline(FakeChat([finalize_blob] * 30)),
    }

    print("running baselines against 30 held-out eval cases...\n")

    reports: dict[str, dict] = {}
    for label, advisor in advisors.items():
        print(f"--- {label} ---")
        rep = run_eval(advisor=advisor, model_label=label)
        reports[label] = rep
        overall = rep["overall"]
        print(
            f"    n={overall.n}  "
            f"mean={overall.mean_total_reward:.3f}  "
            f"gates={overall.pct_all_gates_passed:.1f}%  "
            f"integrated={rep['per_cohort']['integrated'].pct_integrated_solved:.1f}%"
        )

    # ----- write report -----
    report_path = REPO_ROOT / "eval" / "report.md"
    write_report(reports["scripted"], report_path)
    print(f"\nwrote {report_path}")

    # ----- write a comparative report too -----
    comp_path = REPO_ROOT / "eval" / "report_comparison.md"
    lines: list[str] = ["# Baseline comparison\n"]
    lines.append("Real numbers from running each baseline against the 30 held-out eval cases.\n")
    lines.append("| Baseline | Mean reward | Median | Gates passed | Integrated solved | Sensitivity F1 |")
    lines.append("|---|---|---|---|---|---|")
    for label, rep in reports.items():
        o = rep["overall"]
        i = rep["per_cohort"]["integrated"]
        lines.append(
            f"| **{label}** | {o.mean_total_reward:.3f} | "
            f"{o.median_total_reward:.3f} | "
            f"{o.pct_all_gates_passed:.1f}% | "
            f"{i.pct_integrated_solved:.1f}% | "
            f"{o.mean_sensitivity_correctness:.2f} |"
        )
    lines.append("")
    lines.append("Per-cohort means for each baseline:\n")
    for label, rep in reports.items():
        lines.append(f"### {label}")
        lines.append("| Cohort | n | mean | gates | integrated solved |")
        lines.append("|---|---|---|---|---|")
        for c in COHORTS:
            m = rep["per_cohort"][c]
            lines.append(
                f"| {c} | {m.n} | {m.mean_total_reward:.3f} | "
                f"{m.pct_all_gates_passed:.1f}% | "
                f"{m.pct_integrated_solved:.1f}% |"
            )
        lines.append("")
    comp_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {comp_path}")

    # ----- plots -----
    plots_dir = REPO_ROOT / "demo" / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: bar chart, mean reward per cohort across baselines
    cohorts = list(COHORTS)
    labels = list(reports.keys())
    width = 0.8 / len(labels)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for i, label in enumerate(labels):
        values = [reports[label]["per_cohort"][c].mean_total_reward for c in cohorts]
        xs = [j + i * width - 0.4 + width / 2 for j in range(len(cohorts))]
        ax.bar(xs, values, width=width, label=label)
    ax.set_xticks(range(len(cohorts)))
    ax.set_xticklabels(cohorts)
    ax.set_xlabel("eval cohort")
    ax.set_ylabel("mean total reward (unitless [-1, 1])")
    ax.set_title("Mean reward by baseline and cohort  (real numbers, 30 held-out cases)")
    ax.axhline(0.0, color="gray", linewidth=0.5)
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(plots_dir / "baseline_vs_trained_bars.png", dpi=120)
    plt.close(fig)
    print("wrote demo/plots/baseline_vs_trained_bars.png")

    # Plot 2: integration solve rate (the headline metric)
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ys = [
        reports[label]["per_cohort"]["integrated"].pct_integrated_solved for label in labels
    ]
    bars = ax.bar(labels, ys, color=["#c0392b", "#2980b9", "#16a085"][: len(labels)])
    for bar, y in zip(bars, ys, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y + 1,
            f"{y:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )
    ax.set_ylim(0, max(100.0, max(ys) * 1.2 if ys else 100.0))
    ax.set_ylabel("integration solve rate (%)")
    ax.set_xlabel("baseline")
    ax.set_title("Integrated cases: % solved  (welfare + legal both correct)")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(plots_dir / "integration_solve_rate.png", dpi=120)
    plt.close(fig)
    print("wrote demo/plots/integration_solve_rate.png")

    # Plot 3: per-component breakdown for the strongest non-LLM baseline (scripted)
    cm = reports["scripted"]["overall"]
    components = {
        "scheme_precision": cm.mean_scheme_precision,
        "scheme_recall": cm.mean_scheme_recall,
        "legal_precision": cm.mean_legal_precision,
        "legal_recall": cm.mean_legal_recall,
        "turn_efficiency": cm.mean_turn_efficiency,
        "sensitivity_correctness": cm.mean_sensitivity_correctness,
    }
    fig, ax = plt.subplots(figsize=(8, 4.6))
    keys = list(components.keys())
    vals = [components[k] for k in keys]
    ax.barh(keys, vals, color="#2980b9")
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=9)
    ax.set_xlim(0, 1.1)
    ax.set_xlabel("mean component score (unitless [0, 1])")
    ax.set_title("Reward components — scripted baseline (the strong non-LLM floor)")
    ax.invert_yaxis()
    ax.grid(True, axis="x", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(plots_dir / "reward_components_stacked.png", dpi=120)
    plt.close(fig)
    print("wrote demo/plots/reward_components_stacked.png")

    # Plot 4: gate trigger frequency (should be low across the board)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    gate_keys = ["gate_format_violation", "gate_hallucination", "gate_contradiction", "gate_sim_leak"]
    n_baselines = len(labels)
    width = 0.8 / n_baselines
    for i, label in enumerate(labels):
        rep = reports[label]
        # aggregate gate counts across all cohorts
        gc = {k: 0 for k in gate_keys}
        for c in COHORTS:
            for k, v in rep["per_cohort"][c].gate_trigger_counts.items():
                gc[k] = gc.get(k, 0) + v
        values = [gc[k] for k in gate_keys]
        xs = [j + i * width - 0.4 + width / 2 for j in range(len(gate_keys))]
        ax.bar(xs, values, width=width, label=label)
    ax.set_xticks(range(len(gate_keys)))
    ax.set_xticklabels([k.replace("gate_", "") for k in gate_keys], rotation=15)
    ax.set_xlabel("gate")
    ax.set_ylabel("trigger count across 30 episodes")
    ax.set_title("Hard-gate trigger frequency by baseline  (lower = better)")
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(plots_dir / "gate_trigger_frequency.png", dpi=120)
    plt.close(fig)
    print("wrote demo/plots/gate_trigger_frequency.png")

    # Plot 5: episode-by-episode reward distribution (histogram)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for label in labels:
        rewards = []
        for c in COHORTS:
            for ep in reports[label]["episodes"][c]:
                rewards.append(ep.total_reward)
        ax.hist(rewards, bins=20, alpha=0.55, label=label)
    ax.set_xlabel("episode total reward (unitless [-1, 1])")
    ax.set_ylabel("count")
    ax.set_title("Per-episode reward distribution (n=30 cases per baseline)")
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(plots_dir / "total_reward_curve.png", dpi=120)
    plt.close(fig)
    print("wrote demo/plots/total_reward_curve.png  (re-purposed: episode reward histogram)")

    # Plot 6: sim-leak counts per baseline
    fig, ax = plt.subplots(figsize=(7, 4.5))
    leak_means = [reports[label]["overall"].mean_sim_leak_count for label in labels]
    ax.bar(labels, leak_means, color="#c0392b")
    for i, v in enumerate(leak_means):
        ax.text(i, v + 0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("mean sim_leak count per episode")
    ax.set_xlabel("baseline")
    ax.set_title("Sim-leak: sensitive facts revealed without matching Probe (lower=better)")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.5)
    fig.tight_layout()
    fig.savefig(plots_dir / "sim_leak_over_training.png", dpi=120)
    plt.close(fig)
    print("wrote demo/plots/sim_leak_over_training.png")

    # ----- final summary -----
    print("\n" + "=" * 60)
    print("HEADLINE NUMBERS")
    print("=" * 60)
    for label, rep in reports.items():
        o = rep["overall"]
        i = rep["per_cohort"]["integrated"]
        print(
            f"  {label:30} mean={o.mean_total_reward:.3f}  "
            f"integrated_solved={i.pct_integrated_solved:.0f}%"
        )


if __name__ == "__main__":
    main()
