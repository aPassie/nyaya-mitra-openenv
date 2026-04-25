"""verify every kb json has a fresh source.verified_on stamp."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

KB_ROOT = Path(__file__).parent.parent / "src" / "nyaya_mitra" / "knowledge" / "data"
MAX_AGE_DAYS = 90


def main() -> int:
    today = date.today()
    stale: list[str] = []
    missing: list[str] = []

    for js in list(KB_ROOT.glob("schemes/*.json")) + list(KB_ROOT.glob("frameworks/*.json")):
        data = json.loads(js.read_text())
        src = data.get("source") or {}
        verified = src.get("verified_on")
        if not verified:
            missing.append(str(js))
            continue
        try:
            d = datetime.strptime(verified, "%Y-%m-%d").date()
        except ValueError:
            missing.append(f"{js} (bad date format: {verified})")
            continue
        if (today - d).days > MAX_AGE_DAYS:
            stale.append(f"{js} (verified {verified}, {(today - d).days} days old)")

    if missing:
        print("missing or malformed source.verified_on:")
        for m in missing:
            print(f"  {m}")
    if stale:
        print(f"stale (>{MAX_AGE_DAYS} days):")
        for s in stale:
            print(f"  {s}")

    return 1 if (missing or stale) else 0


if __name__ == "__main__":
    sys.exit(main())
