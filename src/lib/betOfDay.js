import predictions from '../data/predictions.json';

// ── Bet of the day.
//
// The selection rule is deliberately not a new one. The site already defines
// "official": a pick is only published as official when the model/market blend
// clears the best available price by a set margin, and only official picks are
// archived and settled. So the strongest bet on the board is simply the
// best-rated official pick — confidence first, edge as the tie-break.
//
// Scoped to the earliest day that still has an official pick rather than to the
// literal calendar date: the build runs twice daily, and by the evening run
// today's fixtures may all have kicked off. Better to show tomorrow's pick than
// an empty page.
//
// Returns null when nothing qualifies at all. Roughly three quarters of
// fixtures never produce an official pick, so a quiet day is a real outcome and
// the page says so instead of promoting something the model never endorsed.

const TIPS = Array.isArray(predictions) ? predictions : predictions.tips ?? [];

// edge_pct is (fair_prob × price − 1) × 100, so the model's own price for the
// outcome falls straight out of the published numbers — no second source, and
// the reader can check the arithmetic.
export const fairOdds = (price, edgePct) => price / (1 + Number(edgePct) / 100);

const dayKey = (iso) => String(iso ?? '').slice(0, 10);

export function betOfTheDay(now = new Date()) {
  const upcoming = TIPS.filter((t) => {
    const r = t.recommendation;
    if (!r?.official) return false;
    const k = Date.parse(t.kickoff);
    return Number.isFinite(k) && k > now.getTime();
  });
  if (!upcoming.length) return null;

  const day = upcoming.map((t) => dayKey(t.kickoff)).sort()[0];
  const sameDay = upcoming.filter((t) => dayKey(t.kickoff) === day);

  sameDay.sort(
    (a, b) =>
      (b.recommendation.confidence ?? 0) - (a.recommendation.confidence ?? 0) ||
      (b.recommendation.edge_pct ?? 0) - (a.recommendation.edge_pct ?? 0)
  );

  const pick = sameDay[0];
  return {
    tip: pick,
    day,
    // the runners-up give the page somewhere to go on a day when the top pick
    // does not suit the reader, without pretending they are equally rated
    others: sameDay.slice(1, 4),
    officialToday: sameDay.length,
  };
}
