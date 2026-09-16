(function () {
  'use strict';

  window.dataLayer = window.dataLayer || [];
  window.trackShuconEvent = function (name, parameters) {
    var payload = parameters || {};
    if (typeof window.gtag === 'function') window.gtag('event', name, payload);
    else window.dataLayer.push(Object.assign({ event: name }, payload));
  };

  var year = document.getElementById('year2');
  if (year) year.textContent = new Date().getFullYear();

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

  document.querySelectorAll('[data-event]').forEach(function (element) {
    element.addEventListener('click', function () {
      window.trackShuconEvent(element.getAttribute('data-event'), {
        link_text: element.textContent.trim(),
        link_url: element.href || window.location.href,
        page_path: window.location.pathname
      });
    });
  });

  var trackedForms = new WeakSet();
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('focusin', function () {
      if (!trackedForms.has(form)) {
        trackedForms.add(form);
        window.trackShuconEvent('lead_form_started', { form_id: form.id || 'lead-form' });
      }
    });
  });

  if (document.body.dataset.pageType === 'case-study') {
    window.trackShuconEvent('case_study_viewed', { page_path: window.location.pathname });
  }

  document.querySelectorAll('[data-print-checklist]').forEach(function (button) {
    button.addEventListener('click', function () {
      window.trackShuconEvent('checklist_downloaded', { format: 'print_or_pdf' });
      window.print();
    });
  });
}());
