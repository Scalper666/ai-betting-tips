// ── "X odds" accumulator pages: /tips/2-odds, /tips/3-odds, /tips/5-odds,
//    /tips/10-odds. In our biggest markets (Nigeria, Kenya, Ghana) people
//    search for a slip by its combined price — "2 odds daily", "sure 3 odds",
//    "5 odds tips", "10 odds" — not by market. Each page builds ONE slip from
//    the screener's model-rated picks: the combination nearest the target price
//    with the highest model hit chance, and it prints that chance instead of
//    calling anything "sure".
import screener from '../data/screener.json';
import historyData from '../data/history.json';
import { matchSlug } from './utils.js';

// per-leg price window — same rule as /tools/acca-builder: below 1.20 a leg
// adds margin without moving the price, above 3.00 the model's edge is unproven
export const LEG_MIN = 1.2;
export const LEG_MAX = 3.0;
const POOL = 14;                 // top-rated candidates searched per slip
const HORIZON_H = 48;            // "daily" = kick-offs within two days
const HORIZON_WIDE_H = 24 * 7;   // fallback when the feed is thin (int'l breaks)

export const BRACKETS = [
  {
    slug: '2-odds', target: 2, minLegs: 1, maxLegs: 3, emoji: '2️⃣', name: '2 Odds',
    tile: 'Two or three short-priced legs that double the stake — the banker-style slip',
    intro: 'A 2 odds slip is the "banker" of accumulator betting: two or three short-priced selections that together roughly double your stake. Ours is rebuilt twice a day from the model\'s highest-rated picks, and instead of promising it is sure, the page tells you how often a slip like this should actually land.',
    how: 'The builder takes the screener\'s top-rated football picks priced 1.20–3.00, one per match, and searches every two- and three-leg combination for the one that lands on or just above 2.00 with the highest combined model probability. Short prices win that search by design — a 2 odds slip is meant to be the safest product on this site, not the most exciting.',
    faq: [
      { q: 'What does "2 odds" mean?', a: 'It means the combined decimal price of the slip is about 2.00, so a winning bet returns roughly double the stake (stake plus an equal profit). It is usually built from two or three selections priced between 1.20 and 1.50 rather than from one even-money pick.' },
      { q: 'Are these sure 2 odds?', a: 'No — there is no such thing as sure odds, and any site selling "sure 2 odds" is selling a feeling. Two legs at a genuine 75% each land together about 56% of the time; that is the honest ceiling for a slip like this, and our settled singles record on this page shows what our own picks actually do at these prices.' },
      { q: 'How is the daily 2 odds slip chosen?', a: 'From the model\'s own rated picks, not from a tipster\'s hunch: the screener rates every fixture by the gap between the model\'s probability and the best available price, and the slip is the two- or three-leg combination nearest 2.00 with the highest model hit chance. It is re-priced at every refresh, twice a day.' },
      { q: 'When is it updated?', a: 'The site rebuilds around 05:30 and 16:30 UTC. The slip only ever includes matches that have not kicked off, so after the evening refresh it typically points at tomorrow\'s early fixtures.' },
      { q: 'Should I stake more on a 2 odds slip because it is "safer"?', a: 'Stake flat and small on every slip you place. A 2 odds slip loses at least a third of the time even when the picks are good; a staking plan that survives a five-slip losing run is what separates a hobby from a hole.' },
    ],
  },
  {
    slug: '3-odds', target: 3, minLegs: 2, maxLegs: 4, emoji: '3️⃣', name: '3 Odds',
    tile: 'Three-ish legs that treble the stake — the everyday accumulator',
    intro: 'A 3 odds slip is the everyday accumulator: three or four selections whose combined price sits around 3.00, paying about twice the stake in profit. Ours is built twice a day from the model\'s highest-rated picks, with the model\'s own hit chance printed next to it — the number every "sure 3 odds" page leaves out.',
    how: 'Candidates are the screener\'s top-rated football picks priced 1.20–3.00, one per match. Every two-, three- and four-leg combination is scored and the slip nearest 3.00 with the highest combined model probability wins. That usually means three legs around 1.40–1.50 rather than one long shot, because three moderate favourites land far more often than one outsider at the same combined price.',
    faq: [
      { q: 'What does "3 odds" mean?', a: 'A slip whose combined decimal price is about 3.00: a winning bet returns three times the stake, i.e. the stake back plus twice the stake in profit. Three selections around 1.44 each multiply to roughly 3.00.' },
      { q: 'Are these sure 3 odds?', a: 'No. Three legs at a genuine 70% each land together only about 34% of the time — roughly one slip in three. We publish that figure for the exact slip on the page because the alternative is pretending, and our settled singles record shows how our picks actually perform at these prices.' },
      { q: 'Why not one 3.00 pick instead of three legs?', a: 'Because our own first model version lost eight straight on outsiders: betting markets overprice longshots, so a single 3.00 selection is usually worse value than three moderate favourites at the same combined price. The margin you pay per leg is the cost of that trade, and it is shown on the slip.' },
      { q: 'How often is the 3 odds slip updated?', a: 'Twice a day, around 05:30 and 16:30 UTC, and it only includes fixtures that have not started. Check the prices before you place it — a leg that has drifted past the model\'s fair value no longer belongs on the slip.' },
      { q: 'Can I add my own leg to the slip?', a: 'Use the AI acca builder: it starts from the same rated picks, lets you toggle legs and shows the combined price and the model\'s hit chance as you go. Adding a leg you have not priced is how a 3 odds slip quietly becomes a 6 odds lottery ticket.' },
    ],
  },
  {
    slug: '5-odds', target: 5, minLegs: 3, maxLegs: 5, emoji: '5️⃣', name: '5 Odds',
    tile: 'Four or five legs paying five times the stake — the weekend slip',
    intro: 'A 5 odds slip is the weekend accumulator: four or five selections whose combined price is about 5.00. It pays well and it loses more often than it wins — our page says so in numbers, and builds the slip from the model\'s rated picks rather than from the longest prices on the coupon.',
    how: 'Candidates are the screener\'s top-rated football picks priced 1.20–3.00, one per match. Every combination of three to five legs is scored and the slip nearest 5.00 with the highest combined model probability is chosen. At this target the search almost always prefers four or five short legs over two long ones, because that is what keeps the hit chance above lottery territory.',
    faq: [
      { q: 'What does "5 odds" mean?', a: 'A slip with a combined decimal price around 5.00: a winning bet returns five times the stake. Four selections at about 1.50 each, or five at about 1.38, multiply to roughly 5.00.' },
      { q: 'Are these sure 5 odds?', a: 'No, and a 5 odds slip cannot be: even four legs at a genuine 70% each land together only about 24% of the time — one slip in four. The page prints the model\'s hit chance for the exact slip and the settled record of our singles at these prices, so you can see the real odds behind the odds.' },
      { q: 'How much bookmaker margin is baked into a 5 odds acca?', a: 'Each leg carries the bookmaker\'s margin and an accumulator multiplies them. Four legs at a typical 5% margin cost about 19% of fair value before kick-off; five legs about 23%. That is why accas are the most profitable product on any betting menu — for the bookmaker.' },
      { q: 'Is a 5 odds slip a good bet?', a: 'It is a high-variance bet with a known cost. If every leg is a genuine value pick it can have a positive expected value, but the results arrive in long losing runs broken by occasional wins. Stake accordingly and judge it over dozens of slips, never one Saturday.' },
      { q: 'When does the slip refresh?', a: 'Twice daily, around 05:30 and 16:30 UTC, always from fixtures that have not kicked off. Prices move between refreshes; the acca builder lets you re-check the slip leg by leg.' },
    ],
  },
  {
    slug: '10-odds', target: 10, minLegs: 4, maxLegs: 6, emoji: '🔟', name: '10 Odds',
    tile: 'Five or six legs paying ten times the stake — the big-ticket slip',
    intro: 'A 10 odds slip is the big-ticket accumulator: five or six selections multiplying to about 10.00. Ours is built from the model\'s rated picks and comes with the one number every "sure 10 odds" page hides — how often a slip like this should land. Spoiler: not often, and the page treats you like an adult about it.',
    how: 'Candidates are the screener\'s top-rated football picks priced 1.20–3.00, one per match. Every combination of four to six legs is scored and the slip nearest 10.00 with the highest combined model probability wins. Even the best version of this slip is a low-probability bet — the page exists to make that probability visible, not to sell the dream.',
    faq: [
      { q: 'What does "10 odds" mean?', a: 'A slip whose combined decimal price is about 10.00, returning ten times the stake when every leg wins. Six selections at about 1.47 each, or five at about 1.58, multiply to roughly 10.00.' },
      { q: 'Are these sure 10 odds?', a: 'No — and at this price the word "sure" is simply false advertising. Six legs at a genuine 70% each land together about 12% of the time, roughly one slip in eight. The model\'s hit chance for the exact slip is printed on the page, alongside the settled record of our singles at these prices.' },
      { q: 'How much does the bookmaker margin cost on a 10 odds acca?', a: 'Six legs at a typical 5% margin each bake in about 26% of combined margin before kick-off. Nothing about model ratings changes that arithmetic; what the ratings do is make sure the legs are at least positive-value on their own.' },
      { q: 'Is a 10 odds accumulator ever worth it?', a: 'As entertainment with a known price, staked small — yes. As a plan to make money — no. Singles preserve far more of whatever edge exists; every added leg multiplies the margin against you. We publish this slip because people search for it, and we would rather they see the honest numbers here than the "sure" version elsewhere.' },
      { q: 'When is the 10 odds slip updated?', a: 'Twice daily, around 05:30 and 16:30 UTC, from fixtures that have not started. If the feed cannot supply enough rated picks to reach 10.00 within the price rules, the page says so instead of padding the slip with unrated legs.' },
    ],
  },
];

const realTip = (h) => h.score !== 'simulated' && !String(h.event_id ?? '').startsWith('mock');

// Top-rated screener picks that can go on a slip: football, priced inside the
// leg window, one per fixture, kicking off within the horizon.
export function candidates(nowIso, horizonHours = HORIZON_H) {
  const now = Date.parse(nowIso);
  const horizon = now + horizonHours * 3600e3;
  const seen = new Set();
  const out = [];
  // edge > 0 keeps every leg positive-value on the model's own numbers, so
  // the slip's expected value is positive by construction (a product of
  // factors above 1) — the only version of an acca worth publishing
  const rows = [...(screener.rows ?? [])]
    .filter((r) => r.sport === 'Football' && Number(r.odds) >= LEG_MIN && Number(r.odds) <= LEG_MAX
      && Number(r.confidence) > 0 && Number(r.edge) > 0)
    .sort((a, b) => b.score - a.score);
  for (const r of rows) {
    const k = Date.parse(r.kickoff);
    if (isNaN(k) || k < now || k > horizon) continue;
    const key = `${r.home}|${r.away}`;
    if (seen.has(key)) continue;
    seen.add(key);
    // leg probability implied by the model's fair price, i.e. the same number
    // the edge is quoted against everywhere on the site. (The screener's
    // `confidence` diverges on whole-line totals such as Under 3.0, where a
    // push refunds the stake — fair price accounts for that, confidence not.)
    const odds = Number(r.odds);
    out.push({
      home: r.home, away: r.away, league: r.league, kickoff: r.kickoff, market: r.market,
      odds, score: r.score, edge: r.edge, icon: r.icon ?? '⚽',
      p: Math.min(0.97, Math.max(0.02, (1 + Number(r.edge) / 100) / odds)),
      href: `/predictions/${matchSlug(r)}`,
    });
    if (out.length >= POOL) break;
  }
  return out;
}

// The slip: the leg combination inside [lo, hi] with the highest combined
// model probability; fewer legs break ties. Exhaustive over the pool — at most
// a few thousand combinations, fine at build time.
function search(pool, bracket, lo, hi) {
  let best = null;
  const rec = (start, chosen, odds, p) => {
    if (chosen.length >= bracket.minLegs && odds >= lo && odds <= hi) {
      if (!best || p > best.p || (p === best.p && chosen.length < best.legs.length)) best = { legs: [...chosen], odds, p };
    }
    if (chosen.length === bracket.maxLegs) return;
    for (let i = start; i < pool.length; i++) {
      const o = odds * pool[i].odds;
      if (o > hi) continue;
      chosen.push(pool[i]);
      rec(i + 1, chosen, o, p * pool[i].p);
      chosen.pop();
    }
  };
  rec(0, [], 1, 1);
  return best;
}

// Price windows tried in order, on target first: a "2 odds" slip at 3.0 is a
// different product to the person searching, so a slip that lands on target
// with a Friday leg beats one that misses it with tonight's fixtures.
const TIERS = [[1, 1.2], [1, 1.35], [0.9, 1.45]];

export function buildSlip(bracket, nowIso) {
  const pools = [candidates(nowIso), candidates(nowIso, HORIZON_WIDE_H)];
  let slip = null;
  let pool = pools[0];
  outer: for (const [lo, hi] of TIERS) {
    for (const p of pools) {
      const s = search(p, bracket, bracket.target * lo, bracket.target * hi);
      if (s) { slip = s; pool = p; break outer; }
    }
  }
  if (!slip) return null;
  const legs = [...slip.legs].sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff));
  return {
    legs,
    odds: Math.round(slip.odds * 100) / 100,
    p: slip.p,
    fair: Math.round((1 / slip.p) * 100) / 100,   // price the model thinks the slip is worth
    poolSize: pool.length,
    firstKick: legs[0].kickoff,
    lastKick: legs[legs.length - 1].kickoff,
  };
}

// Settled singles by price band from the public record — the only honest
// basis for "how often does a leg like this win". Draws on real, non-mock
// settlements only (the same filter the results pages use).
export function singlesRecord() {
  const settled = Object.values(historyData.tips ?? {})
    .filter((h) => realTip(h) && (h.status === 'won' || h.status === 'lost'));
  const band = (lo, hi) => {
    const rows = settled.filter((h) => Number(h.odds) >= lo && Number(h.odds) < hi);
    const won = rows.filter((h) => h.status === 'won').length;
    return { lo, hi, n: rows.length, won, rate: rows.length ? won / rows.length : null };
  };
  return {
    bands: [band(1.2, 1.5), band(1.5, 2.0), band(2.0, 3.01)],
    all: band(LEG_MIN, LEG_MAX + 0.01),
  };
}
