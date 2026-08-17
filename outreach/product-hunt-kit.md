# Product Hunt — launch kit

Всё готово к запуску. От тебя: выбрать день (вторник–четверг), выложить в 00:01 PT
(10:01 по Кипру / 07:01 UTC — чем раньше в сутках PH, тем больше времени собирать голоса),
и в течение дня отвечать на комментарии. Ссылку на страницу запуска НЕ постить в чужие
треды — PH банит за vote-begging.

## Форма подачи (producthunt.com/posts/new)

**Link:** https://ai-betting-tips.com

**Name:** AI Betting Tips

**Tagline** (≤60 символов):
```
Football predictions with every result published — even losses
```
(запасной вариант: `An AI football model that publishes its losses too` — 50)

**Topics:** Artificial Intelligence, Sports, Data & Analytics

**Description** (краткое, поле “What is it?”):
```
A football predictions site that does the opposite of tipster marketing: every pick
is archived before kick-off, settled against the real final score, and published —
losing runs included. Poisson goal model blended with market odds, value picks only
when the edge clears the best available price, closing-line value tracked on every
pick. Free, no signup, 10 languages. The full settled log is open data (CC BY 4.0
on Kaggle).
```

**Первый комментарий мейкера** (запостить сразу после публикации):
```
Hi Product Hunt! Maker here.

I got tired of tipster sites that quietly delete their losing months, so I built
the opposite: a football prediction model whose entire record is public and
settles itself against real final scores twice a day.

How it works:
• A time-decayed Poisson goal model rates every club's attack/defence from ~11k
  historical results, then blends with market-implied probabilities.
• A pick is only published when the blend clears the best available price by a
  set margin — most days that's just a handful of picks, some days zero.
• Every pick stores the odds at publication AND the closing odds, so you can see
  closing-line value — the earliest honest signal of whether a model has an edge.
• Losses stay on the site forever. The full settled log is CC BY 4.0 on Kaggle.

It's free, there's no signup, and it runs in 10 languages (including Swahili,
Hausa, Yoruba, Igbo and Amharic — African markets are badly underserved).

Honest limitations: the model knows results and prices, not injuries or rotation;
top-league markets are sharp, so edges are small and rare. That's exactly what
the public record is for — judge it yourself.

Ask me anything about the model, the data, or why publishing losses is the whole
point.
```

## Галерея (1270×760)

Файлы в `outreach/product-hunt/`:
1. `ph-1-hero.png` — брендовая карточка (лого + tagline)
2. `ph-2-how.png` — «как это работает» в 3 шага
3. `ph-3-record.png` — честный график settled-лога (кумулятивный профит, CLV)
Плюс добавь 1–2 живых скриншота сайта (главная и страница матча) — свежие можно
снять в браузере на весь экран; PH сам отресайзит.

**Логотип для формы:** `outreach/logo/ai-betting-tips-logo-1024.png` (240×240 они
режут сами).

## Чеклист дня запуска

- [ ] 00:01 PT — пост опубликован, топики выставлены, галерея загружена
- [ ] сразу — первый комментарий мейкера
- [ ] в профиле PH заполнить bio + ссылку на сайт
- [ ] отвечать на КАЖДЫЙ комментарий в первые 4–6 часов (это ранжирует)
- [ ] НЕ просить голоса ни в каких чатах/тредах — бан
- [ ] вечером — добавить строку в трекер (раздел 7 backlink-kit.md)

## Что даёт

Профиль + страница запуска = 2 dofollow-ссылки с DR~90 домена, плюс страница
запуска сама ранжируется по «ai betting tips» запросам. Даже без топ-5 дня —
самая сильная бесплатная ссылка из оставшихся.

---

# Бонус: график для r/dataisbeautiful

Файл: `outreach/product-hunt/reddit-settled-record.png` (тот же график, что ph-3,
но с Reddit-заголовком). Постить ПОСЛЕ прогрева аккаунта (1–2 недели комментариев),
флейр **[OC]**.

**Title:**
```
[OC] I built a football betting model and publish every single pick's result — 318 settled picks later: -5.7 units, losses and all
```

**Обязательный комментарий (правило сабреддита — источник и инструмент, запостить сразу):**
```
Data source: our own public prediction log — every pick archived before kick-off
and auto-settled against real final scores (CC BY 4.0):
https://www.kaggle.com/datasets/aibettingtips/football-betting-predictions-fully-settled-log
Tool: matplotlib.

Context: picks are published only when a Poisson goal model blended with market
odds clears the best available price. Flat 1-unit stakes. The -8.2u drawdown and
the swings back are exactly why we publish everything — cherry-picked tipster
records are survivorship bias in action. Average closing-line value sits at
-0.5% over 300+ picks, which honestly says the model has no proven edge yet;
the public log is the experiment. Happy to answer questions about the model or
the data.
```

Не вставляй ссылку на сайт в сам пост — только Kaggle в комментарии-источнике
(двойная ссылка в посте = типичная причина удаления модераторами).
