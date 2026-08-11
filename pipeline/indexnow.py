"""
Ping IndexNow (Bing / Yandex / Seznam / Naver) after a deploy. Google does not
support IndexNow; it uses the sitemap.

Submits ONLY what changed — never the whole site. The first version pushed all
~5,000 sitemap URLs twice a day; the protocol explicitly asks for changed URLs
only, and repeated full-site resubmission is the abuse pattern that gets a host
soft-banned. Ours was: every batch started returning 403 (from CI and locally,
single-URL pings included) while Bing Webmaster Tools showed "IndexNow not set
up". Volume is now capped and the state of what was already announced lives in
data/indexnow-state.json (committed, so CI runs share it).

What gets submitted, in priority order, capped at MAX_SUBMIT:
  1. URLs never announced before (new pages)
  2. A fixed set of hubs whose content genuinely changes every build

The key is public by protocol design: engines verify it by fetching
https://{host}/{key}.txt, which lives in public/.
"""
from __future__ import annotations
import json, re, sys, time, urllib.request, ssl
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "data" / "indexnow-state.json"
HOST = "ai-betting-tips.com"
KEY = "7c41a9f2d85e4b06b3c9f1a8e2d47905"

MAX_SUBMIT = 200          # per run; well under any documented threshold
BATCH = 100

# pages that are genuinely new content on every rebuild
ALWAYS = [
    f"https://{HOST}/",
    f"https://{HOST}/predictions/",
    f"https://{HOST}/predictions/today/",
    f"https://{HOST}/predictions/tomorrow/",
    f"https://{HOST}/predictions/weekend/",
    f"https://{HOST}/bet-of-the-day/",
    f"https://{HOST}/screener/",
    f"https://{HOST}/dropping-odds/",
]


def main() -> int:
    sm = ROOT / "dist" / "sitemap-0.xml"
    if not sm.exists():
        print("⚠ dist/sitemap-0.xml not found — build first; skipping IndexNow")
        return 0
    urls = re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8"))
    if not urls:
        print("⚠ sitemap has no URLs — skipping")
        return 0

    try:
        seen = set(json.loads(STATE.read_text(encoding="utf-8")).get("announced", []))
    except (OSError, ValueError):
        seen = set()

    fresh = [u for u in urls if u not in seen]
    payload = fresh[:MAX_SUBMIT]
    room = MAX_SUBMIT - len(payload)
    if room > 0:
        payload += [u for u in ALWAYS if u not in payload][:room]

    if not payload:
        print("✓ IndexNow: nothing new to announce")
        return 0

    ctx = ssl.create_default_context()
    if sys.platform == "win32":
        ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT

    ok_urls: list[str] = []
    failures = 0
    for i in range(0, len(payload), BATCH):
        chunk = payload[i:i + BATCH]
        body = json.dumps({
            "host": HOST,
            "key": KEY,
            "keyLocation": f"https://{HOST}/{KEY}.txt",
            "urlList": chunk,
        }).encode()
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow", data=body,
            headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                if r.status in (200, 202):
                    ok_urls += chunk
                else:
                    failures += 1
                    print(f"  ⚠ batch {i // BATCH + 1}: HTTP {r.status}")
        except Exception as e:
            failures += 1
            print(f"  ⚠ batch {i // BATCH + 1}: {e}")
        time.sleep(2)

    # only accepted URLs enter the state — rejected ones retry next run
    if ok_urls:
        seen.update(u for u in ok_urls if u not in ALWAYS)
        STATE.write_text(json.dumps(
            {"updated_at": datetime.now(timezone.utc).isoformat(),
             "announced": sorted(seen)}), encoding="utf-8")

    print(f"✓ IndexNow: {len(ok_urls)} URLs accepted, {failures} batch(es) failed, "
          f"{len(fresh) - len([u for u in ok_urls if u in fresh])} new still queued")
    # every batch rejected = the endpoint is refusing us — surface it in CI
    # instead of a green tick over a dead integration. Partial success stays 0.
    return 1 if failures and not ok_urls else 0


if __name__ == "__main__":
    raise SystemExit(main())
