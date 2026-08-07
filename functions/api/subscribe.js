// Newsletter signup endpoint (Cloudflare Pages Function).
//
// Storage is a KV namespace bound as SUBSCRIBERS. The binding cannot be created
// from the repo — see DEPLOY.md — so the handler refuses loudly when it is
// missing rather than accepting an address it has nowhere to put. Dropping
// signups silently is the one failure mode that must not happen here.
//
// Addresses are stored one key per subscriber so a duplicate signup overwrites
// itself instead of growing the list, and so a single unsubscribe is a single
// delete.

const EMAIL = /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i;

const json = (status, body) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.SUBSCRIBERS) return json(503, { ok: false, error: 'not_configured' });

  let data;
  try {
    data = await request.json();
  } catch {
    return json(400, { ok: false, error: 'bad_request' });
  }

  // Honeypot: a field hidden from people, irresistible to form bots. Answer 200
  // so the bot records a success and does not retry with a different shape.
  if (data.company) return json(200, { ok: true });

  const email = String(data.email ?? '').trim().toLowerCase();
  if (!EMAIL.test(email) || email.length > 254) return json(400, { ok: false, error: 'bad_email' });
  if (data.consent !== true) return json(400, { ok: false, error: 'consent_required' });

  const key = `sub:${email}`;
  const existing = await env.SUBSCRIBERS.get(key);
  if (existing) return json(200, { ok: true, already: true });

  await env.SUBSCRIBERS.put(
    key,
    JSON.stringify({
      email,
      at: new Date().toISOString(),
      // country is the only other thing we keep, and only to know which
      // markets the list is coming from — no IP, no fingerprint
      country: request.cf?.country ?? null,
      source: String(data.source ?? '').slice(0, 40),
    })
  );

  return json(200, { ok: true });
}
// Only POST is exported on purpose: Pages answers 405 for every other method
// on its own, and adding an onRequest catch-all here would shadow this handler.
