@echo off
REM ============================================================
REM  One command: refresh live data, rebuild, deploy.
REM  Mirrors .github/workflows/daily-refresh.yml (which runs this
REM  same pipeline in the cloud every morning — this script is for
REM  manual/off-schedule runs).
REM
REM  Pipeline lives in .\pipeline, data snapshots in .\data,
REM  keys in .\pipeline\.env (gitignored).
REM ============================================================
cd /d "%~dp0"

python pipeline\build.py
if errorlevel 1 ( echo [refresh] build.py failed & exit /b 1 )

python pipeline\results.py
if errorlevel 1 ( echo [refresh] results.py failed & exit /b 1 )

python pipeline\stats.py
if errorlevel 1 ( echo [refresh] stats.py failed & exit /b 1 )

python pipeline\screener.py
if errorlevel 1 ( echo [refresh] screener.py failed & exit /b 1 )

python pipeline\generate_content.py
if errorlevel 1 ( echo [refresh] generate_content.py failed - continuing with cached copy )

python pipeline\sync_astro.py
if errorlevel 1 ( echo [refresh] sync_astro.py failed & exit /b 1 )

call npm run build
if errorlevel 1 ( echo [refresh] astro build failed & exit /b 1 )

call npx wrangler pages deploy dist --project-name ai-betting-tips --commit-dirty=true
if errorlevel 1 ( echo [refresh] cloudflare deploy failed & exit /b 1 )
echo [refresh] live at https://ai-betting-tips.pages.dev

git add data src\data
git diff --cached --quiet
if not errorlevel 1 (
  echo [refresh] no data changes to commit
  exit /b 0
)
git commit -m "data: manual refresh"
git push
echo [refresh] data snapshot pushed to GitHub
