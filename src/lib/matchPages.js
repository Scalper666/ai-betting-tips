import predictions from '../data/predictions.json';
import historyData from '../data/history.json';
import { matchSlug, slugify } from './utils.js';

// Path set for match pages: CURRENT feed ∪ SETTLEMENT ARCHIVE — a match page
// never dies. Shared by the EN route and the [lang] routes (frontmatter
// isolation: getStaticPaths can only see imports).
export function buildMatchPaths() {
  const tips = predictions.tips ?? [];
  const live = new Map(tips.map((t) => [matchSlug(t), t]));

  const bySlug = {};
  for (const h of Object.values(historyData.tips ?? {})) {
    if (h.score === 'simulated' || String(h.event_id ?? '').startsWith('mock')) continue;
    if (!h.home || !h.away) continue;
    const slug = slugify(`${h.home}-vs-${h.away}`);
    (bySlug[slug] ??= []).push(h);
  }

  const slugs = new Set([...live.keys(), ...Object.keys(bySlug)]);
  return [...slugs].map((slug) => ({
    params: { slug },
    props: {
      tip: live.get(slug) ?? null,
      archive: (bySlug[slug] ?? []).sort((a, b) => String(b.kickoff ?? '').localeCompare(String(a.kickoff ?? ''))),
    },
  }));
}
