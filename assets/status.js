// Status lookup page: reference + email -> timeline. Loaded with defer after site.js.
(function () {
  var cfg = window.BLUEMIND || {};
  var STEPS = {
    referral: ['new', 'contacted', 'intake_scheduled', 'accepted'],
    application: ['new', 'contacted', 'interviewing', 'offered', 'hired'],
    message: ['new', 'replied', 'closed']
  };
  var NAMES = {
    new: 'Received', contacted: 'Contacted', intake_scheduled: 'Intake scheduled', accepted: 'Accepted for services',
    interviewing: 'Interviewing', offered: 'Offer made', hired: 'Hired', replied: 'Replied', closed: 'Closed', declined: 'Not proceeding'
  };
  var KIND = { referral: 'Referral', application: 'Job application', message: 'Message' };
  var form = document.getElementById('statusForm'), out = document.getElementById('statusResult'), box = form.querySelector('.form-status');
  var q = new URLSearchParams(location.search).get('ref');
  if (q) document.getElementById('s_ref').value = q.toUpperCase();
  function fmt(d) { var p = d.split('-'); return p.length === 3 ? new Date(p[0], p[1] - 1, p[2]).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : d; }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;
    box.className = 'form-status'; out.classList.remove('show');
    var btn = form.querySelector('button'); btn.disabled = true; btn.textContent = 'Checking…';
    fetch((cfg.apiBase || '') + '/api/website-portal/status', { method: 'POST', mode: 'cors', credentials: 'omit', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reference: form.reference.value.trim(), email: form.email.value.trim(), website: form.website.value }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { if (!r.ok) throw new Error((b && typeof b.detail === 'string' && b.detail) || 'We could not check that right now. Please call ' + (cfg.phone || '(734) 252-5215') + '.'); return b; }); })
      .then(function (b) {
        document.getElementById('r_kind').textContent = KIND[b.kind] || 'Submission';
        document.getElementById('r_label').textContent = b.label;
        var pill = document.getElementById('r_pill');
        pill.className = 'status-pill ' + (b.status === 'declined' || b.status === 'closed' ? 'closed' : (b.status === 'new' ? 'pending' : ''));
        document.getElementById('r_ref').textContent = b.reference;
        document.getElementById('r_next').textContent = b.next_step;
        document.getElementById('r_sub').textContent = fmt(b.submitted_on);
        document.getElementById('r_upd').textContent = fmt(b.updated_on);
        var tl = document.getElementById('r_timeline'); tl.innerHTML = '';
        var steps = STEPS[b.kind] || [];
        var at = steps.indexOf(b.status);
        if (b.status === 'declined') { steps = steps.slice(0, 1).concat(['declined']); at = 1; }
        steps.forEach(function (s, i) { var li = document.createElement('li'); li.textContent = NAMES[s] || s; if (i < at) li.className = 'done'; if (i === at) li.className = 'current'; tl.appendChild(li); });
        out.classList.add('show'); out.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      })
      .catch(function (err) { box.className = 'form-status err'; box.textContent = err.message; })
      .then(function () { btn.disabled = false; btn.textContent = 'Check status'; });
  });
})();
