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

## 2.5. Каталоги: прямые ссылки на формы + тексты для полей

Актуализировано 16 авг 2026: эра бесплатных AI-каталогов закончилась — верхняя тройка стала платной. Бесплатные — вверху, платные — с ценами, чтобы не тратить время на формы.

**Бесплатные (делать сейчас):**

| Площадка | Как | Что подавать |
|---|---|---|
| Product Hunt | producthunt.com — Launch (бесплатно, их основная модель) | /tools/acca-builder как продукт |
| AlternativeTo | alternativeto.net → Add application | /tools |
| SaaSHub | saashub.com/submit («free», подтверждено) | сайт |
| Kaggle | New Dataset (датасет из архива результатов) | ссылка на сайт как источник |
| GitHub awesome-списки | PR в awesome-sports-analytics / awesome-football-analytics | /research + /model |
| Reddit / HN / IndieHackers / Quora | тексты R1-R3, H1, Q1 ниже | по текстам |

**Платные (НЕ покупать до реальных партнёрок; это легальные review fee, не PBN — вопрос чисто экономический):**

| Площадка | Цена | Вердикт |
|---|---|---|
| TopAI.tools | $47 fast-track (бесплатной очереди больше нет) | единственная осмысленная дешёвая покупка — потом |
| There's An AI For That | $49 / $347 | $49 — когда будет монетизация; $347 — никогда (нецелевая рассылка) |
| Futurepedia | $497 (базовый $247 «sold out») | нет: цена ссылки безумна для нашего этапа |
| Insidr.ai | проверить при подаче — вероятно тоже платный | по обстоятельствам |

В AI-каталоги подаём **/tools/acca-builder**, а не главную: их формат — «инструмент», и конкретный AI-билдер купонов проходит модерацию легче, чем «сайт прогнозов». Ссылка на главную всё равно будет в профиле листинга.

### Поля форм (копипаст, EN)

**Name:** `AI Betting Tips — Acca Builder` (для AI-каталогов) / `AI Betting Tips` (для остальных)

**Tagline / short (до 80 зн., 3 варианта — чередуй, не вставляй один и тот же текст везде):**
1. `AI football predictions with a fully transparent, settled track record`
2. `Poisson-model football tips — every pick archived, graded and published`
3. `Free AI acca builder + football predictions with open methodology`

**Description ~160 зн. (для карточек, 2 варианта):**
1. `AI football predictions for 28 leagues: Poisson model, value screener, acca builder and free calculators. Every pick is archived and settled openly — losses included.`
2. `Free football betting tips from a versioned statistical model. Full settled log, closing-line-value tracking, odds comparison and no-signup betting calculators.`

**Long description (300–600 зн., 2 варианта):**

Вариант 1 (AI-каталоги):
> AI Betting Tips generates football predictions for 28 leagues with a time-decayed Poisson model blended with market prices. The Acca Builder assembles accumulator coupons from the model's screened value picks and shows honestly how hit rate falls with every leg. Unlike typical tipster sites, the full track record is published and settled automatically against real scores — losing runs and closing line value included. Free, no signup, updated twice daily.

Вариант 2 (общие каталоги):
> An independent football predictions site built on a documented statistical model rather than invented experts. Covers 28 leagues with daily tips, an AI value screener, odds comparison, H2H stats, league tables and free betting calculators (odds converter, accumulator, margin, Kelly). Radical transparency is the core feature: every published pick is archived before kick-off and graded against the final score, with the complete log — wins and losses — public.

**Tags/категории:** `Sports` `Betting` `Predictions` `Data & Analytics` (что есть из этого списка)
**Pricing:** `Free`
**Логотип:** https://ai-betting-tips.com/apple-touch-icon.png · **Обложка:** https://ai-betting-tips.com/og.png (1200×630). Скриншоты для галереи — главная и /screener.

### Правила публикации (чтобы Google это засчитал, а не наказал)

1. **Анкор — только бренд или URL** («AI Betting Tips», «ai-betting-tips.com»). Никогда не «best betting tips» и подобные коммерческие анкоры — переоптимизация анкоров это единственный реальный риск санкций на этом этапе.
2. **Описания варьировать** — выше по 2-3 варианта; один и тот же текст на 10 площадках выглядит как автоспам и хуже модерируется.
3. **Темп: 3–5 площадок в неделю**, не всё за вечер. Резкий всплеск одинаковых ссылок — паттерн, который Google дисконтирует.
4. **nofollow — тоже ссылка.** Каталоги часто ставят nofollow; это всё равно трафик, брендовые сигналы и путь краулеру. Не гнаться только за dofollow.
5. **Заполнять профиль целиком** (лого, скрины, категории) — полупустые заявки чаще отклоняют.
6. **Не платить за featured/premium** в каталогах-помойках. Бесплатное размещение в нормальном каталоге > платное в мусорном.
7. **Проверка результата — GSC → Ссылки, через 2–4 недели.** Ссылки индексируются медленно; судить на следующий день бессмысленно.

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


---

## 7. Трекинг размещений

| Дата | Площадка | URL/статус | Ссылка появилась? |
|---|---|---|---|
| 2026-08-13 | Insidr.ai | форма отправлена (insidr.ai/submit-tools/), ждёт модерацию | проверить через неделю |
| 2026-08-13 | SaaSHub | карточка создана: saashub.com/related-alternatives/ai-betting-tips — ждёт одобрения (Free-очередь до 32 дней); лого уже стоит (их автофетч), скриншот загружен; 1024px-лого лежит в outreach/logo/ для будущих площадок (Product Hunt и т.п.) | проверить через месяц |
| 2026-08-14 | AlternativeTo | карточка создана + 6 альтернатив привязаны (Forebet, 1X2.TV, PredictLix, MetaPred, Daily Sport Pick, Vitibet); статус «waiting to be reviewed»; бесплатная очередь — МЕСЯЦЫ, за $5 — ревью за 1-2 дня (рекомендовано); после одобрения добавить скриншоты руками (их фетчер падал на og.png); ссылку не шарить до одобрения | ждёт ревью |
| 2026-08-14 | Kaggle | датасет опубликован (Public, CC BY 4.0): kaggle.com/datasets/aibettingtips/football-betting-predictions-fully-settled-log — 2 CSV + README; в описании ссылки на ai-betting-tips.com и /model | да — в описании датасета |
