/* BlueMind Therapy — site behaviour: mobile nav, photo slots, and the three forms. */
(function () {
  'use strict';

  // ── Mobile navigation ─────────────────────────────────────────────────
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
  }

  // ── Photo slots: show the illustrated panel until a real photo exists ──
  document.querySelectorAll('.photo img').forEach(function (img) {
    var slot = img.closest('.photo');
    var markEmpty = function () { slot.classList.add('is-empty'); };
    if (img.complete && img.naturalWidth === 0) markEmpty();
    img.addEventListener('error', markEmpty);
  });

  // ── Forms ─────────────────────────────────────────────────────────────
  var cfg = window.BLUEMIND || {};
  var ENDPOINTS = {
    referral: { path: '/api/referral-portal/referrals', kind: 'json' },
    application: { path: '/api/website-portal/applications', kind: 'multipart' },
    message: { path: '/api/website-portal/messages', kind: 'json' },
  };

  function fallbackText() {
    return 'Please call us at ' + (cfg.phone || '(734) 252-5215') + ' or email ' + (cfg.email || 'info@bluemindmi.com') + '.';
  }

  function buildJson(form) {
    var data = {};
    var fd = new FormData(form);
    var multi = {};
    form.querySelectorAll('input[type="checkbox"][data-multi]').forEach(function (cb) { multi[cb.name] = true; });
    fd.forEach(function (value, key) {
      if (value instanceof File) return;
      if (multi[key]) {
        if (!data[key]) data[key] = [];
        if (value) data[key].push(value);
        return;
      }
      data[key] = typeof value === 'string' ? value.trim() : value;
    });
    Object.keys(multi).forEach(function (k) { if (!data[k]) data[k] = []; });
    // Empty dates must be null, not "".
    form.querySelectorAll('input[type="date"]').forEach(function (d) {
      if (!d.value) data[d.name] = null;
    });
    return data;
  }

  function showStatus(form, kind, text) {
    var box = form.querySelector('.form-status');
    if (!box) return;
    box.className = 'form-status ' + kind;
    box.textContent = text;
    box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  function showSuccess(form, result) {
    var title = form.dataset.successTitle || 'Received';
    var body = form.dataset.successBody || (result && result.message) || 'Thank you.';
    var card = document.createElement('div');
    card.className = 'form-card success-card';
    card.setAttribute('role', 'status');
    card.innerHTML =
      '<div class="check"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg></div>' +
      '<h2></h2><p class="lede"></p><p class="ref"></p><p class="small muted"></p>';
    card.querySelector('h2').textContent = title;
    card.querySelector('.lede').textContent = body;
    if (result && result.reference) {
      card.querySelector('.ref').textContent = 'Your reference number is ' + result.reference + '.';
      card.querySelector('.small').textContent = 'Keep it handy if you call us about this submission.';
    }
    var holder = form.closest('.form-card') || form;
    holder.replaceWith(card);
    card.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  document.querySelectorAll('form[data-endpoint]').forEach(function (form) {
    var endpoint = ENDPOINTS[form.dataset.endpoint];
    if (!endpoint) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;

      var file = form.querySelector('input[type="file"]');
      if (file && file.files && file.files[0] && file.files[0].size > 5 * 1024 * 1024) {
        showStatus(form, 'err', 'Your resume is larger than 5 MB. Please attach a smaller PDF or Word file.');
        file.focus();
        return;
      }

      var button = form.querySelector('button[type="submit"]');
      var original = button ? button.textContent : '';
      if (button) { button.disabled = true; button.textContent = 'Sending…'; }

      var url = (cfg.apiBase || '') + endpoint.path;
      var options = { method: 'POST', mode: 'cors', credentials: 'omit' };
      if (endpoint.kind === 'multipart') {
        options.body = new FormData(form);
      } else {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(buildJson(form));
      }

      fetch(url, options)
        .then(function (res) {
          return res.json().catch(function () { return {}; }).then(function (body) {
            if (!res.ok) {
              var detail = body && body.detail;
              if (Array.isArray(detail)) detail = detail.map(function (d) { return d.msg; }).join(' ');
              var msg = res.status === 429
                ? 'Too many submissions from this connection. Please wait a little while and try again, or call us.'
                : (typeof detail === 'string' && detail) || ('We could not send this (' + res.status + '). ' + fallbackText());
              throw new Error(msg);
            }
            return body;
          });
        })
        .then(function (result) { showSuccess(form, result); })
        .catch(function (err) {
          var text = (err && err.message && !/Failed to fetch|NetworkError|Load failed/i.test(err.message))
            ? err.message
            : 'We could not reach our intake system right now. ' + fallbackText();
          showStatus(form, 'err', text);
          if (button) { button.disabled = false; button.textContent = original; }
        });
    });
  });

  // ── Conditional fields (show when a yes/no select says yes) ───────────
  document.querySelectorAll('[data-shows]').forEach(function (ctrl) {
    var target = document.getElementById(ctrl.dataset.shows);
    if (!target) return;
    var sync = function () { target.hidden = !(ctrl.value === 'Yes' || ctrl.value === 'Other'); };
    ctrl.addEventListener('change', sync);
    sync();
  });

  // ── Footer year ───────────────────────────────────────────────────────
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });
})();

/* ── Premium layer: motion and flow ──────────────────────────────────────── */
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.add('js');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Header shrink + reading progress bar.
  var header = document.querySelector('.site-header');
  var bar = document.createElement('div'); bar.className = 'progress'; bar.setAttribute('aria-hidden', 'true');
  document.body.appendChild(bar);
  var ticking = false;
  function onScroll() {
    if (ticking) return; ticking = true;
    requestAnimationFrame(function () {
      var y = window.scrollY || 0;
      if (header) header.classList.toggle('scrolled', y > 24);
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? Math.min(100, (y / h) * 100) : 0) + '%';
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  // Scroll reveal: sections' direct children and cards settle into place as they enter.
  var targets = document.querySelectorAll('.card, .step, .faq details, .section-head, .split > *, .contact-item, .stat, .page-intro .wrap > *');
  targets.forEach(function (el) { el.classList.add('reveal'); });
  if (!reduce && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    targets.forEach(function (el) { io.observe(el); });
    // Safety net: nothing stays hidden if the observer never fires.
    setTimeout(function () { targets.forEach(function (el) { el.classList.add('in'); }); }, 2500);
  } else {
    targets.forEach(function (el) { el.classList.add('in'); });
  }

  // Hero: pointer glow and parallax on the floating pieces.
  var hero = document.querySelector('.hero');
  if (hero && !reduce && window.matchMedia('(pointer: fine)').matches) {
    var glow = hero.querySelector('.glow');
    var floats = hero.querySelectorAll('.float');
    hero.addEventListener('pointermove', function (e) {
      var r = hero.getBoundingClientRect();
      var x = e.clientX - r.left, y = e.clientY - r.top;
      if (glow) { glow.style.setProperty('--gx', x + 'px'); glow.style.setProperty('--gy', y + 'px'); }
      var dx = (x / r.width - 0.5), dy = (y / r.height - 0.5);
      floats.forEach(function (f, i) {
        var k = (i + 1) * 10;
        f.style.transform = 'translate3d(' + (dx * k) + 'px,' + (dy * k) + 'px,0)';
      });
    });
  }

  // Count-up numbers.
  document.querySelectorAll('[data-count]').forEach(function (el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    if (isNaN(target) || reduce) { el.textContent = String(target); return; }
    var start = null, dur = 900, from = 0;
    var run = function (ts) {
      if (!start) start = ts;
      var p = Math.min(1, (ts - start) / dur), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = String(Math.round(from + (target - from) * eased));
      if (p < 1) requestAnimationFrame(run);
    };
    requestAnimationFrame(run);
  });

  // Step-by-step forms: each fieldset is a step; validation per step; progress bar.
  document.querySelectorAll('form[data-stepper]').forEach(function (form) {
    var steps = Array.prototype.slice.call(form.querySelectorAll('fieldset'));
    if (steps.length < 2) return;
    var idx = 0;
    var stepper = document.createElement('div'); stepper.className = 'stepper';
    stepper.innerHTML = '<div class="bar"><i></i></div><ol></ol>';
    var list = stepper.querySelector('ol'), fill = stepper.querySelector('.bar i');
    steps.forEach(function (fs, i) {
      var li = document.createElement('li');
      var legend = fs.querySelector('legend');
      li.textContent = (i + 1) + '. ' + (legend ? legend.textContent.trim() : 'Step ' + (i + 1));
      list.appendChild(li);
    });
    form.insertBefore(stepper, form.firstChild);
    var nav = document.createElement('div'); nav.className = 'step-nav';
    nav.innerHTML = '<button type="button" class="btn btn-secondary" data-back>Back</button><span class="spacer"></span><span class="small muted" data-pos></span><button type="button" class="btn btn-primary" data-next>Continue</button>';
    var err = document.createElement('p'); err.className = 'step-error'; err.setAttribute('role', 'alert');
    var actions = form.querySelector('.form-actions');
    form.insertBefore(err, actions);
    form.insertBefore(nav, actions);
    var back = nav.querySelector('[data-back]'), next = nav.querySelector('[data-next]'), pos = nav.querySelector('[data-pos]');

    function show(i, focus) {
      idx = Math.max(0, Math.min(steps.length - 1, i));
      steps.forEach(function (fs, j) { fs.classList.toggle('active', j === idx); });
      list.querySelectorAll('li').forEach(function (li, j) {
        li.classList.toggle('done', j < idx); li.classList.toggle('current', j === idx);
      });
      fill.style.width = (((idx + 1) / steps.length) * 100) + '%';
      back.hidden = idx === 0;
      var last = idx === steps.length - 1;
      next.hidden = last;
      nav.hidden = last;
      form.classList.toggle('last', last);
      pos.textContent = 'Step ' + (idx + 1) + ' of ' + steps.length;
      err.classList.remove('show');
      if (focus) {
        var first = steps[idx].querySelector('input, select, textarea');
        stepper.scrollIntoView({ block: 'start', behavior: reduce ? 'auto' : 'smooth' });
        if (first) setTimeout(function () { first.focus({ preventScroll: true }); }, 350);
      }
    }
    function valid(fs) {
      var controls = fs.querySelectorAll('input, select, textarea');
      for (var i = 0; i < controls.length; i++) {
        if (controls[i].closest('[hidden]')) continue;
        if (!controls[i].checkValidity()) { controls[i].reportValidity(); return false; }
      }
      return true;
    }
    next.addEventListener('click', function () {
      if (!valid(steps[idx])) { err.textContent = 'Please complete the highlighted field to continue.'; err.classList.add('show'); return; }
      show(idx + 1, true);
    });
    back.addEventListener('click', function () { show(idx - 1, true); });
    form.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && idx < steps.length - 1 && e.target.type !== 'submit') {
        e.preventDefault(); next.click();
      }
    });
    // On a failed submit (server says a field is wrong), jump to the first invalid step.
    form.addEventListener('submit', function () {
      for (var i = 0; i < steps.length; i++) { if (!valid(steps[i])) { show(i, true); break; } }
    }, true);
    show(0, false);
  });

  // Sticky call bar on phones (not on pages that already are a form).
  if (!document.body.hasAttribute('data-no-sticky')) {
    var cfg = window.BLUEMIND || {};
    var stick = document.createElement('div'); stick.className = 'sticky-cta';
    stick.innerHTML = '<a class="btn btn-secondary" href="' + (cfg.phoneHref || 'tel:+17342525215') + '">Call us</a><a class="btn btn-primary" href="refer.html">Refer a child</a>';
    var referLink = document.querySelector('.nav a.btn-primary');
    if (referLink) stick.querySelector('.btn-primary').setAttribute('href', referLink.getAttribute('href'));
    document.body.appendChild(stick);
    document.body.classList.add('has-sticky');
  }

  // Prefetch internal pages on hover so navigation feels instant.
  var seen = {};
  document.addEventListener('pointerover', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href');
    if (!href || /^(https?:|mailto:|tel:|#)/.test(href) || seen[href]) return;
    seen[href] = true;
    var l = document.createElement('link'); l.rel = 'prefetch'; l.href = href; document.head.appendChild(l);
  }, { passive: true });
})();

/* ── Photo gallery ───────────────────────────────────────────────────────── */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.gallery').forEach(function (g) {
    var track = g.querySelector('.gallery-track');
    var dots = g.querySelector('.gallery-dots');
    var count = g.querySelector('.gallery-count');
    var prev = g.querySelector('.prev'), next = g.querySelector('.next');
    var slides = function () { return Array.prototype.slice.call(track.querySelectorAll('.gallery-slide')); };

    function buildDots() {
      dots.innerHTML = '';
      slides().forEach(function (s, i) {
        var b = document.createElement('button');
        b.type = 'button'; b.setAttribute('role', 'tab'); b.setAttribute('aria-label', 'Photo ' + (i + 1));
        b.addEventListener('click', function () { go(i); });
        dots.appendChild(b);
      });
      if (slides().length < 2) { prev.hidden = true; next.hidden = true; dots.hidden = true; count.hidden = true; }
    }
    function index() { return Math.round(track.scrollLeft / Math.max(1, track.clientWidth)); }
    function go(i) {
      var n = slides().length; if (!n) return;
      i = (i + n) % n;
      track.scrollTo({ left: i * track.clientWidth, behavior: reduce ? 'auto' : 'smooth' });
    }
    function sync() {
      var i = index(), n = slides().length;
      dots.querySelectorAll('button').forEach(function (b, j) { b.setAttribute('aria-selected', j === i ? 'true' : 'false'); });
      count.textContent = n ? (i + 1) + ' / ' + n : '';
    }
    // A missing photo removes its slide rather than showing a broken image.
    slides().forEach(function (s) {
      var img = s.querySelector('img');
      var drop = function () { s.remove(); buildDots(); sync(); };
      if (img.complete && img.naturalWidth === 0) drop();
      img.addEventListener('error', drop);
    });
    buildDots(); sync();
    prev.addEventListener('click', function () { go(index() - 1); });
    next.addEventListener('click', function () { go(index() + 1); });
    var raf = false;
    track.addEventListener('scroll', function () { if (raf) return; raf = true; requestAnimationFrame(function () { sync(); raf = false; }); }, { passive: true });
    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); go(index() + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); go(index() - 1); }
    });
    window.addEventListener('resize', function () { go(index()); });
  });
})();
