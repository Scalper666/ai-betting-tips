// ── Per-bet-type data for /tips/{type}.
// Every type page used to render the same six fixtures, which made them near
// duplicates of each other and of /predictions. These helpers give each page
// what is actually true for its market: the model's picks in that market where
// it makes them, our settled record in it, and — for markets the model does
// NOT price (BTTS, correct score, double chance) — real base rates from our
// results dataset instead of pretending we have picks.
import predictions from '../data/predictions.json';
import historyData from '../data/history.json';
import fdData from '../data/football-data.json';
import { leagueName } from './leagues.js';

const realTip = (h) => h.score !== 'simulated' && !String(h.event_id ?? '').startsWith('mock');
const soccer = (t) => String(t.sport_key ?? '').startsWith('soccer');

// Which live picks belong on a type page. Types absent from this map are
// markets we do not price — their pages lean on base-rate data instead.
// NB: live feed picks carry `side`/`text`, not the `outcome` field the
// settlement archive uses — a draw shows up as text "Draw" rather than
// outcome === 'Draw'. Matching on the archive's field silently returned
// nothing here.
const isDraw = (t) => {
  const r = t.recommendation ?? {};
  return r.type === 'h2h' && (r.side === 'Draw' || /\bdraw\b/i.test(String(r.text ?? '')));
};
const LIVE = {
  'over-under': (t) => t.recommendation?.type === 'totals',
  draw: isDraw,
  'match-result': (t) => t.recommendation?.type === 'h2h' && !isDraw(t),
};

export function picksForType(slug, limit = 6) {
  const f = LIVE[slug];
  if (!f) return [];
  return (predictions.tips ?? [])
    .filter((t) => soccer(t) && f(t))
    .sort((a, b) => (b.recommendation?.confidence ?? 0) - (a.recommendation?.confidence ?? 0))
    .slice(0, limit);
}

// Settled record in this market — the number no competitor publishes.
const HIST = {
  'over-under': (h) => h.type === 'totals',
  draw: (h) => h.type === 'h2h' && h.outcome === 'Draw',
  'match-result': (h) => h.type === 'h2h' && h.outcome !== 'Draw',
};

export function recordForType(slug) {
  const f = HIST[slug];
  if (!f) return null;
  const settled = Object.values(historyData.tips ?? {})
    .filter((h) => realTip(h) && f(h) && ['won', 'lost', 'void'].includes(h.status));
  if (!settled.length) return null;
  const won = settled.filter((h) => h.status === 'won').length;
  const lost = settled.filter((h) => h.status === 'lost').length;
  const profit = Math.round(settled.reduce((a, h) => a + (h.profit ?? 0), 0) * 100) / 100;
  const decided = won + lost;
  return {
    n: settled.length,
    won,
    lost,
    void: settled.length - decided,
    profit,
    roi: decided ? Math.round((profit / decided) * 1000) / 10 : null,
    winRate: decided ? Math.round((won / decided) * 1000) / 10 : null,
    early: decided < 30,
  };
}

// All finished matches we hold, across leagues.
function allResults() {
  const out = [];
  for (const [sk, lg] of Object.entries(fdData.leagues ?? {})) {
    const name = leagueName(sk, lg.name);
    for (const r of lg.results ?? []) {
      if (typeof r.hs === 'number' && typeof r.as === 'number') out.push({ ...r, league: name });
    }
  }
  return out;
}

// BTTS base rates per league — the honest content for a market we do not price.
export function bttsRates(minGames = 60) {
  const by = {};
  for (const r of allResults()) {
    const b = (by[r.league] ??= { league: r.league, n: 0, btts: 0 });
    b.n += 1;
    if (r.hs > 0 && r.as > 0) b.btts += 1;
  }
  return Object.values(by)
    .filter((b) => b.n >= minGames)
    .map((b) => ({ ...b, pct: Math.round((b.btts / b.n) * 1000) / 10 }))
    .sort((a, b) => b.pct - a.pct);
}

// Most frequent exact scorelines — the honest content for correct score.
export function commonScores(limit = 10) {
  const counts = new Map();
  let total = 0;
  for (const r of allResults()) {
    const key = `${r.hs}-${r.as}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
    total += 1;
  }
  const rows = [...counts.entries()]
    .map(([score, n]) => ({
      score,
      n,
      pct: Math.round((n / total) * 1000) / 10,
      fair: Math.round((total / n) * 100) / 100,   // fair decimal odds at this rate
    }))
    .sort((a, b) => b.n - a.n)
    .slice(0, limit);
  return { rows, total };
}

// Home / draw / away split — the base rate behind double chance.
export function outcomeSplit() {
  const rows = allResults();
  const n = rows.length;
  if (!n) return null;
  const home = rows.filter((r) => r.hs > r.as).length;
  const draw = rows.filter((r) => r.hs === r.as).length;
  const away = n - home - draw;
  const pc = (x) => Math.round((x / n) * 1000) / 10;
  return {
    n,
    home: pc(home),
    draw: pc(draw),
    away: pc(away),
    // double chance base rates follow directly
    homeOrDraw: pc(home + draw),
    awayOrDraw: pc(away + draw),
    homeOrAway: pc(home + away),
  };
}

// Accumulator legs: highest-confidence picks from distinct fixtures, priced in
// a range where combining is at least defensible (see /tools/acca-builder).
export function accaLegs(count = 3) {
  const seen = new Set();
  const legs = [];
  for (const t of [...(predictions.tips ?? [])]
    .filter((t) => soccer(t) && Number(t.recommendation?.price) >= 1.3 && Number(t.recommendation?.price) <= 2.2)
    .sort((a, b) => (b.recommendation?.confidence ?? 0) - (a.recommendation?.confidence ?? 0))) {
    const key = `${t.home}|${t.away}`;
    if (seen.has(key)) continue;
    seen.add(key);
    legs.push(t);
    if (legs.length >= count) break;
  }
  return legs;
}
