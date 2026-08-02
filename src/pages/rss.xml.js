// RSS feed: weekly recaps + today's top match previews. One more discovery
// channel for crawlers, rebuilt on every deploy.
import predictions from '../data/predictions.json';
import { getRecapWeeks } from '../lib/recap.js';
import { matchSlug } from '../lib/utils.js';

const SITE = 'https://ai-betting-tips.com';
const esc = (s) => String(s ?? '').replace(/[<>&'"]/g, (c) => ({
  '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;',
}[c]));

export async function GET() {
  const items = [];

  for (const w of getRecapWeeks().slice(-8).reverse()) {
    const s = w.stats;
    items.push({
      title: `Week ${w.week} ${w.isoYear} model results${s.settled ? `: ${s.won}W–${s.lost}L, ${s.profit > 0 ? '+' : ''}${s.profit.toFixed(2)}u` : ''}`,
      link: `${SITE}/news/recap/${w.slug}/`,
      date: new Date(w.monday + 'T08:00:00Z'),
      desc: `Full settled log for ${w.label}: every tip archived before kick-off and graded on the final score.`,
    });
  }

  const tips = [...(predictions.tips ?? [])]
    .sort((a, b) => (b.recommendation?.confidence ?? 0) - (a.recommendation?.confidence ?? 0))
    .slice(0, 15);
  for (const t of tips) {
    items.push({
      title: `${t.home} vs ${t.away}: prediction & best odds (${t.league})`,
      link: `${SITE}/predictions/${matchSlug(t)}/`,
      date: new Date(predictions.updated_at ?? Date.now()),
      desc: `Our tip: ${t.recommendation?.text} at ${Number(t.recommendation?.price ?? 0).toFixed(2)} — odds comparison, team form and head-to-head inside.`,
    });
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>AI Betting Tips</title>
<link>${SITE}/</link>
<description>Free football predictions, openly settled results and honest bookmaker reviews.</description>
<language>en</language>
${items.map((i) => `<item><title>${esc(i.title)}</title><link>${esc(i.link)}</link><guid>${esc(i.link)}</guid><pubDate>${i.date.toUTCString()}</pubDate><description>${esc(i.desc)}</description></item>`).join('\n')}
</channel></rss>`;

  return new Response(xml, { headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' } });
}
