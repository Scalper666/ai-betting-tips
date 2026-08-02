"""
Ping IndexNow (Bing / Yandex / Seznam / Naver) with every URL from the built
sitemap after a deploy — new and refreshed pages get crawled within minutes
instead of days. Google does not support IndexNow; it uses the sitemap.

The key is public by protocol design: search engines verify it by fetching
https://{host}/{key}.txt, which lives in public/.
"""
from __future__ import annotations
import json, re, sys, urllib.request, ssl
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
HOST = "ai-betting-tips.com"
KEY = "7c41a9f2d85e4b06b3c9f1a8e2d47905"


def main() -> int:
    sm = ROOT / "dist" / "sitemap-0.xml"
    if not sm.exists():
        print("⚠ dist/sitemap-0.xml not found — build first; skipping IndexNow")
        return 0
    urls = re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8"))
    if not urls:
        print("⚠ sitemap has no URLs — skipping")
        return 0

    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls[:10000],
    }).encode()

    ctx = ssl.create_default_context()
    if sys.platform == "win32":
        ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    # bing.com/indexnow validates reliably and shares URLs with the whole
    # IndexNow network; the api.indexnow.org aggregator 403s on fresh keys
    req = urllib.request.Request(
        "https://www.bing.com/indexnow", data=body,
        headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            print(f"✓ IndexNow: {len(urls)} URLs submitted, HTTP {r.status}")
    except Exception as e:
        print(f"⚠ IndexNow ping failed (non-fatal): {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
