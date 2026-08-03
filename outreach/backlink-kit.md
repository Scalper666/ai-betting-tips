# Backlink-кит AI Betting Tips

Рабочий документ для линкбилдинга. Тексты постов и писем — на английском (готовы к копипасту), инструкции — на русском. Обновлён: август 2026.

**Главное правило:** мы никогда не покупаем ссылки, не спамим и не выдаём себя за «просто пользователя» там, где это против правил. Наш козырь — реальные данные и радикальная прозрачность (публикуем и убытки, и CLV). Это редкость в нише, и именно это цепляет модераторов и авторов.

---

## 1. Что продвигаем (наши линк-магниты)

| Актив | URL | Питч-угол |
|---|---|---|
| Исследование маржи | /research/bookmaker-margins | «Средняя best-price маржа 2.86% против 5–7% у одиночного букмекера — на живых данных 18 лиг, пересчитывается каждый день» |
| Предсказуемость лиг | /research/league-predictability | «Какие лиги статистически предсказуемее — на 2 сезонах результатов» |
| CLV-эксперимент | /research/clv-experiment | «Мы публикуем closing line value каждого пика нашей модели — тест на честность, который не проходит ни один продавец прогнозов» |
| Методология модели | /model | «Poisson-модель с открытой методологией, версиями и известными ограничениями» |
| Трек-рекорд | /tipsters | «Полный settled-лог, включая убыточные серии — flat 1 unit» |
| Калькуляторы | /tools | Конвертер кэфов, акка- и маржа-калькулятор — бесплатные, без регистрации |
| Гайды | /guides | 12 обучающих статей с worked examples |
| H2H-база | /h2h | 1655 страниц очных встреч |

**UTM для отслеживания в GA4:** добавляй `?utm_source=reddit&utm_medium=post&utm_campaign=outreach` (меняй source: hn, quora, forum, email). В GA: Отчёты → Источники трафика.

---

## 2. Куда идти (по приоритету и вероятности успеха)

### Уровень A — лёгкие быстрые ссылки (сделать за неделю)

1. **AI-каталоги** — сайт называется AI Betting Tips, мы буквально их формат:
   - theresanaiforthat.com (TAAFT) — submit tool, бесплатная заявка
   - futurepedia.io — submit
   - topai.tools, aitoolsdirectory.com, insidr.ai — submit
   - Питч: «AI football predictions with fully transparent model tracking (CLV, settled log)». Категория: Sports / Data.
2. **Каталоги инструментов:** saashub.com, alternativeto.net (позиционировать /tools как альтернативу odds-converter-сайтам).
3. **GitHub awesome-списки** — PR в `awesome-sports-analytics`, `awesome-football-analytics` (искать на GitHub): добавить /research и /model как «open methodology betting model with published CLV». PR-описание честное, без маркетинга.
4. **Kaggle** — опубликовать датасет «Football odds & settled predictions archive» (наш results-archive без ключей) со ссылкой на сайт как источник. Дают dofollow-профиль + доверие.

### Уровень B — Reddit (аккуратно, по правилам каждого саба)

⚠️ Общие правила Reddit: аккаунту 1+ месяц и карма 100+; правило 90/10 (9 обычных комментариев на 1 свой линк); сначала неделю комментировать без ссылок. Бан за самопромо в первых постах — почти гарантирован. Не постить одно и то же в несколько сабов в один день.

| Саб | Что постить | Текст ниже |
|---|---|---|
| r/algobetting (идеальный фит) | CLV-эксперимент + методология | Текст R1 |
| r/SoccerBetting | Исследование маржи (в weekly discussion thread — не отдельным постом сначала) | Текст R2 |
| r/dataisbeautiful | График предсказуемости лиг как [OC] — нужен красивый chart, скажи мне — сделаю PNG | — |
| r/Python | Дев-стори: «пайплайн на Python: odds API → Poisson → static site» | Текст R3 |
| r/sportsbook | Только комментарии с ответами, ссылки в профиле. Отдельные посты — бан | — |

### Уровень C — сообщества и форумы

- **Hacker News** — Show HN про прозрачный трекинг модели (Текст H1). Лучшее время: будни 14:00-16:00 UTC. Шанс невелик, но хвост трафика длинный.
- **IndieHackers** — build-in-public пост: «3800-страничный programmatic SEO сайт на Astro + Python, соло» — там любят цифры и стек.
- **Беттинг-форумы:** bettingadvice.com/forum, punterslounge.com — завести профиль, ссылка в подписи, отвечать в разделах статистики. Не спамить тредами.
- **Quora** — вопросы «how to read betting odds», «what is asian handicap», «are AI betting tips accurate» → развёрнутый ответ + ссылка на соответствующий гайд (Текст Q1-заготовка).

### Уровень D — outreach по email (медленно, но самые жирные ссылки)

Цели: авторы беттинг-блогов, статистические футбольные сайты, авторы рассылок про спортивную аналитику, преподаватели статистики (CLV-эксперимент — готовый учебный пример). Искать: Google «football betting blog», «sports analytics newsletter», авторы на Substack/Medium с материалами про value betting. 5-10 писем в неделю, персонализированных. Шаблоны E1-E3 ниже.

### Куда НЕ идти

- «Каталоги букмекерских сайтов» с платным размещением — это PBN-помойки, риск санкций Google.
- Покупка ссылок, обмен «ты мне — я тебе» пакетами, комментарий-спам.
- Wikipedia — удалят и запомнят домен.

---

## 3. Готовые тексты — Reddit

### R1 — r/algobetting (пост)

**Title:** We publish the CLV of every pick our Poisson model makes — 100% of them, including the losing streaks

**Body:**

> Most tipster sites show you a cherry-picked month. We decided to do the opposite experiment: publish every single pick our model makes, flat-staked, and track closing line value on all of them.
>
> The setup: time-decayed Poisson attack/defence rates (240-day half-life, shrinkage toward league mean), blended 40/60 with market-implied probabilities. A pick only goes out when the blend clears the best available price with sane odds caps — most matches produce no pick.
>
> Honest results so far: our v1 went 0-for-8 on double-digit-odds picks (classic longshot bias — the model overrated its own fair odds against sharper closing prices), which forced the odds-cap rebuild. Early v2 sample is small; CLV is the metric we're watching, not ROI, since it converges orders of magnitude faster.
>
> Methodology and the live CLV table: [link /research/clv-experiment]. Happy to answer anything about the decay/shrinkage choices — and genuinely curious what CLV thresholds others treat as "model has signal".

*(Фишка: пост даёт ценность и признаёт ошибки — r/algobetting такое любит. Отвечай на все комментарии в первые 2 часа.)*

### R2 — r/SoccerBetting (сначала в weekly thread, потом отдельным постом через 2-3 недели)

> Ran the numbers on bookmaker margins across 18 leagues we track daily: average best-price margin (shopping across books) is 2.86%, while typical single-bookmaker margins on the same fixtures run 5–7%. In practice that means line shopping alone cuts the fee you pay roughly in half — before any skill enters the picture. Data recomputes on every site rebuild if anyone wants to check their league: [link /research/bookmaker-margins]

### R3 — r/Python (дев-угол)

**Title:** I built a fully automated football-prediction pipeline: Odds API → Poisson model → 3,800-page static site, rebuilt twice a day by GitHub Actions

**Body:**

> Stack: Python pipeline (requests + a hand-rolled time-decayed Poisson model, no ML frameworks), JSON handoff to an Astro static site, GitHub Actions cron twice a day, Cloudflare Pages hosting. Total hosting cost: $0. The pipeline pulls odds for 18 leagues, settles yesterday's picks against real scores, recomputes model ratings, regenerates ~3,800 pages and deploys — no server anywhere.
>
> The part I'd defend in a code review: every published pick is archived immutably and graded automatically, so the site can't quietly delete its losers — the settlement log is generated from the same archive the model writes to. [link /model]
>
> Happy to share details on the Poisson shrinkage, the odds-API credit budgeting, or the Astro programmatic-SEO setup.

### Q1 — Quora-заготовка (адаптируй под вопрос)

> Short answer: [двух-трёхстрочный прямой ответ на вопрос своими словами].
>
> Longer version with a worked example: [1 абзац сути из соответствующего гайда, пересказанной, НЕ копипастой]. There's a free calculator/guide that walks through the exact numbers here: [link соответствующего /guides или /tools с utm_source=quora]. Disclosure: I work on that site.

---

## 4. Готовый текст — Hacker News

### H1 — Show HN

**Title:** Show HN: A betting-tips site that publishes every losing pick and its closing-line value

**Body:**

> The tipster industry runs on survivorship bias — losing months get deleted, fake "verified profits" everywhere. As an experiment in the opposite direction, we publish our model's complete settled log (currently negative ROI on the early sample, flat-staked) plus the closing line value of every pick, which is the fastest honest signal of whether a model has edge.
>
> Under the hood: time-decayed Poisson ratings blended with market prices, Python pipeline, 3,800-page Astro static site rebuilt twice daily by CI for $0 hosting. The margins research (best-price margin across books: 2.86% avg vs 5–7% single-book) doubles as a consumer-protection artifact.
>
> Not financial advice; the site says so on every page. Interested in feedback on the CLV methodology specifically.

*(HN уважает «negative ROI on the early sample» — это наш анти-скам-питч. Никогда не удаляй эту честность из текста.)*

---

## 5. Шаблоны писем (персонализируй первую строку под каждого адресата!)

### E1 — блогеру/автору рассылки (data-share)

**Subject:** League predictability data for [их сайт/рассылка]

> Hi [Name],
>
> Your piece on [конкретная их статья — обязательно прочитай и назови] made a point about [деталь] that matches what we see in our data.
>
> We track odds across 18 leagues daily and publish a couple of open datasets that might be useful for your writing: which leagues are statistically most predictable (2 seasons of results), and live bookmaker-margin comparisons (best-price avg 2.86% vs 5–7% single-book). Everything recomputes automatically — no stale numbers.
>
> If any of it is useful for a future piece, feel free to use the data with a link back. And if you'd like a custom cut (specific league, market or timeframe), I'm happy to pull it — no strings.
>
> [Имя]
> ai-betting-tips.com/research

### E2 — resource-страницы и «лучшие инструменты» подборки

**Subject:** Free odds converter + margin calculator for your [название страницы] page

> Hi [Name],
>
> Your [точное название их resource-страницы] lists a few odds calculators — a couple of the links there now 404 ([какие именно, если нашёл]).
>
> We maintain free, no-signup betting calculators (decimal/fractional/American converter with implied probability, accumulator and margin calculators): ai-betting-tips.com/tools. If they fit the list, they'd be a working replacement.
>
> Either way, thanks for maintaining the page — it's a genuinely useful roundup.
>
> [Имя]

### E3 — гостевой пост

**Subject:** Guest post idea: "Why every tipster you follow should publish closing line value"

> Hi [Name],
>
> I run ai-betting-tips.com, where we publish our prediction model's full settled record — including the losing runs — plus the closing line value of every pick.
>
> I'd like to write a piece for [их сайт] on how readers can use CLV to separate real betting skill from marketing in under a month of data — with our own numbers (flattering and not) as the worked example. 1,200–1,500 words, original, with the data to back every claim.
>
> If the angle fits, I can send an outline this week.
>
> [Имя]

---

## 6. Темп и трекинг

- **Неделя 1:** уровень A целиком (каталоги, awesome-списки, Kaggle) + завести/прогреть Reddit-аккаунт комментариями.
- **Неделя 2:** R1 в r/algobetting, R2 в weekly thread, IndieHackers-пост.
- **Неделя 3:** Show HN, R3 в r/Python, первые 10 писем E1/E2.
- **Постоянно:** 2-3 ответа на Quora в неделю, 5-10 писем в неделю.
- **Трекинг:** таблица (площадка / дата / URL размещения / статус / трафик по UTM из GA4). Ссылки индексируются неделями — судить по GSC «Ссылки» через месяц, не через день.
- **Метрика успеха месяца 1:** 10-15 живых размещений, 3-5 доменов в GSC Links, первые переходы по UTM.
