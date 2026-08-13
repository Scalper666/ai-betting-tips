"""Translate the UI dictionary into overlay languages (Swahili, Hausa, Yoruba).

The FR overlay set the pattern: a flat {key: string} module that t() consults
before the 4-column dictionary. This script builds such overlays for any
language in TARGETS by feeding the EN strings to Haiku in batches, with the
same conventions as translate_static.py (placeholders, brands and numbers are
untouchable; every risk warning keeps its force).

Reads the dictionary via node (the JS module is the source of truth — parsing
it with regex would drift), caches per key+source-hash so re-runs only pay for
new or changed strings.

Usage:  python pipeline/translate_ui.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "src" / "i18n"
CACHE = ROOT / "data" / "ui-translations-cache.json"

MODEL = os.getenv("TRANSLATE_MODEL", "claude-haiku-4-5-20251001")
BATCH = 40
WORKERS = 4

TARGETS = {
    "sw": ("Swahili (Kenya/Tanzania standard; use the betting vocabulary East African "
           "bookmakers use — 'odds' commonly stays English, goals = 'mabao')"),
    "ha": ("Hausa (Nigeria/Niger, Boko/Latin script; betting terms as used by Nigerian "
           "bookmakers — English loanwords are fine where Hausa speakers use them)"),
    "yo": ("Yoruba (Nigeria, with correct diacritics; betting terms as actually used by "
           "Yoruba-speaking bettors — English loanwords are fine where natural)"),
    "ig": ("Igbo (Nigeria, standard orthography with diacritics; betting terms as used by "
           "Igbo-speaking bettors — English loanwords are fine where natural)"),
}

SYSTEM = (
    "You are a professional betting-industry translator. Translate each UI string of a "
    "sports-betting website into {language}. Hard rules: placeholders like {{n}}, {{home}}, "
    "{{away}}, {{score}}, {{fair}}, {{offered}} must appear UNCHANGED in the translation; "
    "keep numbers, odds, brand names ('AI Betting Tips', bookmaker names, 'BeGambleAware'), "
    "league names, '18+' and emoji exactly as-is; keep ⚠️/ⓘ/🕒 prefixes; risk warnings and "
    "disclaimers must keep their full force — never soften them; short labels must stay "
    "short (these fit buttons and table headers); translate idiomatically, not word-for-word. "
    "Return a JSON object mapping every given key to its translated string."
)


def node_dump() -> dict[str, str]:
    """{key: en_string} straight from the JS module."""
    js = (
        "const m = await import('./src/i18n/index.js');"
        "const out = {};"
        "for (const [k, v] of Object.entries(m.D)) if (v && typeof v.en === 'string') out[k] = v.en;"
        "console.log(JSON.stringify(out));"
    )
    r = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"node dump failed: {r.stderr[:400]}")
    return json.loads(r.stdout)


def client():
    import anthropic
    kwargs = {}
    if sys.platform == "win32":
        import ssl
        ctx = ssl.create_default_context()
        ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        kwargs["http_client"] = anthropic.DefaultHttpxClient(verify=ctx)
    return anthropic.Anthropic(**kwargs)


def translate_batch(cl, language: str, chunk: dict[str, str]) -> dict[str, str]:
    schema = {
        "type": "object",
        "properties": {k: {"type": "string"} for k in chunk},
        "required": list(chunk),
        "additionalProperties": False,
    }
    msg = cl.messages.create(
        model=MODEL, max_tokens=8000,
        system=SYSTEM.replace("{language}", language),
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": json.dumps(chunk, ensure_ascii=False)}],
    )
    if msg.stop_reason == "refusal":
        raise RuntimeError("model refused")
    return json.loads(next(b.text for b in msg.content if b.type == "text")), msg.usage


def main() -> int:
    src = node_dump()
    print(f"ключей EN: {len(src)}")
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}

    cl = client()
    tin = tout = 0
    for lang, language in TARGETS.items():
        done: dict[str, str] = {}
        todo: dict[str, str] = {}
        for k, en in src.items():
            h = hashlib.md5(en.encode()).hexdigest()[:10]
            hit = cache.get(f"{lang}:{k}")
            if hit and hit.get("h") == h:
                done[k] = hit["t"]
            else:
                todo[k] = en
        print(f"[{lang}] из кэша {len(done)}, переводить {len(todo)}")

        items = list(todo.items())
        chunks = [dict(items[i:i + BATCH]) for i in range(0, len(items), BATCH)]

        def work(ch):
            return translate_batch(cl, language, ch)

        with ThreadPoolExecutor(WORKERS) as ex:
            for res, usage in ex.map(work, chunks):
                for k, v in res.items():
                    done[k] = v
                    cache[f"{lang}:{k}"] = {"h": hashlib.md5(src[k].encode()).hexdigest()[:10], "t": v}
                tin += usage.input_tokens
                tout += usage.output_tokens

        # placeholder integrity: a lost {home} breaks pages silently
        import re
        bad = []
        for k, v in done.items():
            need = set(re.findall(r"\{[a-z]+\}", src[k]))
            if need - set(re.findall(r"\{[a-z]+\}", v)):
                bad.append(k)
                done[k] = src[k]          # fall back to EN rather than break
                cache.pop(f"{lang}:{k}", None)
        if bad:
            print(f"  ⚠ [{lang}] потеряны плейсхолдеры, оставлен EN: {bad[:8]}{'…' if len(bad) > 8 else ''}")

        body = ",\n".join(
            f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(done[k], ensure_ascii=False)}"
            for k in sorted(done)
        )
        (OUT_DIR / f"{lang}.js").write_text(
            f"// Generated by pipeline/translate_ui.py — edit via the cache, not by hand.\n"
            f"// Flat overlay, same contract as fr.js: t() reads this first, falls back to EN.\n"
            f"export const {lang.upper()} = {{\n{body},\n}};\n",
            encoding="utf-8")
        print(f"  ✓ src/i18n/{lang}.js: {len(done)} ключей")

    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    cost = tin / 1e6 * 1.0 + tout / 1e6 * 5.0
    print(f"✓ tokens {tin}+{tout} ≈ ${cost:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
