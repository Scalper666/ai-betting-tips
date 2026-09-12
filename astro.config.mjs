import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { SHOW_OPERATORS } from './src/lib/operators.js';
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

// Trailing-slash consistency. Pages live at /x/ (build.format 'directory'),
// canonical and sitemap say /x/, but hand-written internal links said /x and
// Cloudflare 308s every one of them: the Sep-2026 crawl-stats report showed
// 37% of Googlebot requests ending in a redirect hop on a site that gets ~800
// requests a day. Rewriting the built HTML is the one place that catches every
// link — templates, hreflang alternates, JSON-LD URLs — without touching
// hundreds of call sites. Files (.svg/.xml/...) and /api/ routes are left alone.
const slashed = (p) => (p === '' || p.endsWith('/') || /\.[a-z0-9]+$/i.test(p) || p.startsWith('/api/') ? p : p + '/');
const fixPath = (p) => {
  const m = p.match(/^(.*?)([.,;:)]*)$/);   // prose URLs may carry trailing punctuation
  return slashed(m[1]) + m[2];
};
function* htmlFiles(dir) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const f = join(dir, e.name);
    if (e.isDirectory()) yield* htmlFiles(f);
    else if (e.name.endsWith('.html')) yield f;
  }
}
const trailingSlashLinks = () => ({
  name: 'trailing-slash-links',
  hooks: {
    'astro:build:done': ({ dir, logger }) => {
      let files = 0, links = 0;
      for (const f of htmlFiles(fileURLToPath(dir))) {
        const src = readFileSync(f, 'utf8');
        const out = src
          .replace(/href="(\/[^"?#]*)([?#][^"]*)?"/g, (m, p, tail = '') => { const s = fixPath(p); if (s !== p) links++; return `href="${s}${tail}"`; })
          .replace(/(https:\/\/ai-betting-tips\.com)(\/[^"'<>\s?#]*)/g, (m, host, p) => { const s = fixPath(p); if (s !== p) links++; return host + s; });
        if (out !== src) { writeFileSync(f, out); files++; }
      }
      logger.info(`trailing-slash: ${links} links fixed in ${files} files`);
    },
  },
});

// Sitemap lastmod: data-driven pages genuinely change on every rebuild (odds,
// standings, settlements — twice daily via CI), while editor-written pages only
// change when we edit them. Claiming "modified today" for a guide nobody
// touched is a false signal, so the two groups get different dates.
// Bump CONTENT_UPDATED whenever guides/glossary/tools/legal copy changes.
const CONTENT_UPDATED = '2026-08-14T00:00:00.000Z';
const BUILD_ISO = new Date().toISOString();
const STATIC_RE = /^\/(guides|glossary|tools|about|model|contact|privacy|terms|responsible-gambling|cookies)(\/|$)/;

export default defineConfig({
  site: 'https://ai-betting-tips.com',
  build: { format: 'directory' },      // /predictions/real-madrid-vs-man-city/
  trailingSlash: 'always',             // one URL form everywhere: /x/ (see trailingSlashLinks)
  integrations: [trailingSlashLinks(), sitemap({
    // operator sections hidden: keep their (301-shadowed) pages out of sitemaps
    filter: (page) => SHOW_OPERATORS || !/\/(bookmakers|bonuses|casinos|betting-apps)(\/|$)/.test(new URL(page).pathname),
    serialize(item) {
      const path = new URL(item.url).pathname.replace(/^\/(es|pt|de|fr)(?=\/|$)/, '') || '/';
      item.lastmod = STATIC_RE.test(path) ? CONTENT_UPDATED : BUILD_ISO;
      return item;
    },
  })],
});
