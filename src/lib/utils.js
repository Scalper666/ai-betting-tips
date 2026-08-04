// Build timestamp — evaluated once per build, so data-driven pages can state
// (and mark up) when their odds/standings/results were last refreshed. CI
// rebuilds twice a day, so this is a truthful "last updated" for those pages.
export const BUILD_ISO = new Date().toISOString();

// Short human date for "updated" lines. Locale-aware, day-month-year order.
export const fmtDate = (iso, lang = 'en') => {
  const d = new Date(iso);
  return isNaN(d) ? '' : d.toLocaleDateString(lang, { day: 'numeric', month: 'short', year: 'numeric' });
};

export function slugify(s) {
  return String(s ?? '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export const matchSlug = (tip) => slugify(`${tip.home}-vs-${tip.away}`);

export function abbr(name) {
  const w = String(name ?? '').split(/[\s.]+/).filter(Boolean);
  if (w.length >= 2) return (w[0][0] + w[1][0] + (w[2] ? w[2][0] : '')).toUpperCase().slice(0, 3);
  return String(name ?? '').slice(0, 3).toUpperCase();
}

const PALETTE = ['#db0007', '#132257', '#a50044', '#004170', '#dc052d', '#003366',
                 '#e32219', '#6caddf', '#ef0107', '#7b1fa2', '#0a8f5b', '#1a4ea3'];
export const badgeColor = (name) =>
  PALETTE[[...String(name ?? '')].reduce((a, c) => a + c.charCodeAt(0), 0) % PALETTE.length];

export function confidenceLabel(c) {
  if (c >= 75) return { label: 'High', cls: '' };
  if (c >= 62) return { label: 'Medium', cls: 'gold' };
  return { label: 'Value', cls: 'violet' };
}

export function avgScore(scores) {
  const v = Object.values(scores ?? {});
  return v.length ? +(v.reduce((a, b) => a + b, 0) / v.length).toFixed(1) : 0;
}

export const SCORE_LABELS = {
  odds: 'Odds & margins',
  markets: 'Market depth',
  payout: 'Payout speed',
  app: 'Mobile app',
  bonus: 'Bonus value',
  support: 'Support & trust',
};

export const CASINO_SCORE_LABELS = {
  games: 'Game selection',
  live: 'Live casino',
  payout: 'Payout speed',
  bonus: 'Bonus value',
  app: 'Mobile experience',
  safety: 'Safety & licensing',
};

export const AVATAR_STYLES = [
  'background:linear-gradient(135deg,#fcd535,#f0b90b);color:#0b0e11',
  'background:linear-gradient(135deg,#ff8a5c,#ff5c8a)',
  'background:linear-gradient(135deg,#3ad,#27e)',
  'background:linear-gradient(135deg,#b06cff,#7b3cff)',
  'background:linear-gradient(135deg,#5ce0d6,#2cab9e);color:#04221a',
];

export const signed = (v) => `${v >= 0 ? '+' : ''}${v}`;

const KICKOFF_WORDS = {
  en: ['Today', 'Tomorrow', 'en-GB'],
  es: ['Hoy', 'Mañana', 'es-ES'],
  pt: ['Hoje', 'Amanhã', 'pt-BR'],
  de: ['Heute', 'Morgen', 'de-DE'],
  fr: ["Aujourd'hui", 'Demain', 'fr-FR'],
};

export function kickoffLabel(iso, lang = 'en') {
  if (!iso) return 'TBD';
  const d = new Date(iso);
  if (isNaN(d)) return 'TBD';
  const [today, tomorrow, tag] = KICKOFF_WORDS[lang] ?? KICKOFF_WORDS.en;
  const t = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  const days = Math.round((new Date(d).setHours(0, 0, 0, 0) - new Date().setHours(0, 0, 0, 0)) / 86400000);
  if (days <= 0) return `${today} · ${t}`;
  if (days === 1) return `${tomorrow} · ${t}`;
  return `${d.toLocaleDateString(tag, { weekday: 'short' })} · ${t}`;
}

// FAQPage JSON-LD from [{q, a}] — merged into each page's schema graph
export const faqSchema = (faqs) => ({
  '@type': 'FAQPage',
  mainEntity: (faqs ?? []).map((f) => ({
    '@type': 'Question',
    name: f.q,
    acceptedAnswer: { '@type': 'Answer', text: f.a },
  })),
});
