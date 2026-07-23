@echo off
REM ============================================================
REM  One command: refresh live data, rebuild, deploy.
REM    1) run the odds pipeline (fetch odds -> data -> sync into src\data)
REM    2) npm run build            (fresh dist\)
REM    3) wrangler pages deploy    (direct upload -> ai-betting-tips.pages.dev)
REM    4) commit + push data to GitHub (history/backup)
REM
REM  Prereqs (already set up): wrangler login done once, git remote set,
REM  real ODDS_API_KEY in ..\sharptips\pipeline\.env.
REM
REM  Schedule daily (runs when the PC is on):
REM    schtasks /create /sc DAILY /st 08:00 /tn AIBetTipsRefresh ^
REM      /tr "D:\CLOUDE\sharptips-astro\refresh.bat"
REM ============================================================
cd /d "%~dp0"

call "..\sharptips\pipeline\update.bat"
if errorlevel 1 (
  echo [publish] pipeline failed - nothing deployed
  exit /b 1
)

call npm run build
if errorlevel 1 (
  echo [publish] astro build failed - nothing deployed
  exit /b 1
)

call npx wrangler pages deploy dist --project-name ai-betting-tips --commit-dirty=true
if errorlevel 1 (
  echo [publish] cloudflare deploy failed
  exit /b 1
)
echo [publish] live at https://ai-betting-tips.pages.dev

git add src\data
git diff --cached --quiet
if not errorlevel 1 (
  echo [publish] no data changes to commit
  exit /b 0
)
git commit -m "data: daily refresh"
git push
echo [publish] data snapshot pushed to GitHub
