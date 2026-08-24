// ── Single source of truth for tool navigation (header dropdown + ToolsBox).
//    These two surfaces drifted out of sync when the calculator family grew —
//    now they both render this list. `key` is an i18n label; `label` is a
//    proper noun that needs no translation (system-bet names).
export const NAV_TOOLS = [
  { href: '/tools/acca-builder', icon: '🤖', key: 'ft.accaBuilder' },
  { href: '/tools/odds-converter', icon: '🔁', key: 'ft.oddsConverter' },
  { href: '/tools/ev-calculator', icon: '⚖️', key: 'ft.evCalc' },
  { href: '/tools/no-vig-calculator', icon: '🧾', key: 'ft.noVig' },
  { href: '/tools/asian-handicap-calculator', icon: '🎚️', key: 'ft.ahCalc' },
  { href: '/tools/poisson-calculator', icon: '📈', key: 'ft.poissonCalc' },
  { href: '/tools/accumulator-calculator', icon: '🎯', key: 'ft.accaCalc' },
  { href: '/tools/kelly-calculator', icon: '📐', key: 'tl.nmKelly' },
  { href: '/tools/margin-calculator', icon: '📊', key: 'ft.marginCalc' },
  { href: '/tools/hedging-calculator', icon: '🛡️', key: 'tl.nmHedge' },
  { href: '/tools/dutching-calculator', icon: '🪢', key: 'tl.nmDutch' },
  { href: '/tools/trixie-calculator', icon: '🧩', label: 'Trixie' },
  { href: '/tools/patent-calculator', icon: '🧩', label: 'Patent' },
  { href: '/tools/yankee-calculator', icon: '🧩', label: 'Yankee' },
  { href: '/tools/lucky-15-calculator', icon: '🧩', label: 'Lucky 15' },
  { href: '/tools/canadian-calculator', icon: '🧩', label: 'Canadian' },
  { href: '/tools/lucky-31-calculator', icon: '🧩', label: 'Lucky 31' },
  { href: '/tools/heinz-calculator', icon: '🧩', label: 'Heinz' },
  { href: '/tools/lucky-63-calculator', icon: '🧩', label: 'Lucky 63' },
  { href: '/tools/super-heinz-calculator', icon: '🧩', label: 'Super Heinz' },
  { href: '/tools/goliath-calculator', icon: '🧩', label: 'Goliath' },
  { href: '/dropping-odds', icon: '📉', key: 'ft.droppingOdds' },
];
