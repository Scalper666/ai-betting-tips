import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  // TODO: switch back to https://ai-betting-tips.com once the domain is bought
  // (canonical/sitemap must point at the domain that actually serves the site).
  site: 'https://ai-betting-tips.pages.dev',
  build: { format: 'directory' },      // /predictions/real-madrid-vs-man-city/
  trailingSlash: 'ignore',
  integrations: [sitemap()],           // emits /sitemap-index.xml at build time
});
