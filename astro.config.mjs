import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Sitemap lastmod: data-driven pages genuinely change on every rebuild (odds,
// standings, settlements — twice daily via CI), while editor-written pages only
// change when we edit them. Claiming "modified today" for a guide nobody
// touched is a false signal, so the two groups get different dates.
// Bump CONTENT_UPDATED whenever guides/glossary/tools/legal copy changes.
const CONTENT_UPDATED = '2026-08-04T00:00:00.000Z';
const BUILD_ISO = new Date().toISOString();
const STATIC_RE = /^\/(guides|glossary|tools|about|model|contact|privacy|terms|responsible-gambling|cookies)(\/|$)/;

export default defineConfig({
  site: 'https://ai-betting-tips.com',
  build: { format: 'directory' },      // /predictions/real-madrid-vs-man-city/
  trailingSlash: 'ignore',
  integrations: [sitemap({
    serialize(item) {
      const path = new URL(item.url).pathname.replace(/^\/(es|pt|de|fr)(?=\/|$)/, '') || '/';
      item.lastmod = STATIC_RE.test(path) ? CONTENT_UPDATED : BUILD_ISO;
      return item;
    },
  })],
});
