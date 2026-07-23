# Deploy checklist — ai-betting-tips.com

From working prototype to a live, auto-updating site. Steps marked 🧑 need you
(accounts / keys); everything else is already wired in the code.

## 1. Real odds data 🧑 ~5 min

1. Sign up at <https://the-odds-api.com> (free tier = 500 requests/month).
2. Copy your API key.
3. Open `..\sharptips\pipeline\.env` and set:
   ```
   ODDS_API_KEY=your_real_32_char_key
   ODDS_API_SPORTS=soccer_epl,soccer_uefa_champs_league   # keep the list short to save quota
   ```
4. Test one refresh:
   ```
   cd ..\sharptips\pipeline
   update.bat
   ```
   This fetches odds → writes `data\*.json` → syncs into `src\data\` here.
   `update.bat --mock` runs with sample data and no API calls.

## 2. Put the repo on GitHub 🧑 ~5 min

```
# from this folder (already a git repo)
git remote add origin https://github.com/<you>/ai-betting-tips.git
git branch -M main
git push -u origin main
```

## 3. Cloudflare Pages 🧑 ~5 min

1. <https://dash.cloudflare.com> → **Workers & Pages** → **Create** → **Pages** →
   **Connect to Git** → pick the repo.
2. Build settings:
   - Framework preset: **Astro**
   - Build command: `npm run build`
   - Output directory: `dist`
3. Deploy. Every `git push` now rebuilds and ships automatically.

## 4. Domain 🧑 ~10 min (+ DNS propagation)

- In the Pages project → **Custom domains** → add `ai-betting-tips.com`.
- Point the domain's nameservers (or CNAME) to Cloudflare as instructed there.
- `site:` in `astro.config.mjs` is already set to the production URL.

## 5. Daily refresh

Run `refresh.bat` (in this folder) — it refreshes data and pushes, and Cloudflare
redeploys. Schedule it with Task Scheduler (see the header of `refresh.bat`).
The API key stays on your machine; nothing secret goes to GitHub.

> Want updates without your PC on? That's the next step: move the pipeline into
> this repo and run it from a scheduled GitHub Action (key stored as a repo
> secret). Ask and I'll set it up.

## Still demo — replace before/soon after launch

- **Bookmakers / casinos** are demo entries (red badge). Join real affiliate
  programs, then fill `src/data/bookmakers.json` and `src/data/casinos.json`
  with real brands + affiliate links; the badge disappears automatically.
- **Legal pages** (About, Privacy, Terms, Responsible Gambling, Contact) are not
  built yet — most affiliate programs require them. Ask and I'll scaffold them.
- **Page copy** is currently templated. Unique AI-written text per page is what
  earns SEO traffic — ask and I'll add a Claude-API content step.
