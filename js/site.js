(function () {
  'use strict';

  var LEAD_ENDPOINT = 'https://script.google.com/macros/s/AKfycbw9CVm38ySD_-9Pmh8dBXiwVBFBDIsvWG3BcCn_lg7qaAlUKp3-yZN5oFYcC-o0cQNt/exec';
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var path = window.location.pathname;

  window.dataLayer = window.dataLayer || [];
  window.trackShuconEvent = function (name, parameters) {
    var payload = parameters || {};
    if (typeof window.gtag === 'function') window.gtag('event', name, payload);
    else window.dataLayer.push(Object.assign({ event: name }, payload));
  };

  var logoLink = document.querySelector('.nav-logo');
  var root = logoLink ? (logoLink.getAttribute('href') || '').replace(/index\.html$/, '') : '';

  // Links point at index.html so local file:// previews work; on the live site use the canonical folder URLs.
  if (/^https?:$/.test(window.location.protocol)) {
    document.querySelectorAll('a[href*="index.html"]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (/^(https?:|mailto:|tel:|\/\/)/.test(href) && href.indexOf(window.location.host) === -1) return;
      var clean = href.replace(/(^|\/)index\.html(?=$|[#?])/, '$1');
      a.setAttribute('href', clean === '' ? './' : clean);
    });
  }

  var year = document.getElementById('year2');
  if (year) year.textContent = new Date().getFullYear();

  /* Navigation: mobile toggle, active page, scrolled state */
  var nav = document.querySelector('.nav');
  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (toggle && links) {
    toggle.setAttribute('aria-expanded', 'false');
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    links.addEventListener('click', function (event) {
      if (event.target.tagName === 'A') {
        links.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }
  if (links) {
    var section = function (p) {
      var m = p.replace(/index\.html$/, '').match(/\/(ai-agents|agents|platform|solutions|hospital-revenue-leakage|blog)\//);
      if (!m) return null;
      return m[1] === 'agents' ? 'ai-agents' : m[1];
    };
    var current = section(path);
    links.querySelectorAll('a:not(.nav-cta)').forEach(function (a) {
      if (current && section(a.pathname) === current) a.setAttribute('aria-current', 'page');
    });
  }

  /* Scroll-driven UI */
  var backTop = document.getElementById('back-top');
  var sticky = null;
  var progress = null;
  var article = document.querySelector('article .prose, article.article, .prose');
  if (article && /\/blog\/[^/]+\.html$/.test(path) && !/index\.html$/.test(path)) {
    progress = document.createElement('div');
    progress.className = 'read-progress';
    progress.setAttribute('aria-hidden', 'true');
    document.body.appendChild(progress);
  }

  var contact = document.getElementById('contact');
  var heroEl = document.querySelector('.agent-hero, .landing-hero, .commercial-hero, .blog-hero, .article-head, header');
  sticky = document.createElement('div');
  sticky.className = 'sticky-cta';
  sticky.innerHTML = '<span>See an agent run on your workflow</span><a href="' + root + 'index.html#contact" data-event="demo_clicked">Book a demo</a>';
  document.body.appendChild(sticky);

  /* WhatsApp: floating button + one-time CEO modal after 15s */
  var WA_URL = 'https://wa.me/918755504999?text=' + encodeURIComponent('Hi Saksham, I found Shucon MedAI and would like to discuss AI agents for our hospital.');
  var waIcon = '<svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true"><path fill="currentColor" d="M16 3a13 13 0 0 0-11.2 19.6L3 29l6.6-1.7A13 13 0 1 0 16 3zm0 23.6c-2 0-3.9-.5-5.6-1.5l-.4-.2-3.9 1 1-3.8-.3-.4A10.6 10.6 0 1 1 16 26.6zm5.8-7.9c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2l-1 1.2c-.2.2-.4.2-.7.1a8.7 8.7 0 0 1-4.3-3.8c-.3-.6.3-.5.9-1.7.1-.2 0-.4 0-.5l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.1 1.1-1.1 2.7s1.2 3.2 1.3 3.4c.2.2 2.3 3.5 5.6 4.9 2.1.9 2.9 1 4 .8.6-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.2-.3-.2-.6-.4z"/></svg>';
  var waFab = document.createElement('a');
  waFab.className = 'wa-fab';
  waFab.href = WA_URL;
  waFab.target = '_blank';
  waFab.rel = 'noopener';
  waFab.setAttribute('aria-label', 'Contact the CEO on WhatsApp');
  waFab.innerHTML = waIcon + '<span class="wa-fab-label">Contact CEO on WhatsApp</span>';
  waFab.addEventListener('click', function () { window.trackShuconEvent('whatsapp_clicked', { source: 'fab' }); });
  document.body.appendChild(waFab);

  var WA_KEY = 'shucon_wa_prompt_seen';
  var waSeen = false;
  try { waSeen = window.localStorage.getItem(WA_KEY) === '1'; } catch (e) { waSeen = false; }
  if (!waSeen) {
    var showWaPrompt = function () {
      var active = document.activeElement;
      if (document.hidden || document.querySelector('.demo-modal[open]') || (active && /INPUT|TEXTAREA|SELECT/.test(active.tagName))) {
        setTimeout(showWaPrompt, 5000);
        return;
      }
      try { window.localStorage.setItem(WA_KEY, '1'); } catch (e) { /* storage unavailable */ }
      var box = document.createElement('dialog');
      box.className = 'wa-prompt';
      box.setAttribute('aria-labelledby', 'waPromptTitle');
      box.setAttribute('tabindex', '-1');
      box.innerHTML =
        '<button type="button" class="wa-prompt-close" aria-label="Close">&times;</button>' +
        '<img class="wa-prompt-photo" src="' + root + 'images/saksham-gupta-linkedin.jpg" alt="Saksham Gupta" width="88" height="88">' +
        '<h2 id="waPromptTitle">Talk directly to our CEO</h2>' +
        '<div class="wa-prompt-who"><strong>Saksham Gupta</strong><span>CEO &middot; Ex-Microsoft, core AI Copilot team</span></div>' +
        '<p>Exploring AI agents for your hospital? Message me on WhatsApp and I&rsquo;ll help you find the right place to start.</p>' +
        '<a class="wa-prompt-cta" href="' + WA_URL + '" target="_blank" rel="noopener">' + waIcon + 'Chat on WhatsApp</a>' +
        '<button type="button" class="wa-prompt-later">Maybe later</button>';
      document.body.appendChild(box);
      if (typeof box.showModal === 'function') box.showModal(); else box.setAttribute('open', '');
      box.focus();
      window.requestAnimationFrame(function () { box.classList.add('show'); });
      window.trackShuconEvent('whatsapp_prompt_shown', { page: path });
      var closed = false;
      var close = function () {
        if (closed) return;
        closed = true;
        box.classList.remove('show');
        setTimeout(function () { if (box.open && box.close) box.close(); box.remove(); }, reduceMotion ? 0 : 250);
      };
      box.addEventListener('cancel', function (e) { e.preventDefault(); close(); });
      box.addEventListener('click', function (e) { if (e.target === box) close(); });
      box.querySelector('.wa-prompt-close').addEventListener('click', close);
      box.querySelector('.wa-prompt-later').addEventListener('click', close);
      box.querySelector('.wa-prompt-cta').addEventListener('click', function () {
        window.trackShuconEvent('whatsapp_clicked', { source: 'prompt' });
        close();
      });
    };
    setTimeout(showWaPrompt, 15000);
  }

  var contactVisible = false;
  if (contact && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      contactVisible = entries[0].isIntersecting;
      onScroll();
    }, { threshold: 0.05 }).observe(contact);
  }

  var ticking = false;
  function onScroll() {
    var y = window.scrollY;
    if (nav) nav.classList.toggle('is-scrolled', y > 8);
    if (backTop) backTop.classList.toggle('show', y > 900);
    var heroBottom = heroEl ? heroEl.getBoundingClientRect().bottom + y : 600;
    sticky.classList.toggle('show', y > heroBottom - 80 && !contactVisible && !document.querySelector('.demo-modal[open]'));
    if (progress) {
      var rect = article.getBoundingClientRect();
      var total = rect.height - window.innerHeight * 0.6;
      var ratio = Math.min(1, Math.max(0, (-rect.top + window.innerHeight * 0.2) / total));
      progress.style.transform = 'scaleX(' + ratio + ')';
    }
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; window.requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();

  /* Lead forms */
  var CHIPS = ['Revenue leakage', 'Insurance claims', 'Patient calls', 'Stakeholder actions', 'HMS platform', 'Diagnostics', 'Custom agent'];
  var PAGE_INTEREST = [
    [/revenue-leakage|billing-leakage|pharmacy|case-study|hospital-ai|operations-ai/, 'Revenue leakage'],
    [/insurance-claims/, 'Insurance claims'],
    [/patient-engagement/, 'Patient calls'],
    [/stakeholder-action/, 'Stakeholder actions'],
    [/hospital-management-system/, 'HMS platform'],
    [/diagnostics/, 'Diagnostics'],
    [/custom-healthcare-ai/, 'Custom agent']
  ];
  function pageInterest() {
    for (var i = 0; i < PAGE_INTEREST.length; i++) if (PAGE_INTEREST[i][0].test(path)) return PAGE_INTEREST[i][1];
    return '';
  }

  function enhanceChips(form) {
    var group = form.querySelector('.chip-group');
    if (!group) return;
    if (!group.children.length) {
      CHIPS.forEach(function (label) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'chip';
        b.textContent = label;
        b.setAttribute('aria-pressed', 'false');
        group.appendChild(b);
      });
    }
    group.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip) return;
      chip.setAttribute('aria-pressed', chip.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
    });
  }
  function selectChip(form, label) {
    form.querySelectorAll('.chip').forEach(function (c) {
      c.setAttribute('aria-pressed', String(c.textContent === label));
    });
  }

  function successMarkup() {
    return '<div class="lead-success" role="status">' +
      '<div class="tick" aria-hidden="true">&#10003;</div>' +
      '<h3>Request received</h3>' +
      '<p>We will reply within one business day with times for a 30-minute discovery call. While you wait:</p>' +
      '<div class="next-links">' +
      '<a href="' + root + 'hospital-revenue-leakage-checklist/index.html">Run the 25-point revenue leakage audit</a>' +
      '<a href="' + root + 'ai-agents/index.html">Compare all agent suites</a>' +
      '<a href="' + root + 'leadership/saksham-gupta/index.html">Meet the founder</a>' +
      '</div></div>';
  }

  function bindLeadForm(form) {
    if (form.dataset.bound) return;
    form.dataset.bound = '1';
    enhanceChips(form);
    var alertBox = form.parentNode.querySelector('.form-alert, #form-alert');
    var submit = form.querySelector('button[type="submit"]');
    var label = submit ? submit.textContent : '';
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var data = new FormData(form);
      var picked = Array.prototype.map.call(form.querySelectorAll('.chip[aria-pressed="true"]'), function (c) { return c.textContent; });
      var details = (data.get('message') || '').toString().trim();
      var parts = [];
      if (picked.length) parts.push('Interested in: ' + picked.join(', '));
      if (details) parts.push(details);
      parts.push('Page: ' + path);
      data.set('message', parts.join('\n'));
      if (!data.get('phone')) data.set('phone', '-');

      submit.textContent = 'Sending...';
      submit.disabled = true;
      var request = new XMLHttpRequest();
      request.open('POST', LEAD_ENDPOINT);
      request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
      request.timeout = 15000;
      function fail() {
        if (alertBox) alertBox.innerHTML = '<div class="error">We could not send your request. Please email <a href="mailto:saksham@shucontech.in">saksham@shucontech.in</a>.</div>';
        submit.textContent = label;
        submit.disabled = false;
      }
      request.onreadystatechange = function () {
        if (request.readyState !== 4) return;
        if (request.status >= 200 && request.status < 400) {
          form.outerHTML = successMarkup();
          if (alertBox) alertBox.innerHTML = '';
          window.trackShuconEvent('lead_form_submitted', { form_id: form.id || 'lead-form', interest: picked.join(',') });
        } else fail();
      };
      request.onerror = fail;
      request.ontimeout = fail;
      request.send(new URLSearchParams(data).toString());
    });
  }
  document.querySelectorAll('form[data-lead-form]').forEach(bindLeadForm);

  /* Demo modal: opens from any "#contact" CTA on pages without an inline form */
  var modal = null;
  function buildModal() {
    modal = document.createElement('dialog');
    modal.className = 'demo-modal';
    modal.setAttribute('aria-labelledby', 'demoModalTitle');
    modal.innerHTML =
      '<div class="demo-modal-inner form-card">' +
      '<div class="demo-modal-head"><div><h3 id="demoModalTitle">Book an agent discovery call</h3>' +
      '<p class="fsub">30 minutes with our team. We map one workflow and show how an agent would run it.</p></div>' +
      '<button type="button" class="demo-close" aria-label="Close">&times;</button></div>' +
      '<div class="form-alert" aria-live="polite"></div>' +
      '<form id="modal-form" data-lead-form novalidate>' +
      '<div class="frow"><div class="fg"><label for="m-name">Full name *</label><input id="m-name" name="fullName" autocomplete="name" required></div>' +
      '<div class="fg"><label for="m-email">Work email *</label><input id="m-email" type="email" name="email" autocomplete="email" required></div></div>' +
      '<div class="frow"><div class="fg"><label for="m-org">Organization *</label><input id="m-org" name="hospitalName" autocomplete="organization" required></div>' +
      '<div class="fg"><label for="m-phone">Phone <span class="optional">(optional)</span></label><input id="m-phone" type="tel" name="phone" autocomplete="tel"></div></div>' +
      '<div class="fg"><label>What would you like to automate?</label><div class="chip-group" role="group" aria-label="Workflows"></div></div>' +
      '<div class="fg"><label for="m-msg">Anything else? <span class="optional">(optional)</span></label><textarea id="m-msg" name="message" rows="2" placeholder="Team, systems or current bottleneck"></textarea></div>' +
      '<button type="submit" class="btn btn-primary">Request discovery call</button>' +
      '<div class="demo-assure"><span>Reply within 1 business day</span><span>No obligation</span><span>Your data stays private</span></div>' +
      '</form></div>';
    document.body.appendChild(modal);
    modal.querySelector('.demo-close').addEventListener('click', function () { modal.close(); });
    modal.addEventListener('click', function (e) { if (e.target === modal) modal.close(); });
    modal.addEventListener('close', onScroll);
    bindLeadForm(modal.querySelector('form'));
  }
  function openModal(trigger) {
    if (!modal) buildModal();
    var form = modal.querySelector('form');
    var title = modal.querySelector('#demoModalTitle');
    var text = trigger ? trigger.textContent.trim() : '';
    title.textContent = /^(book|discuss|request|talk)/i.test(text) && text.length > 12 ? text : 'Book an agent discovery call';
    if (form) {
      var interest = trigger && trigger.dataset.interest || pageInterest();
      if (interest) selectChip(form, interest);
    }
    modal.showModal();
    onScroll();
    var first = modal.querySelector('input');
    if (first) first.focus();
    window.trackShuconEvent('demo_modal_opened', { page_path: path, trigger: text });
  }

  var hasInlineForm = !!document.getElementById('contact-form');
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href$="#contact"]');
    if (!a || typeof HTMLDialogElement !== 'function') return;
    if (hasInlineForm) {
      var target = document.getElementById('contact');
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' });
      var interest = a.dataset.interest;
      var inline = document.getElementById('contact-form');
      if (interest && inline) selectChip(inline, interest);
      setTimeout(function () { var f = document.getElementById('fullName'); if (f) f.focus({ preventScroll: true }); }, reduceMotion ? 0 : 650);
      return;
    }
    e.preventDefault();
    openModal(a);
  });

  /* Analytics hooks */
  document.querySelectorAll('[data-event]').forEach(function (element) {
    element.addEventListener('click', function () {
      window.trackShuconEvent(element.getAttribute('data-event'), {
        link_text: element.textContent.trim(),
        link_url: element.href || window.location.href,
        page_path: path
      });
    });
  });
  var trackedForms = new WeakSet();
  document.addEventListener('focusin', function (e) {
    var form = e.target.closest && e.target.closest('form');
    if (form && !trackedForms.has(form)) {
      trackedForms.add(form);
      window.trackShuconEvent('lead_form_started', { form_id: form.id || 'lead-form' });
    }
  });
  if (document.body.dataset.pageType === 'case-study') {
    window.trackShuconEvent('case_study_viewed', { page_path: path });
  }
  document.querySelectorAll('[data-print-checklist]').forEach(function (button) {
    button.addEventListener('click', function () {
      window.trackShuconEvent('checklist_downloaded', { format: 'print_or_pdf' });
      window.print();
    });
  });

  /* Homepage: goal filter for product suites */
  var filterBar = document.querySelector('[data-goal-filter]');
  if (filterBar) {
    var cards = document.querySelectorAll('.suite-grid [data-goal]');
    var grid = document.querySelector('.suite-grid');
    filterBar.addEventListener('click', function (e) {
      var btn = e.target.closest('button[data-goal]');
      if (!btn) return;
      var goal = btn.dataset.goal;
      filterBar.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
      grid.classList.toggle('is-filtered', goal !== 'all');
      cards.forEach(function (card) {
        var show = goal === 'all' || card.dataset.goal.split(' ').indexOf(goal) !== -1;
        card.hidden = !show;
        if (show) card.classList.add('revealed');
      });
      window.trackShuconEvent('suite_filter_used', { goal: goal });
    });
  }

  /* Homepage: live operations console */
  var consoleEl = document.querySelector('.ops-console');
  var feed = consoleEl && consoleEl.querySelector('[data-feed]');
  if (consoleEl && feed) {
    var runs = consoleEl.querySelectorAll('.agent-run');
    var events = [
      ['R', '3 unbilled pharmacy items flagged', 'Billing desk'],
      ['P', 'Admission enquiry called back in 40 sec', 'Patient access'],
      ['I', 'Missing discharge summary attached to claim', 'TPA desk'],
      ['O', 'OT charge exception escalated', 'Unit head'],
      ['R', 'Discount outside policy held for approval', 'Finance'],
      ['P', 'Follow-up booked after OPD visit', 'Front office'],
      ['I', 'Pre-auth documents verified', 'Insurance team'],
      ['O', 'Daily action brief sent', 'COO']
    ];
    var idx = 0;
    var tick = function () {
      var ev = events[idx % events.length];
      runs.forEach(function (r) { r.classList.toggle('is-active', r.querySelector('.run-icon').textContent === ev[0]); });
      feed.classList.remove('in');
      void feed.offsetWidth;
      feed.innerHTML = '<b>' + ev[1] + '</b><span>Routed to ' + ev[2] + '</span>';
      feed.classList.add('in');
      idx++;
    };
    tick();
    if (!reduceMotion) setInterval(function () { if (!document.hidden) tick(); }, 2800);
  }

  /* Count-up metrics */
  var counters = document.querySelectorAll('[data-count]');
  function runCount(el) {
    var end = parseFloat(el.dataset.count);
    if (reduceMotion || !end) { el.textContent = el.dataset.count; return; }
    var start = null;
    var step = function (ts) {
      if (!start) start = ts;
      var p = Math.min(1, (ts - start) / 1100);
      el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
      if (p < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
  }

  /* Scroll reveal */
  if ('IntersectionObserver' in window && !reduceMotion) {
    var selector = '.section-intro, .section-head, .suite-card, .stakeholder-row, .stakeholder-demo .content-copy, .platform-band, .founder-panel, .resource-card, .landing-card, .process-item, .related-card, .post-card, .info-card, .step, .agent-faq details, .stat, .profile-facts > *, .contact-grid > *, .cta-band, .link-panel, .feat';
    var targets = Array.prototype.filter.call(document.querySelectorAll(selector), function (el) {
      return el.getBoundingClientRect().top > window.innerHeight * 0.92 && !el.closest('.demo-modal');
    });
    document.documentElement.classList.add('js-reveal');
    var siblingIndex = new Map();
    targets.forEach(function (el) {
      var parent = el.parentNode;
      var i = siblingIndex.get(parent) || 0;
      siblingIndex.set(parent, i + 1);
      el.style.setProperty('--reveal-delay', Math.min(i, 5) * 0.07 + 's');
      el.setAttribute('data-reveal', '');
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('revealed');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    targets.forEach(function (el) { io.observe(el); });
  }
  if (counters.length && 'IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        runCount(entry.target);
        cio.unobserve(entry.target);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (c) { cio.observe(c); });
  }
}());
