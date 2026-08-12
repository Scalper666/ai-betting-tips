"""Copy pipeline-generated data into the Astro project.

The pipeline writes predictions/screener/stats into  <repo>/data/.
The Astro site reads them from  <astro>/src/data/.
This bridges the two so one `update.bat` refresh feeds the live site — no manual copy.

The Astro project is located in this order:
  1) ASTRO_DIR in pipeline/.env   (absolute path to the Astro project root)
  2) sibling folder ../sharptips-astro   (the default layout)

Only the three generated files are synced. bookmakers/casinos/countries are
hand-maintained inside the Astro project and are deliberately left untouched.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent  # D:\CLOUDE\sharptips
SRC = ROOT / "data"

# Files the pipeline generates and the Astro site consumes.
# history.json feeds the "Recent results" transparency block (settled bets).
# content.json holds AI-written page copy (generate_content.py); optional.
FILES = ["predictions.json", "screener.json", "stats.json", "history.json", "content.json",
         "football-data.json", "results-archive.json", "odds_history.json",
         # co.uk import: read by research/home-advantage and lib/seasonTables
         "results-import.json",
         # eternal match-page registry: read by lib/matchPages
         "match-registry.json"]


def astro_data_dir() -> Path | None:
    candidates = []
    env = os.getenv("ASTRO_DIR", "").strip()
    if env:
        candidates.append(Path(env))
    candidates.append(ROOT)                              # pipeline inside the Astro repo
    candidates.append(ROOT.parent / "sharptips-astro")  # legacy sibling layout
    for c in candidates:
        if (c / "src" / "data").is_dir():
            return c / "src" / "data"
    return None


def main() -> int:
    dest = astro_data_dir()
    if dest is None:
        print("[sync_astro] Astro project not found "
              "(set ASTRO_DIR in .env or place it at ../sharptips-astro) — skipped")
        return 0

    copied = 0
    for name in FILES:
        src = SRC / name
        if not src.exists():
            print(f"[sync_astro] {name}: source missing — skipped")
            continue
        shutil.copyfile(src, dest / name)
        copied += 1
        print(f"[sync_astro] {name} -> {dest / name}")

    print(f"[sync_astro] {copied}/{len(FILES)} files synced to Astro")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
