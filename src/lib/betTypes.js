// Bet-type category pages. In a module (not page frontmatter) because Astro's
// getStaticPaths runs in isolation and can only see imports.
export const BET_TYPES = [
  { slug: 'accumulator', name: 'Accumulator Tips', emoji: '🎯', short: 'acca', long: 'daily accumulator (acca) tips combining several selections into one high-odds bet' },
  { slug: 'btts', name: 'BTTS Tips', emoji: '⚽', short: 'both teams to score', long: 'both teams to score (BTTS) predictions where we back goals at both ends' },
  { slug: 'over-under', name: 'Over/Under Goals Tips', emoji: '📊', short: 'over/under goals', long: 'over and under goals tips across the 1.5, 2.5 and 3.5 lines' },
  { slug: 'correct-score', name: 'Correct Score Tips', emoji: '🔢', short: 'correct score', long: 'high-odds correct score predictions for the exact final result' },
  { slug: 'double-chance', name: 'Double Chance Tips', emoji: '🛡️', short: 'double chance', long: 'lower-risk double chance tips covering two of the three outcomes' },
  { slug: 'draw', name: 'Draw Tips', emoji: '🤝', short: 'draw', long: 'value draw predictions for tight, evenly-matched fixtures' },
];
