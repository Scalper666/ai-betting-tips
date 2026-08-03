// Edge geo-block (Cloudflare Pages Functions). Countries where promoting
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
]);

export async function onRequest(context) {
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
