"""Translate editor-written static content (guides, glossary) into site locales.

One-off / incremental: reads src/data/guides.json + glossary.json, translates
each entry into es/pt/de/fr with Haiku (cheap, structured output), and writes
src/data/guides.{lang}.json / glossary.{lang}.json next to the originals.

Caching: every translated entry stores _src_hash (sha256 of the translatable
source fields). Unchanged entries are never re-translated, so re-running after
adding one new guide only pays for that guide. Files are committed to the repo;
this script is run manually, not by CI.

Usage:
    python pipeline/translate_static.py            # translate everything missing
    python pipeline/translate_static.py --only guides
    python pipeline/translate_static.py --langs es,pt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "data"

MODEL = os.getenv("TRANSLATE_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 4000
WORKERS = 4
LANGS = {
    "es": "Spanish (neutral Latin-American, usable in Spain too)",
    "pt": "Brazilian Portuguese",
    "de": "German (Germany)",
    "fr": "French (France)",
}

SYSTEM = (
    "You are a professional betting-industry translator. Translate the given JSON "
    "content into {language}. Rules: keep ALL numbers, odds, currency amounts, brand "
    "names, league names and URLs exactly as-is; use the betting terminology real "
    "bookmakers use in that market (e.g. Spanish 'cuotas', German 'Quoten', Portuguese "
    "'odds' is commonly kept, French 'cotes'); keep the honest, no-hype tone of the "
    "source, including every risk warning and 18+ note; translate idiomatically, not "
    "word-for-word; keep roughly the same length. Return only the translated fields "
    "in the same JSON structure."
)


def _obj(props: dict, req: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": req, "additionalProperties": False}


S = {"type": "string"}
S_ARR = {"type": "array", "items": S}
S_FAQ = {"type": "array", "items": _obj({"q": S, "a": S}, ["q", "a"])}
S_SECTIONS = {"type": "array", "items": _obj({"h": S, "ps": S_ARR}, ["h", "ps"])}

# translatable fields per collection (schema built per-item from what exists)
GUIDE_FIELDS = {"title": S, "nav": S, "desc": S, "sections": S_SECTIONS,
                "example": S, "takeaways": S_ARR, "faq": S_FAQ}
TERM_FIELDS = {"term": S, "short": S, "definition": S_ARR, "example": S}
# season hubs: window is a date range shown as-is, slug/sport_key are keys
SEASON_FIELDS = {"window": S, "intro": S_ARR, "outlook": S_ARR, "faq": S_FAQ,
                 "pre_season_note": S}


def src_hash(entry: dict, fields: dict) -> str:
    payload = {k: entry[k] for k in fields if k in entry}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def make_client():
    import anthropic
    from anthropic import DefaultHttpxClient
    kw = {}
    if sys.platform == "win32":
        # same AV TLS-interception fix as generate_content.py / odds_api.py
        try:
            ctx = ssl.create_default_context()
            ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
            kw["http_client"] = DefaultHttpxClient(verify=ctx)
        except Exception:
            pass
    return anthropic.Anthropic(**kw)


def translate_one(client, entry: dict, fields: dict, lang: str, label_extra: dict | None = None) -> dict:
    """Translate the translatable subset of `entry`; return full localized entry."""
    payload = {k: entry[k] for k in fields if k in entry}
    schema = _obj({k: fields[k] for k in payload}, list(payload))
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM.format(language=LANGS[lang]),
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("model refused")
    data = json.loads(next(b.text for b in resp.content if b.type == "text"))
    out = {**entry, **data, "_src_hash": src_hash(entry, fields), "_model": resp.model}
    if label_extra:
        out.update(label_extra)
    return out, resp.usage.input_tokens, resp.usage.output_tokens


def run_collection(client, name: str, entries: list[dict], fields: dict,
                   key: str, langs: list[str], extra_translate) -> dict:
    """Translate one collection into every language; returns usage totals."""
    tin = tout = done = 0
    for lang in langs:
        out_path = SRC / f"{name}.{lang}.json"
        existing = {}
        if out_path.exists():
            try:
                old = json.loads(out_path.read_text(encoding="utf-8"))
                existing = {e[key]: e for e in old.get(name if name != "glossary" else "terms", [])}
            except Exception:
                existing = {}

        todo, keep = [], []
        for e in entries:
            h = src_hash(e, fields)
            prev = existing.get(e[key])
            if prev and prev.get("_src_hash") == h:
                keep.append(prev)
            else:
                todo.append(e)

        results = {}
        if todo:
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                futs = {pool.submit(translate_one, client, e, fields, lang,
                                    extra_translate(client, e, lang) if extra_translate else None): e[key]
                        for e in todo}
                for f in as_completed(futs):
                    k = futs[f]
                    try:
                        entry, i, o = f.result()
                        results[k] = entry
                        tin += i; tout += o; done += 1
                        print(f"  ✓ {lang}:{name}:{k}")
                    except Exception as ex:
                        print(f"  ✗ {lang}:{name}:{k}: {ex}")

        # preserve source order
        merged = []
        for e in entries:
            if e[key] in results:
                merged.append(results[e[key]])
            else:
                prev = next((p for p in keep if p[key] == e[key]), None)
                if prev:
                    merged.append(prev)
        wrapper = {"lang": lang, name if name != "glossary" else "terms": merged}
        out_path.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {out_path.name}: {len(merged)} entries ({len(results)} new)")
    return {"in": tin, "out": tout, "done": done}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["guides", "glossary", "seasons"], default=None)
    ap.add_argument("--langs", default="es,pt,de,fr")
    args = ap.parse_args()
    langs = [l.strip() for l in args.langs.split(",") if l.strip() in LANGS]

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠ ANTHROPIC_API_KEY not set — aborting")
        sys.exit(1)
    client = make_client()

    usage = {"in": 0, "out": 0, "done": 0}

    if args.only in (None, "guides"):
        guides = json.loads((SRC / "guides.json").read_text(encoding="utf-8"))["guides"]
        u = run_collection(client, "guides", guides, GUIDE_FIELDS, "slug", langs, None)
        for k in usage: usage[k] += u[k]

    if args.only in (None, "glossary"):
        gl = json.loads((SRC / "glossary.json").read_text(encoding="utf-8"))
        # glossary entries carry a see[0].label worth translating; do it via the same
        # structured call by folding label into the schema-free path: simplest is to
        # translate the four core fields and copy `see` as-is (label stays EN — the
        # linked tool pages are EN anyway).
        u = run_collection(client, "glossary", gl["terms"], TERM_FIELDS, "slug", langs, None)
        for k in usage: usage[k] += u[k]

    if args.only in (None, "seasons"):
        seasons = json.loads((SRC / "seasons.json").read_text(encoding="utf-8"))["seasons"]
        u = run_collection(client, "seasons", seasons, SEASON_FIELDS, "slug", langs, None)
        for k in usage: usage[k] += u[k]

    cost = usage["in"] / 1e6 * 1.0 + usage["out"] / 1e6 * 5.0
    print(f"\n✓ translated {usage['done']} entries · tokens {usage['in']}+{usage['out']} ≈ ${cost:.2f}")


if __name__ == "__main__":
    main()
