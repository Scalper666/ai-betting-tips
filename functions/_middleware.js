// Edge middleware (Cloudflare Pages Functions): redirect table, geo-block and
// the www canonical, applied at the CDN before any page is served.
//
// The redirects live here rather than in _redirects because Cloudflare only
// honours roughly the first 100 entries of that file on our plan — we have 600+,
// and the ones past the cap silently did nothing for weeks (GSC kept failing its
// 404 validation while the file looked complete). A Map has no such limit.
// Regenerate redirects.json with scratchpad/mkredirects.py.
import REDIRECTS from './redirects.json';

// Edge geo-block. Countries where promoting
// offshore betting is actively prosecuted get HTTP 451 instead of the site.
// Runs at the CDN before any page is served; Googlebot (US) is unaffected.
// Edit BLOCKED to adjust policy.
const BLOCKED = new Set([
  'TR', // Turkey — state monopoly, promotion prosecuted
  'TH', // Thailand — gambling illegal
  'VN', // Vietnam — gambling illegal
  'ID', // Indonesia — gambling illegal
  'PK', // Pakistan — gambling illegal
  'BD', // Bangladesh — gambling illegal
  'KZ', // Kazakhstan — licensed-local-only market, offshore promotion banned
  'AE', // UAE — gambling promotion criminalised; sports betting unlicensed
  'SG', // Singapore — Remote Gambling Act criminalises offshore betting and its promotion
  'KH', // Cambodia — online betting banned by 2019 decree
  'NP', // Nepal — betting prohibited for citizens, promoters prosecuted
]);

export async function onRequest(context) {
  // canonical host: www serves the same Pages project — fold it into the apex
  // with a 301 so Google stops crawling a full duplicate mirror
  const url = new URL(context.request.url);
  if (url.hostname === 'www.ai-betting-tips.com') {
    url.hostname = 'ai-betting-tips.com';
    return Response.redirect(url.toString(), 301);
  }
  // exact-match redirect table (slug migrations, retired family parents)
  const path = url.pathname.replace(/\/+$/, '') || '/';
  // Pages serves directory pages at /x/ and 308s /x -> /x/; a redirect to the
  // slash-less form therefore costs Googlebot TWO hops. Land on /x/ directly.
  const slashed = (p) => (p.endsWith('/') || /\.[a-z0-9]+$/i.test(p) || p.startsWith('/api/') ? p : p + '/');
  const target = REDIRECTS[path];
  if (target) {
    const dest = new URL(slashed(target), url.origin);
    dest.search = url.search;
    return Response.redirect(dest.toString(), 301);
  }

  // Retired families, folded into EN with a 301 (one hop, slash form):
  //  - per-match pages in every non-EN edition (compact editions on
  //    2026-09-02, es/pt/de/fr on 2026-09-19 — see MATCH_LANGS in src/i18n).
  //    Hub pages (/xx/predictions, today, tomorrow, weekend, daily) still exist.
  //  - every localized h2h page (hub, league hubs, pairs) — 2026-09-19.
  const LANGS = 'es|pt|de|fr|am|yo|ig|ha|sw';
  const retired = path.match(new RegExp(`^/(${LANGS})/predictions/(?!daily(/|$)|today$|tomorrow$|weekend$)([^/]+)$`))
    || path.match(new RegExp(`^/(${LANGS})/h2h(/.*)?$`));
  if (retired) {
    const rest = retired[0].startsWith(`/${retired[1]}/h2h`) ? `/h2h${retired[2] ?? ''}` : `/predictions/${retired[3]}`;
    const dest = new URL(slashed(rest), url.origin);
    dest.search = url.search;
    return Response.redirect(dest.toString(), 301);
  }

  const country = context.request.cf?.country;
  if (country && BLOCKED.has(country)) {
    return new Response(
      `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Not available</title>
<meta name="robots" content="noindex"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{background:#0f1720;color:#9cadbe;font:15px/1.6 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;text-align:center;padding:24px}b{color:#fff}</style>
</head><body><div><b>451 — Unavailable for legal reasons</b><br>
This service is not available in your country due to local regulations on betting-related content.</div></body></html>`,
      { status: 451, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } }
    );
  }
  return context.next();
}
