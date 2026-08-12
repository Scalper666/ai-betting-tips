import predictions from '../data/predictions.json';
import historyData from '../data/history.json';
import registry from '../data/match-registry.json';
import { matchSlug, slugify } from './utils.js';

// Path set for match pages: CURRENT feed ∪ SETTLEMENT ARCHIVE ∪ REGISTRY.
// The registry (pipeline/match_registry.py, committed with the snapshot) is
// what makes "a match page never dies" actually true: the settlement archive
// only holds OFFICIAL picks, so model-lean fixtures used to 404 the moment
// the feed dropped their matchday — Search Console logged 49 of those.
// Shared by the EN route and the [lang] routes (frontmatter isolation:
// getStaticPaths can only see imports).
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

  const reg = registry.matches ?? {};
  const slugs = new Set([...live.keys(), ...Object.keys(bySlug), ...Object.keys(reg)]);
  return [...slugs].map((slug) => ({
    params: { slug },
    props: {
      tip: live.get(slug) ?? null,
      archive: (bySlug[slug] ?? []).sort((a, b) => String(b.kickoff ?? '').localeCompare(String(a.kickoff ?? ''))),
      reg: reg[slug] ?? null,
    },
  }));
}
