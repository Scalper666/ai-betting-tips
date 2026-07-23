@echo off
REM ============================================================
REM  One command: refresh live data, then deploy.
REM    1) run the odds pipeline (fetch odds -> data -> sync into src\data)
REM    2) commit the refreshed JSON and push -> Cloudflare Pages rebuilds
REM
REM  Prereq: `git remote` is set (you pushed the repo to GitHub once),
REM          and the pipeline has a real ODDS_API_KEY in its .env.
REM
REM  Schedule daily (runs when the PC is on):
REM    schtasks /create /sc DAILY /st 08:00 /tn AIBetTipsRefresh ^
REM      /tr "D:\CLOUDE\sharptips-astro\refresh.bat"
REM ============================================================
cd /d "%~dp0"

call "..\sharptips\pipeline\update.bat"
if errorlevel 1 (
  echo [publish] pipeline failed - nothing pushed
  exit /b 1
)

git add src\data
git diff --cached --quiet
if not errorlevel 1 (
  echo [publish] no data changes - nothing to deploy
  exit /b 0
)

git commit -m "data: daily refresh"
git push
echo [publish] pushed - Cloudflare Pages will rebuild and deploy
