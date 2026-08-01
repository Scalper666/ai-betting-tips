/* AI Betting Tips — shared UI behaviours */
(function () {
  'use strict';

  /* ---- Mobile nav drawer ---- */
  var burger = document.getElementById('burger');
  var nav = document.getElementById('mobileNav');
  var back = document.getElementById('mnBack');
  var close = document.getElementById('mnClose');
  function openNav() { nav && nav.classList.add('open'); back && back.classList.add('open'); }
  function closeNav() { nav && nav.classList.remove('open'); back && back.classList.remove('open'); }
  burger && burger.addEventListener('click', openNav);
  close && close.addEventListener('click', closeNav);
  back && back.addEventListener('click', closeNav);

  /* ---- SEO "read more" clamp ---- */
  document.querySelectorAll('[data-clamp-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = document.getElementById(btn.getAttribute('data-clamp-toggle'));
      if (!target) return;
      var open = target.classList.toggle('open');
      btn.innerHTML = open ? 'Show less &#9652;' : 'Read more &#9662;';
    });
  });

  /* ---- FAQ accordion ---- */
  document.querySelectorAll('.faq-q').forEach(function (q) {
    q.addEventListener('click', function () {
      q.parentElement.classList.toggle('open');
    });
  });

  /* ---- Generic filter chips (visual active state) ---- */
  document.querySelectorAll('[data-chip-group]').forEach(function (group) {
    group.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip) return;
      group.querySelectorAll('.chip').forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      // optional client-side filter by data-filter on items
      var key = chip.getAttribute('data-filter');
      var scope = group.getAttribute('data-chip-group');
      if (key && scope) {
        document.querySelectorAll('[data-filter-scope="' + scope + '"] [data-cat]').forEach(function (item) {
          item.style.display = (key === 'all' || item.getAttribute('data-cat') === key) ? '' : 'none';
        });
      }
    });
  });

  /* ---- Tabs ---- */
  document.querySelectorAll('[data-tabs]').forEach(function (group) {
    var tabs = group.querySelectorAll('.tab');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('active'); });
        tab.classList.add('active');
        var name = tab.getAttribute('data-tab');
        var scope = group.getAttribute('data-tabs');
        document.querySelectorAll('[data-panel-scope="' + scope + '"] [data-panel]').forEach(function (p) {
          p.style.display = p.getAttribute('data-panel') === name ? '' : 'none';
        });
      });
    });
  });

  /* ---- Stat animations: counters, progress bars, score rings ----
     Values are applied reliably on load (IntersectionObserver is unreliable in
     headless / embedded preview renderers). Bars grow via CSS transition;
     counters tick up. IO is used only as a nicer on-scroll trigger when it works,
     and a timeout backstop guarantees the final state regardless. */
  function runCount(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    var suffix = el.getAttribute('data-suffix') || '';
    var dur = 1100, t0 = Date.now();
    // setInterval (not requestAnimationFrame) so the count still completes in
    // renderers that pause rAF; the final value is always written at p>=1.
    var timer = setInterval(function () {
      var p = Math.min((Date.now() - t0) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      var v = target * eased;
      el.textContent = (target % 1 === 0 ? Math.round(v).toLocaleString() : v.toFixed(1)) + suffix;
      if (p >= 1) clearInterval(timer);
    }, 1000 / 60);
  }

  function activate(el) {
    if (el.dataset.animDone) return;
    el.dataset.animDone = '1';
    if (el.hasAttribute('data-count')) runCount(el);
    else if (el.classList.contains('bar')) { var i = el.querySelector('i'); if (i) i.style.width = (el.getAttribute('data-val') || 0) + '%'; }
    else if (el.classList.contains('ring')) { el.style.setProperty('--p', (el.getAttribute('data-val') || 0) + '%'); }
  }

  var animEls = document.querySelectorAll('[data-count],.bar,.ring');
  var io = ('IntersectionObserver' in window) ? new IntersectionObserver(function (entries) {
    entries.forEach(function (en) { if (en.isIntersecting) { activate(en.target); io.unobserve(en.target); } });
  }, { threshold: 0.25 }) : null;
  if (io) animEls.forEach(function (el) { io.observe(el); });
  // Reliability backstop: guarantee final state even if IO never fires.
  setTimeout(function () { animEls.forEach(activate); }, 700);

  /* ---- Year in footer ---- */
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* ---- Theme (colour scheme) switcher ---- */
  (function () {
    var KEY = 'sharptips-skin';
    function apply(skin) {
      var root = document.documentElement;
      if (skin && skin !== 'azure') root.setAttribute('data-skin', skin);
      else root.removeAttribute('data-skin');
      document.querySelectorAll('[data-skin-set]').forEach(function (b) {
        b.classList.toggle('active', b.getAttribute('data-skin-set') === (skin || 'azure'));
      });
    }
    var saved = 'azure';
    try { saved = localStorage.getItem(KEY) || 'azure'; } catch (e) {}
    apply(saved);
    var sw = document.querySelector('.theme-switch');
    if (!sw) return;
    var btn = sw.querySelector('.theme-btn');
    if (btn) btn.addEventListener('click', function (e) { e.stopPropagation(); sw.classList.toggle('open'); });
    sw.querySelectorAll('[data-skin-set]').forEach(function (b) {
      b.addEventListener('click', function () {
        var skin = b.getAttribute('data-skin-set');
        apply(skin);
        try { localStorage.setItem(KEY, skin); } catch (e) {}
        sw.classList.remove('open');
      });
    });
    document.addEventListener('click', function () { sw.classList.remove('open'); });
  })();

  /* language dropdown (same open/close pattern as the theme switch) */
  (function () {
    var ls = document.querySelector('.lang-switch');
    if (!ls) return;
    var btn = ls.querySelector('.lang-btn');
    if (btn) btn.addEventListener('click', function (e) { e.stopPropagation(); ls.classList.toggle('open'); });
    document.addEventListener('click', function () { ls.classList.remove('open'); });
  })();
})();

/* ---- Text-size control (A− / A+ in the header) ---- */
(function () {
  'use strict';
  var LEVELS = ['s', 'm', 'l', 'xl'];   // zoom: .92 / 1 / 1.1 / 1.2 (css [data-fz])
  function cur() {
    var i = LEVELS.indexOf(document.documentElement.getAttribute('data-fz') || 'l');
    return i < 0 ? 2 : i;
  }
  document.querySelectorAll('[data-fz-step]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var i = Math.min(LEVELS.length - 1, Math.max(0, cur() + parseInt(btn.getAttribute('data-fz-step'), 10)));
      document.documentElement.setAttribute('data-fz', LEVELS[i]);
      try { localStorage.setItem('abt-fz', LEVELS[i]); } catch (e) {}
    });
  });
})();
