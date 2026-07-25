import historyData from '../data/history.json';

// ── Weekly recap data: ISO weeks (Mon–Sun) built from the real settlement
//    archive. Only weeks that have already started get a page — future
//    fixture weeks from the odds feed are skipped until their Monday.
//    Lives in lib/ so getStaticPaths() can import it (frontmatter isolation).

const settledStates = ['won', 'lost', 'void'];

const TYPE_LABELS = {
  h2h: 'Match result (1X2)',
  totals: 'Over/Under totals',
  btts: 'Both teams to score',
  draw: 'Draw',
  'double-chance': 'Double chance',
};

function mondayOf(dateStr) {
  const d = new Date(dateStr + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7)); // Mon=0
  return d;
}

function isoWeekNum(monday) {
  const t = new Date(monday);
  t.setUTCDate(t.getUTCDate() + 3); // ISO week belongs to the year of its Thursday
  const isoYear = t.getUTCFullYear();
  const jan4 = new Date(Date.UTC(isoYear, 0, 4));
  const week1Mon = new Date(jan4);
  week1Mon.setUTCDate(jan4.getUTCDate() - ((jan4.getUTCDay() + 6) % 7));
  return { isoYear, week: Math.floor((t - week1Mon) / 604800000) + 1 };
}

const iso = (d) => d.toISOString().slice(0, 10);

function grade(list) {
  const settled = list.filter((h) => settledStates.includes(h.status));
  const graded = settled.filter((h) => h.status !== 'void');
  const won = graded.filter((h) => h.status === 'won').length;
  const profit = Math.round(settled.reduce((s, h) => s + (h.profit ?? 0), 0) * 100) / 100;
  return {
    tips: list.length,
    settled: settled.length,
    won,
    lost: graded.length - won,
    voided: settled.length - graded.length,
    profit,
    winRate: graded.length ? Math.round((won / graded.length) * 1000) / 10 : null,
    roi: graded.length ? Math.round((profit / graded.length) * 1000) / 10 : null,
  };
}

export function getRecapWeeks() {
  const real = Object.values(historyData.tips ?? {}).filter(
    (h) => h.score !== 'simulated' && !String(h.event_id ?? '').startsWith('mock')
  );
  const byMonday = {};
  for (const h of real) {
    const d = String(h.kickoff ?? '').slice(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) continue;
    (byMonday[iso(mondayOf(d))] ??= []).push(h);
  }
  const today = iso(new Date());

  return Object.keys(byMonday)
    .sort()
    .filter((m) => m <= today)
    .map((m) => {
      const monday = new Date(m + 'T00:00:00Z');
      const { isoYear, week } = isoWeekNum(monday);
      const sunday = new Date(monday);
      sunday.setUTCDate(sunday.getUTCDate() + 6);
      const entries = byMonday[m].sort((a, b) => String(a.kickoff).localeCompare(String(b.kickoff)));

      const days = [...Array(7)].map((_, i) => {
        const d = new Date(monday);
        d.setUTCDate(d.getUTCDate() + i);
        const date = iso(d);
        return { date, ...grade(entries.filter((h) => String(h.kickoff).slice(0, 10) === date)) };
      });

      const byGroup = (key) => {
        const g = {};
        for (const h of entries) (g[h[key] ?? '—'] ??= []).push(h);
        return Object.entries(g)
          .map(([k, list]) => ({ key: k, label: TYPE_LABELS[k] ?? k, ...grade(list) }))
          .sort((a, b) => b.settled - a.settled || b.tips - a.tips);
      };

      const fmt = (d) => d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
      return {
        slug: `${isoYear}-w${String(week).padStart(2, '0')}`,
        isoYear,
        week,
        monday: m,
        sunday: iso(sunday),
        label: `${fmt(monday)} – ${fmt(sunday)}, ${isoYear}`,
        inProgress: iso(sunday) >= today,
        entries,
        days,
        stats: grade(entries),
        byType: byGroup('type'),
        byLeague: byGroup('league'),
      };
    });
}
