import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://ai-betting-tips.com',
  build: { format: 'directory' },      // /predictions/real-madrid-vs-man-city/
  trailingSlash: 'ignore',
  integrations: [sitemap()],           // emits /sitemap-index.xml at build time
});
