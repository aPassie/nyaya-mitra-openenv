"""
contract test for the seam between tracks A and B.

if this passes, both tracks can integrate cleanly.
if it fails, the interface has drifted — STOP and re-sync.

most checks are pytest.skip stubs that get filled in as tracks land.
the cross-track-imports check is live from day one — it's the mechanical
guardrail that prevents silent coupling.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = REPO_ROOT / "src" / "nyaya_mitra"

TRACK_A_PACKAGES = ("env", "citizen", "knowledge", "profile")
TRACK_B_PACKAGES = ("rewards", "case_gen", "advisor")
TRACK_B_TOPLEVEL_DIRS = ("training", "eval")
ALLOWED_CROSS_IMPORTS = {"nyaya_mitra.env.client"}


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                out.add(node.module)
    return out


def _is_in_packages(import_name: str, packages: tuple[str, ...]) -> bool:
    for pkg in packages:
        prefix = f"nyaya_mitra.{pkg}"
        if import_name == prefix or import_name.startswith(prefix + "."):
            return True
    return False


def _scan_dir(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def test_no_cross_track_imports():
    """
    track A code may not import track B internals; track B may not import track A internals.
    only allowed cross-import is nyaya_mitra.env.client (the public http client).
    both sides freely import nyaya_mitra.interface.
    """
    violations: list[str] = []

    for pkg in TRACK_A_PACKAGES:
        pkg_root = SRC_ROOT / pkg
        if not pkg_root.exists():
            continue
        for py in _scan_dir(pkg_root):
            for imp in _module_imports(py):
                if imp in ALLOWED_CROSS_IMPORTS:
                    continue
                if _is_in_packages(imp, TRACK_B_PACKAGES):
                    violations.append(f"[A] {py.relative_to(REPO_ROOT)} imports [B] {imp}")

    for pkg in TRACK_B_PACKAGES:
        pkg_root = SRC_ROOT / pkg
        if not pkg_root.exists():
            continue
        for py in _scan_dir(pkg_root):
            for imp in _module_imports(py):
                if imp in ALLOWED_CROSS_IMPORTS:
                    continue
                if _is_in_packages(imp, TRACK_A_PACKAGES):
                    violations.append(f"[B] {py.relative_to(REPO_ROOT)} imports [A] {imp}")

    for top in TRACK_B_TOPLEVEL_DIRS:
        top_root = REPO_ROOT / top
        if not top_root.exists():
            continue
        for py in _scan_dir(top_root):
            for imp in _module_imports(py):
                if imp in ALLOWED_CROSS_IMPORTS:
                    continue
                if _is_in_packages(imp, TRACK_A_PACKAGES):
                    violations.append(f"[B] {py.relative_to(REPO_ROOT)} imports [A] {imp}")

    assert not violations, "cross-track imports detected:\n  " + "\n  ".join(violations)


def test_interface_imports_cleanly():
    """interface is the only shared package and must import without side effects."""
    import nyaya_mitra.interface as iface

    assert hasattr(iface, "AdvisorAction")
    assert hasattr(iface, "ActionPlan")
    assert hasattr(iface, "CitizenObservation")
    assert hasattr(iface, "CitizenProfile")
    assert hasattr(iface, "ALL_KEYS")
    assert hasattr(iface, "SCHEME_SCHEMA")


def test_reward_keys_are_unique_strings():
    from nyaya_mitra.interface import ALL_KEYS

    assert len(ALL_KEYS) == len(set(ALL_KEYS))
    for k in ALL_KEYS:
        assert isinstance(k, str) and k


def test_action_plan_requires_legal_aid_contact():
    """
    structural anti-liability rule: every legal route must carry a free_legal_aid_contact.
    pydantic should reject construction without it.
    """
    from pydantic import ValidationError

    from nyaya_mitra.interface import LegalRouteRecommendation

    with pytest.raises(ValidationError):
        LegalRouteRecommendation(
            framework_id="domestic_violence_act_2005",
            applicable_situation="x",
            forum="magistrate",
            procedural_steps=["a"],
            required_documents=["b"],
        )


def test_action_plan_round_trips_through_json():
    from nyaya_mitra.interface import (
        ActionPlan,
        FreeLegalAidContact,
        LegalRouteRecommendation,
        PlainSummary,
    )

    plan = ActionPlan(
        legal_routes=[
            LegalRouteRecommendation(
                framework_id="domestic_violence_act_2005",
                applicable_situation="x",
                forum="magistrate",
                procedural_steps=["a"],
                free_legal_aid_contact=FreeLegalAidContact(authority="DLSA", contact_id="dl_001"),
                required_documents=["b"],
            )
        ],
        most_important_next_step="contact dlsa",
        plain_summary=PlainSummary(language="hi", text="..."),
    )
    raw = plan.model_dump_json()
    revived = ActionPlan.model_validate_json(raw)
    assert revived == plan


@pytest.mark.skip(reason="awaiting track A: env loop end-to-end")
def test_full_episode_with_stub_advisor():
    pass


@pytest.mark.skip(reason="awaiting track A: state() debug-gate")
def test_state_locked_without_debug_env():
    pass


@pytest.mark.skip(reason="awaiting track B: aggregator emits all reward keys")
def test_aggregator_emits_all_keys():
    pass


@pytest.mark.skip(reason="awaiting track A: kb json files exist")
def test_kb_json_matches_schema():
    pass
