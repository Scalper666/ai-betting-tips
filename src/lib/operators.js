// Demo bookmaker/casino/bonus sections are hidden until real affiliate deals
// exist (user decision, Aug 2026): the entries in bookmakers.json/casinos.json
// are placeholders, and indexed fake reviews cost more trust than they earn.
//
// Turning this back ON requires TWO steps:
//   1. SHOW_OPERATORS = true (rebuild picks up nav/home/country/route gates)
//   2. DELETE the "demo-operators-hidden" block from public/_redirects —
//      Cloudflare Pages serves _redirects BEFORE static assets, so leaving it
//      would shadow the re-enabled pages with 301s.
export const SHOW_OPERATORS = false;
