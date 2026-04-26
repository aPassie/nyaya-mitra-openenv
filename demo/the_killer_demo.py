"""The 5-line demo that shows what makes Nyaya Mitra different.

Drop this into a talk, paste into a slide, or run it inline. It shows the
structural anti-liability rule firing: the agent literally cannot produce
a "give legal advice" output because Pydantic refuses to construct a
LegalRouteRecommendation without a free_legal_aid_contact.

Run: python demo/the_killer_demo.py
"""

from __future__ import annotations

from pydantic import ValidationError

from nyaya_mitra.interface import LegalRouteRecommendation


def main() -> None:
    print("=" * 72)
    print("DEMO: the agent cannot output advice without routing to legal aid.")
    print("=" * 72)
    print()
    print("trying to construct a LegalRouteRecommendation WITHOUT a free_legal_aid_contact...")
    print()

    try:
        bad = LegalRouteRecommendation(
            framework_id="domestic_violence_act_2005",
            applicable_situation="abuse at home",
            forum="magistrate of the first class",
            procedural_steps=[
                "approach a protection officer",
                "file form DV-1",
            ],
            required_documents=["identity proof", "marriage proof"],
            # missing: free_legal_aid_contact
        )
        print(f"  unexpected: pydantic accepted it: {bad}")
    except ValidationError as e:
        print(f"✓ pydantic rejected it. {e.error_count()} validation error(s):")
        for err in e.errors()[:3]:
            print(f"    - {err['loc']}: {err['msg']}")

    print()
    print("now try with a free_legal_aid_contact attached...")
    print()
    from nyaya_mitra.interface import FreeLegalAidContact

    good = LegalRouteRecommendation(
        framework_id="domestic_violence_act_2005",
        applicable_situation="abuse at home",
        forum="magistrate of the first class",
        procedural_steps=["approach a protection officer", "file form DV-1"],
        required_documents=["identity proof", "marriage proof"],
        free_legal_aid_contact=FreeLegalAidContact(
            authority="DLSA", contact_id="dlsa_ludhiana"
        ),
    )
    print(f"✓ accepted: legal route to {good.framework_id}")
    print(f"  routed via: {good.free_legal_aid_contact.authority} {good.free_legal_aid_contact.contact_id}")
    print()
    print("the schema makes routing the only possible legal output.")
    print("training cannot drift the agent into giving advice — it would emit a malformed action,")
    print("the env would reject it, the format gate would fire, total reward would go to -1.")


if __name__ == "__main__":
    main()
