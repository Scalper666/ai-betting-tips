// ── System-bet definitions for /tools/{slug} calculator pages.
//    parts: [k, count] = how many k-fold combinations the system contains for
//    n selections (count = C(n,k)); singles flag says whether 1-folds are in.
//    Lives here because getStaticPaths is frontmatter-isolated.
export const SYSTEMS = [
  { slug: 'trixie-calculator', name: 'Trixie', n: 3, singles: false, bets: 4,
    blurb: '3 selections: 3 doubles and 1 treble — 4 bets. Two winners already return something.',
    glossary: 'trixie' },
  { slug: 'patent-calculator', name: 'Patent', n: 3, singles: true, bets: 7,
    blurb: '3 selections: 3 singles, 3 doubles and 1 treble — 7 bets. One winner already returns something.',
    glossary: 'patent' },
  { slug: 'yankee-calculator', name: 'Yankee', n: 4, singles: false, bets: 11,
    blurb: '4 selections: 6 doubles, 4 trebles and 1 four-fold — 11 bets.',
    glossary: 'yankee' },
  { slug: 'lucky-15-calculator', name: 'Lucky 15', n: 4, singles: true, bets: 15,
    blurb: '4 selections: 4 singles, 6 doubles, 4 trebles and 1 four-fold — 15 bets.',
    glossary: 'lucky-15' },
  { slug: 'canadian-calculator', name: 'Canadian', n: 5, singles: false, bets: 26,
    blurb: '5 selections: 10 doubles, 10 trebles, 5 four-folds and 1 five-fold — 26 bets. Also called a Super Yankee.',
    glossary: 'system-bet' },
  { slug: 'lucky-31-calculator', name: 'Lucky 31', n: 5, singles: true, bets: 31,
    blurb: '5 selections: 5 singles plus every double, treble, four-fold and the five-fold — 31 bets.',
    glossary: 'system-bet' },
  { slug: 'heinz-calculator', name: 'Heinz', n: 6, singles: false, bets: 57,
    blurb: '6 selections: 15 doubles, 20 trebles, 15 four-folds, 6 five-folds and 1 six-fold — 57 bets.',
    glossary: 'system-bet' },
  { slug: 'lucky-63-calculator', name: 'Lucky 63', n: 6, singles: true, bets: 63,
    blurb: '6 selections: 6 singles plus the full Heinz — 63 bets.',
    glossary: 'system-bet' },
  { slug: 'super-heinz-calculator', name: 'Super Heinz', n: 7, singles: false, bets: 120,
    blurb: '7 selections: every double through to the seven-fold — 120 bets.',
    glossary: 'system-bet' },
  { slug: 'goliath-calculator', name: 'Goliath', n: 8, singles: false, bets: 247,
    blurb: '8 selections: every double through to the eight-fold — 247 bets.',
    glossary: 'system-bet' },
];

const C = (n, k) => {
  let r = 1;
  for (let i = 0; i < k; i++) r = (r * (n - i)) / (i + 1);
  return Math.round(r);
};

/** [{k, count}] rows for the structure table. */
export const systemParts = (sys) => {
  const rows = [];
  for (let k = sys.singles ? 1 : 2; k <= sys.n; k++) rows.push({ k, count: C(sys.n, k) });
  return rows;
};

export const FOLD_NAME = { 1: 'Singles', 2: 'Doubles', 3: 'Trebles', 4: 'Four-folds', 5: 'Five-folds', 6: 'Six-folds', 7: 'Seven-folds', 8: 'Eight-fold' };
