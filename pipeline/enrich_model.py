"""Recompute the model block on an existing predictions.json — no API calls.

build.py writes model probabilities while fetching odds, so adding a new model
field normally means waiting for the next scheduled run (or spending Odds API
credits on a fresh fetch). This walks the current feed instead and refills the
`model` block from the local GoalModel, which reads only committed result data.

Usage:  python pipeline/enrich_model.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "data" / "predictions.json"


def main() -> int:
    from model import GoalModel

    data = json.loads(FEED.read_text(encoding="utf-8"))
    tips = data.get("tips", [])
    gm = GoalModel()
    print(f"--> goal model: {len(gm.leagues)} league(s) fitted")

    filled = skipped = 0
    for t in tips:
        probs = gm.probs(t.get("sport_key", ""), t.get("home", ""), t.get("away", ""))
        if not probs:
            skipped += 1
            continue
        t["model"] = {
            "xg_home": probs["lambda_home"],
            "xg_away": probs["lambda_away"],
            "p_home": probs["p_home"],
            "p_draw": probs["p_draw"],
            "p_away": probs["p_away"],
            "scorelines": probs.get("scorelines"),
            "p_btts": probs.get("p_btts"),
        }
        filled += 1

    FEED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {FEED.name}: {filled} fixtures enriched, {skipped} without a trustworthy fit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
