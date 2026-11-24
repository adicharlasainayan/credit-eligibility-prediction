/* ============================================================
   app.js  |  Credit Card Eligibility Prediction — Frontend Logic
   ============================================================ */

// ─── API base URL ───────────────────────────────────────────────
// Development:  http://localhost:8000
// Production:   set VITE_API_BASE or update RENDER_API_URL in render.yaml
// The script auto-detects by checking if running on localhost.
const API_BASE = (() => {
  const h = window.location.hostname;
  if (h === 'localhost' || h === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  // On Render, frontend is served by the same FastAPI server on the same origin
  return window.location.origin;
})();


// ─── Clock ──────────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('clock');
  if (el) {
    el.textContent = new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      timeZoneName: 'short',
    });
  }
}
setInterval(updateClock, 1000);
updateClock();


// ─── Stats ──────────────────────────────────────────────────────
async function loadStats() {
  try {
    const res  = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) return;
    const data = await res.json();
    setText('statCustomers',   data.total_customers   ?? '—');
    setText('statPredictions', data.total_predictions ?? '—');
    setText('statApproved',    data.approved          ?? '—');
    setText('statRejected',    data.rejected          ?? '—');
  } catch (_) { /* silent — stats are non-critical */ }
}
loadStats();


// ─── Helpers ────────────────────────────────────────────────────
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function fmt(n, decimals = 2) {
  return Number(n).toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtCurrency(n) {
  return '₹' + fmt(n, 0);  // Values are NT$ in raw data; display as-is
}

function payStatusLabel(val) {
  const v = Number(val);
  if (v <= -1) return { text: 'Paid / Revolving', cls: 'pay-status-good' };
  if (v === 0) return { text: 'Min. Payment',      cls: 'pay-status-warning' };
  if (v === 1) return { text: '1-Month Delay',     cls: 'pay-status-warning' };
  if (v === 2) return { text: '2-Month Delay',     cls: 'pay-status-danger' };
  return { text: `${v}-Month Delay`, cls: 'pay-status-danger' };
}

function dismissError() {
  document.getElementById('errorBanner').style.display = 'none';
}

function showError(msg) {
  document.getElementById('errorMsg').textContent = msg;
  document.getElementById('errorBanner').style.display = 'flex';
  document.getElementById('results').style.display = 'none';
}

function showLoader(on) {
  document.getElementById('loader').style.display = on ? 'flex' : 'none';
}


// ─── Main: Check Eligibility ────────────────────────────────────
async function checkEligibility() {
  const idInput = document.getElementById('userId');
  const userId  = idInput.value.trim();

  if (!userId || isNaN(userId) || Number(userId) < 1) {
    showError('Please enter a valid numeric Customer User ID.');
    return;
  }

  document.getElementById('errorBanner').style.display = 'none';
  document.getElementById('results').style.display     = 'none';
  showLoader(true);

  const btn = document.getElementById('checkBtn');
  btn.disabled = true;

  try {
    // ── 1. Prediction ──
    const predRes = await fetch(`${API_BASE}/api/predict/${userId}`);
    if (!predRes.ok) {
      let detail = `HTTP ${predRes.status}`;
      try { const j = await predRes.json(); detail = j.detail || detail; } catch (_) {}
      throw new Error(detail);
    }
    const data = await predRes.json();

    // ── 2. History ──
    let history = [];
    try {
      const histRes = await fetch(`${API_BASE}/api/history/${userId}?limit=10`);
      if (histRes.ok) history = await histRes.json();
    } catch (_) {}

    renderResults(data, history);
    loadStats(); // refresh stats

  } catch (err) {
    showError(err.message || 'Unexpected error. Please check your connection and try again.');
  } finally {
    showLoader(false);
    btn.disabled = false;
  }
}


// ─── Render Results ─────────────────────────────────────────────
function renderResults(d, history) {
  const isApproved = d.is_approved;

  // ── Verdict ──
  const verdictCard = document.getElementById('verdictCard');
  verdictCard.className = 'verdict-card ' + (isApproved ? 'approved' : 'rejected');
  setText('verdictIcon',   isApproved ? '✅' : '❌');
  setText('verdictStatus', isApproved ? '✅  APPROVED' : '❌  NOT APPROVED');
  setText('displayUID',    d.user_id);
  setText('verdictMeta',
    isApproved
      ? `Default probability (${(d.default_probability * 100).toFixed(1)}%) is below the decision threshold (${(d.threshold * 100).toFixed(0)}%) → Customer is eligible for a credit card.`
      : `Default probability (${(d.default_probability * 100).toFixed(1)}%) meets or exceeds the decision threshold (${(d.threshold * 100).toFixed(0)}%) → Credit card application NOT recommended.`
  );

  // ── Customer Profile ──
  const details = [
    ['Customer ID',    d.user_id],
    ['Credit Limit',   'NT\$ ' + fmt(d.limit_bal, 0)],
    ['Age',            d.age + ' years'],
    ['Gender',         d.sex],
    ['Education',      d.education],
    ['Marital Status', d.marriage],
    ['Recent Pay Status', payStatusLabel(d.pay_0).text],
  ];
  const dl = document.getElementById('customerDetails');
  dl.innerHTML = details.map(([k, v]) => `
    <div class="detail-row">
      <span class="detail-key">${k}</span>
      <span class="detail-val">${v}</span>
    </div>`).join('');

  // ── Score ──
  const score = d.credit_health_score;
  setText('scoreNumber',   score);
  setText('scoreCategory', d.score_category);
  setText('scoreRisk',     d.risk_label);

  // Ring
  const circumference = 2 * Math.PI * 50; // r=50 → ~314
  const offset = circumference * (1 - score / 100);
  const ring = document.getElementById('ringFill');
  ring.style.strokeDashoffset = offset;
  ring.style.stroke = scoreColor(score);

  // Progress bar
  document.getElementById('progressFill').style.width = `${score}%`;

  // Category color
  const catEl = document.getElementById('scoreCategory');
  catEl.style.color = scoreColor(score);

  // ── Probabilities ──
  setText('defaultProb',  (d.default_probability   * 100).toFixed(2) + '%');
  setText('noDefaultProb',(d.no_default_probability * 100).toFixed(2) + '%');
  setText('thresholdVal',  (d.threshold * 100).toFixed(0) + '%');
  setText('modelDecision', isApproved ? '✅ APPROVED' : '❌ NOT APPROVED');
  document.getElementById('defaultBar').style.width   = `${d.default_probability   * 100}%`;
  document.getElementById('noDefaultBar').style.width = `${d.no_default_probability * 100}%`;

  // ── Payment History Table ──
  const months = ['Sep (Recent)', 'Aug', 'Jul', 'Jun', 'May', 'Apr (Oldest)'];
  const payKeys  = ['pay_0','pay_2','pay_3','pay_4','pay_5','pay_6'];
  const billKeys = ['bill_amt1','bill_amt2','bill_amt3','bill_amt4','bill_amt5','bill_amt6'];
  const paidKeys = ['pay_amt1','pay_amt2','pay_amt3','pay_amt4','pay_amt5','pay_amt6'];

  const tbody = document.getElementById('payHistoryBody');
  tbody.innerHTML = months.map((m, i) => {
    const st = payStatusLabel(d[payKeys[i]]);
    return `
      <tr>
        <td>${m}</td>
        <td><span class="${st.cls}">${st.text}</span></td>
        <td>NT\$ ${fmt(d[billKeys[i]], 0)}</td>
        <td>NT\$ ${fmt(d[paidKeys[i]], 0)}</td>
      </tr>`;
  }).join('');

  // ── Prediction History Table ──
  const phBody = document.getElementById('predHistoryBody');
  if (!history || history.length === 0) {
    phBody.innerHTML = '<tr><td colspan="6" class="empty-row">No previous checks found.</td></tr>';
  } else {
    phBody.innerHTML = history.map((h, i) => {
      const cls = h.credit_card_status === 'APPROVED' ? 'status-approved' : 'status-rejected';
      const dt  = new Date(h.prediction_date).toLocaleString('en-IN');
      return `
        <tr>
          <td>${i + 1}</td>
          <td>${dt}</td>
          <td>${(h.default_probability   * 100).toFixed(2)}%</td>
          <td>${(h.no_default_probability * 100).toFixed(2)}%</td>
          <td>${h.estimated_credit_score}/100</td>
          <td><span class="${cls}">${h.credit_card_status}</span></td>
        </tr>`;
    }).join('');
  }

  // Show results
  document.getElementById('results').style.display = 'block';
  document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}


// ─── Score Color ────────────────────────────────────────────────
function scoreColor(s) {
  if (s >= 80) return '#3fb950';   // green
  if (s >= 60) return '#56d364';   // light green
  if (s >= 40) return '#e3b341';   // yellow
  if (s >= 20) return '#f0883e';   // orange
  return '#f85149';                 // red
}


// ─── Allow Enter key ────────────────────────────────────────────
document.getElementById('userId').addEventListener('keydown', function (e) {
  if (e.key === 'Enter') checkEligibility();
});
