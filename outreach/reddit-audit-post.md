# Посты «аудит рекорда» — Reddit / Hacker News / Product Hunt

Одна история для всех площадок: **«опубликовали 947 прогноза, потеряли 6%, вот все данные»**.
В этих сообществах читают ровно такое; «sure odds» там банят. Ссылка везде одна:
`https://ai-betting-tips.com/research/settled-picks-audit/` (статья пересчитывается из архива на каждой сборке — цифры в постах сверять с ней перед публикацией).

Правила: аккаунт прогрет (комментарии 1–2 недели), один пост в сабреддит, без кросспоста в тот же день,
отвечать на каждый комментарий в первые 2 часа, не спорить, не продавать. Ссылка на сайт — в тексте один раз,
не в заголовке.

---

## 1. r/algobetting — длинный пост (лучшая площадка)

**Заголовок:**
`Post-mortem: I published 947 football picks from a Poisson+market model and lost 6.1%. Calibration data, market split, and what actually went wrong`

**Текст:**

I've been running a public football prediction model since July: Poisson goal model (time-decayed attack/defence rates, two seasons of results) blended 40/60 with market-implied probabilities, publishing a pick only when the best available price cleared a value threshold. Every pick was archived pre-match with price and timestamp and settled on the final score. Nothing deleted.

**Result (24 Jul – 17 Sep, every pick published before the rule change):** 947 graded picks, 44.9% hit rate at 2.28 average odds (break-even 43.9%), ROI −6.1%, −58 units flat. That's −1.7σ from zero — i.e. not "variance", just no edge minus the margin. Closing-line value: −0.6% average. The market disagreed with me and it was right.

What I actually found when I took it apart:

1. **Calibration is fine above 60%, broken in the middle.** Picks the model rated 60–69% won 62.6%. Picks it rated 50–59% won 43.7% — ten points short — and that bucket was the largest (339 picks) and carried the entire loss on its own (−52u). The model was honest about its favourites and delusional about its coin-flips.

2. **Overs were the black hole.** Over-goals picks: 218 bets, ROI −18%, −39.5u. Unders: −3.5%. 1X2: −0.9%. Classic Poisson-runs-hot on goal expectation vs a sharp totals market. Interesting wrinkle: Overs had *positive* CLV (+1.0%) and still lost — the market drifted my way and the results didn't. Small sample, but it's the one place where "beat the close" and "make money" disagreed.

3. **September ate 45 units in 17 days.** Ratings have a 240-day half-life, so in the opening weeks of a season they still describe last year's squads. The model kept publishing at full volume through exactly the period it knew least about.

4. **Leagues: noise.** Championship went 6/31, Premier League +30% on 43 picks. I did NOT blacklist leagues — fitting rules to a league's last month is how you fit the scoreboard.

**What I changed (v3, live since 18 Sep, reported as a separate track so the old record never gets rewritten):** publish only at blended p ≥ 55%; no Over picks (they stay on the page as a labelled lean); no official picks until both teams have 4 matches in the last 75 days. In-sample that would have been +4% on a quarter of the volume — which I fully expect to shrink to "around zero" out of sample. If it doesn't beat the market either, that goes on the same page.

Full audit with live tables (recomputed daily): https://ai-betting-tips.com/research/settled-picks-audit/
The raw archive is on the daily results pages and as a CSV on Kaggle.

Happy to answer anything about the blend weight, the CLV proxy (twice-daily snapshots, not true close), or why I think publishing the loss is the only version of this that's worth anything.

---

## 2. r/dataisbeautiful — [OC] с графиком калибровки

**Файл:** `outreach/product-hunt/reddit-calibration.png`

**Заголовок:**
`[OC] Calibration of 947 football betting predictions: what the model said vs how often it actually won`

**Первый комментарий (обязателен по правилам сабреддита — источник и инструмент):**

Source: our own public archive of football picks (ai-betting-tips.com), every pick stored pre-match with the model's stated probability and graded on the final score. Tool: Python/matplotlib. Bubble size = number of picks in the bucket.

The interesting bit: the model is honest above 60% (62.6% actual) and overconfident in the 50–59% bucket (43.7% actual) — and that bucket is where most picks were, which is why the whole record ended at −6% ROI. Full breakdown by market, price and month: https://ai-betting-tips.com/research/settled-picks-audit/

---

## 3. Show HN

**Заголовок:** `Show HN: I published 947 football picks from a Poisson model and lost 6% – the audit`

**Текст:**

I built a football prediction site around one rule: every pick is archived before kick-off with its price and settled publicly on the final score, wins and losses alike. After 947 settled picks the model is at −6.1% ROI with −0.6% closing-line value — market-average minus the margin.

Instead of quietly resetting the counter, I published the post-mortem: calibration by stated probability (fine above 60%, ten points overconfident at 50–59%), by market (Over-goals picks alone were −18% ROI), by month (the new-season trap), plus the in-sample counterfactuals with the caveat that they flatter any filter.

The whole pipeline is data-driven and rebuilds twice a day: Poisson model + market blend, 26 leagues, ~7k static pages on Cloudflare, tables recomputed from the archive on each build. New picks run under stricter gates as a separate track so the old record never gets rewritten.

https://ai-betting-tips.com/research/settled-picks-audit/

---

## 4. Product Hunt — правка таглайна под ту же историю

Таглайн: `Football predictions with a public, losing track record — and the audit of why`
Первый комментарий мейкера — сокращённая версия поста для r/algobetting (первые три абзаца + ссылка).

---

## Порядок и сроки

1. r/algobetting — первым (там самая целевая аудитория и ноль риска бана).
2. r/dataisbeautiful — через 2–3 дня, с графиком; отдельный день от п.1.
3. Show HN — в будний день утром по US-времени (13:00–15:00 UTC), после того как сайт покажет v3-трек с ≥10 рассчитанными ставками (иначе «what changed» выглядит голословно).
4. Product Hunt — последним, когда есть свежий Reddit-тред: PH-хантеры любят «это уже обсуждают».

Что это даёт: ссылки с трёх сильных доменов, брендовые запросы, и — главное — единственная история, в которой минусовый рекорд работает на нас, а не против.
