/**
 * RemitMind - Main Web Application Engine
 * Connects directly to FastAPI backend (/api/v1/...) with robust offline fallback.
 * Zero Emojis - Full Light/Dark Theme Support.
 */

const API_BASE = window.location.protocol.startsWith('http') 
  ? window.location.origin 
  : 'http://localhost:8000';

// In-Memory Database for Demo & Local Fallback State
const APP_STATE = {
  transfers: [
    {
      id: 'TRX-9801',
      date: '2026-10-03 18:24',
      sender: 'Rahim Sheikh (Dubai)',
      receiver: 'Amina Begum (Sylhet)',
      corridor: 'AED_BDT',
      amountSrc: '2,000 AED',
      amountBDT: 67780,
      feeBDT: 1220,
      score: 14,
      status: 'completed',
      reasonCodes: ['RECURRING_MATCH', 'VERIFIED_DEVICE'],
      method: 'Visa •••• 4242'
    },
    {
      id: 'TRX-9802',
      date: '2026-10-03 19:10',
      sender: 'Kamil Hossain (Riyadh)',
      receiver: 'Fatema Khatun (Chittagong)',
      corridor: 'SAR_BDT',
      amountSrc: '3,500 SAR',
      amountBDT: 114500,
      feeBDT: 2170,
      score: 22,
      status: 'completed',
      reasonCodes: ['TRUSTED_ACCOUNT'],
      method: 'Mastercard •••• 8891'
    },
    {
      id: 'TRX-9803',
      date: '2026-10-03 19:45',
      sender: 'New Account #4412 (Kuala Lumpur)',
      receiver: 'First-Time Recipient #772 (Dhaka)',
      corridor: 'MYR_BDT',
      amountSrc: '4,800 MYR',
      amountBDT: 133200,
      feeBDT: 2530,
      score: 78,
      status: 'in_review',
      reasonCodes: ['NEW_RECEIVER', 'VELOCITY_3X', 'NEW_DEVICE'],
      method: 'GCC Mada •••• 1120'
    }
  ],
  selectedTiming: 'best',
  activeCorridor: 'AED_BDT'
};

const FX_CONFIG = {
  AED_BDT: { name: 'UAE Dirham', symbol: 'AED', nowRate: 32.85, bestRate: 33.85, bestDay: 'Thursday (Oct 08)', feeNow: 0.02, feeBest: 0.018, savings: 1380 },
  SAR_BDT: { name: 'Saudi Riyal', symbol: 'SAR', nowRate: 32.10, bestRate: 32.95, bestDay: 'Wednesday (Oct 07)', feeNow: 0.022, feeBest: 0.019, savings: 1120 },
  MYR_BDT: { name: 'Malaysian Ringgit', symbol: 'MYR', nowRate: 27.40, bestRate: 28.15, bestDay: 'Thursday (Oct 08)', feeNow: 0.019, feeBest: 0.016, savings: 940 },
  EUR_BDT: { name: 'Euro / Italy', symbol: 'EUR', nowRate: 133.50, bestRate: 136.40, bestDay: 'Friday (Oct 09)', feeNow: 0.015, feeBest: 0.013, savings: 2450 },
  USD_BDT: { name: 'US Dollar', symbol: 'USD', nowRate: 121.20, bestRate: 123.80, bestDay: 'Wednesday (Oct 07)', feeNow: 0.018, feeBest: 0.015, savings: 1820 }
};

document.addEventListener('DOMContentLoaded', () => {
  initAppTheme();
  initAppNavigation();
  initPaymentGateway();
  initAnalystQueue();
  initReceiverApp();
  initAgentApp();
  initCopilot();
  syncTransfersWithBackend();
});

/* ==========================================================================
   1. Theme Management (Light / Dark Mode)
   ========================================================================== */
function initAppTheme() {
  const themeBtn = document.getElementById('app-theme-btn');
  const storedTheme = localStorage.getItem('remitmind_theme') || 'dark';

  document.documentElement.setAttribute('data-theme', storedTheme);
  updateAppThemeIcon(storedTheme);

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('remitmind_theme', next);
      updateAppThemeIcon(next);
      showAppToast(`Switched to ${next === 'dark' ? 'Dark' : 'Light'} Mode`);
    });
  }
}

function updateAppThemeIcon(theme) {
  const container = document.getElementById('app-theme-icon');
  if (!container) return;

  if (theme === 'light') {
    container.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    `;
  } else {
    container.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
    `;
  }
}

/* ==========================================================================
   2. Tabbed Navigation
   ========================================================================== */
function initAppNavigation() {
  const tabs = document.querySelectorAll('.app-nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetView = tab.dataset.view;
      document.querySelectorAll('.app-view').forEach(view => {
        if (view.id === `view-${targetView}`) {
          view.classList.add('active');
        } else {
          view.classList.remove('active');
        }
      });
    });
  });

  const hash = window.location.hash.replace('#', '');
  if (hash) {
    const matchingTab = document.querySelector(`.app-nav-tab[data-view="${hash}"]`);
    if (matchingTab) matchingTab.click();
  }
}

/* ==========================================================================
   3. International Payment Gateway
   ========================================================================== */
function initPaymentGateway() {
  const corridorSelect = document.getElementById('pay-corridor');
  const amountInput = document.getElementById('pay-amount');
  const cardNumInput = document.getElementById('card-number');
  const cardHolderInput = document.getElementById('card-holder');
  const cardExpiryInput = document.getElementById('card-expiry');
  const timingChoices = document.querySelectorAll('.timing-choice-card');

  if (corridorSelect) {
    corridorSelect.addEventListener('change', (e) => {
      APP_STATE.activeCorridor = e.target.value;
      updatePaymentMath();
    });
  }

  if (amountInput) {
    amountInput.addEventListener('input', () => {
      updatePaymentMath();
    });
  }

  if (cardNumInput) {
    cardNumInput.addEventListener('input', (e) => {
      let val = e.target.value.replace(/\D/g, '').substring(0, 16);
      let formatted = val.match(/.{1,4}/g)?.join(' ') || val;
      e.target.value = formatted;
      document.getElementById('disp-card-number').innerText = formatted || '•••• •••• •••• ••••';
    });
  }

  if (cardHolderInput) {
    cardHolderInput.addEventListener('input', (e) => {
      document.getElementById('disp-card-holder').innerText = e.target.value.toUpperCase() || 'RAHIM SHEIKH';
    });
  }

  if (cardExpiryInput) {
    cardExpiryInput.addEventListener('input', (e) => {
      let val = e.target.value.replace(/\D/g, '').substring(0, 4);
      if (val.length >= 2) val = val.substring(0, 2) + '/' + val.substring(2);
      e.target.value = val;
      document.getElementById('disp-card-expiry').innerText = val || 'MM/YY';
    });
  }

  timingChoices.forEach(choice => {
    choice.addEventListener('click', () => {
      timingChoices.forEach(c => c.classList.remove('selected'));
      choice.classList.add('selected');
      APP_STATE.selectedTiming = choice.dataset.timing;
      updatePaymentMath();
    });
  });

  const goalRent = document.getElementById('app-goal-rent');
  const goalSchool = document.getElementById('app-goal-school');
  const goalSavings = document.getElementById('app-goal-savings');

  [goalRent, goalSchool, goalSavings].forEach(input => {
    if (input) {
      input.addEventListener('input', () => {
        balanceAppGoals(input);
        updatePaymentMath();
      });
    }
  });

  const payBtn = document.getElementById('btn-submit-payment');
  if (payBtn) {
    payBtn.addEventListener('click', (e) => {
      e.preventDefault();
      openOtpModal();
    });
  }

  setupOtpFlow();
  updatePaymentMath();
}

function balanceAppGoals(changed) {
  const rent = document.getElementById('app-goal-rent');
  const school = document.getElementById('app-goal-school');
  const savings = document.getElementById('app-goal-savings');
  if (!rent || !school || !savings) return;

  let total = Number(rent.value) + Number(school.value) + Number(savings.value);
  if (total !== 100) {
    let diff = 100 - total;
    if (changed !== savings) {
      savings.value = Math.max(0, Math.min(100, Number(savings.value) + diff));
    } else {
      rent.value = Math.max(0, Math.min(100, Number(rent.value) + diff));
    }
  }

  document.getElementById('app-val-rent').innerText = rent.value + '%';
  document.getElementById('app-val-school').innerText = school.value + '%';
  document.getElementById('app-val-savings').innerText = savings.value + '%';
}

async function updatePaymentMath() {
  const config = FX_CONFIG[APP_STATE.activeCorridor];
  const amountInput = document.getElementById('pay-amount');
  if (!config || !amountInput) return;

  const srcAmount = parseFloat(amountInput.value) || 2000;
  const isBest = APP_STATE.selectedTiming === 'best';

  // Try calling backend /plans/recommend if reachable
  try {
    const res = await fetch(`${API_BASE}/api/v1/plans/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sender_id: 'u_101',
        receiver_id: 'u_202',
        corridor: APP_STATE.activeCorridor,
        amount_src: srcAmount,
        goals: [
          { name: 'rent', share_pct: Number(document.getElementById('app-goal-rent')?.value || 50) },
          { name: 'school', share_pct: Number(document.getElementById('app-goal-school')?.value || 30) },
          { name: 'savings', share_pct: Number(document.getElementById('app-goal-savings')?.value || 20) }
        ]
      })
    });

    if (res.ok) {
      const plan = await res.json();
      const choiceData = isBest ? plan.send_best : plan.send_now;
      document.getElementById('summary-rate').innerText = `1 ${config.symbol} = BDT ${(choiceData.amount_bdt / srcAmount).toFixed(2)}`;
      document.getElementById('summary-fee').innerText = `BDT ${choiceData.fee_bdt.toLocaleString()}`;
      document.getElementById('summary-payout').innerText = `BDT ${choiceData.amount_bdt.toLocaleString()}`;
      document.getElementById('btn-pay-total-amount').innerText = `${srcAmount.toLocaleString()} ${config.symbol}`;

      const savingsTag = document.getElementById('disp-pay-savings-badge');
      if (savingsTag) {
        if (isBest && plan.expected_saving_bdt > 0) {
          savingsTag.innerText = `AI Optimized: + BDT ${plan.expected_saving_bdt.toLocaleString()} Extra Payout`;
          savingsTag.style.display = 'inline-block';
        } else {
          savingsTag.style.display = 'none';
        }
      }
      return;
    }
  } catch (err) {
    // Offline/file mode fallback continues below
  }

  // Local calculation fallback
  const rate = isBest ? config.bestRate : config.nowRate;
  const feePct = isBest ? config.feeBest : config.feeNow;
  const grossBDT = srcAmount * rate;
  const feeBDT = Math.round(grossBDT * feePct);
  const netBDT = Math.round(grossBDT - feeBDT);

  document.getElementById('summary-rate').innerText = `1 ${config.symbol} = BDT ${rate.toFixed(2)}`;
  document.getElementById('summary-fee').innerText = `BDT ${feeBDT.toLocaleString()} (${(feePct * 100).toFixed(1)}%)`;
  document.getElementById('summary-payout').innerText = `BDT ${netBDT.toLocaleString()}`;
  document.getElementById('btn-pay-total-amount').innerText = `${srcAmount.toLocaleString()} ${config.symbol}`;

  const savingsTag = document.getElementById('disp-pay-savings-badge');
  if (savingsTag) {
    if (isBest) {
      savingsTag.innerText = `AI Optimized: + BDT ${config.savings.toLocaleString()} Extra Payout`;
      savingsTag.style.display = 'inline-block';
    } else {
      savingsTag.style.display = 'none';
    }
  }
}

/* ==========================================================================
   4. 3D Secure / OTP Simulation & Backend Submission
   ========================================================================== */
function setupOtpFlow() {
  const modal = document.getElementById('otp-modal');
  const otpInputs = document.querySelectorAll('.otp-box');
  const confirmBtn = document.getElementById('btn-confirm-otp');
  const cancelBtn = document.getElementById('btn-cancel-otp');

  otpInputs.forEach((input, index) => {
    input.addEventListener('keyup', (e) => {
      if (e.key >= '0' && e.key <= '9') {
        if (index < otpInputs.length - 1) otpInputs[index + 1].focus();
      } else if (e.key === 'Backspace') {
        if (index > 0) otpInputs[index - 1].focus();
      }
    });
  });

  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      modal.classList.remove('open');
    });
  }

  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
      modal.classList.remove('open');
      executePaymentWithBackend();
    });
  }
}

function openOtpModal() {
  const modal = document.getElementById('otp-modal');
  if (modal) {
    modal.classList.add('open');
    document.querySelector('.otp-box')?.focus();
  }
}

async function executePaymentWithBackend() {
  const amountInput = document.getElementById('pay-amount');
  const srcAmount = parseFloat(amountInput.value) || 2000;
  const config = FX_CONFIG[APP_STATE.activeCorridor];
  const simulateAnomaly = document.getElementById('chk-simulate-anomaly')?.checked || false;
  const receiverName = document.getElementById('pay-receiver-name')?.value || 'Amina Begum (Sylhet)';

  let transferPayload = {
    sender_id: 'u_101',
    receiver_id: 'u_recv_001',
    corridor: APP_STATE.activeCorridor,
    amount_src: srcAmount,
    device_id: simulateAnomaly ? 'dev_emulator_suspicious' : 'dev_dubai_trusted',
    channel: 'app',
    simulate_anomaly: simulateAnomaly
  };

  try {
    const res = await fetch(`${API_BASE}/api/v1/transfers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(transferPayload)
    });

    if (res.ok) {
      const data = await res.json();
      const localTrx = {
        id: data.transfer_id,
        date: new Date().toISOString().replace('T', ' ').substring(0, 16),
        sender: 'Rahim Sheikh (Dubai)',
        receiver: receiverName,
        corridor: APP_STATE.activeCorridor,
        amountSrc: `${srcAmount.toLocaleString()} ${config.symbol}`,
        amountBDT: data.amount_bdt || Math.round(srcAmount * config.bestRate * 0.98),
        feeBDT: data.fee_bdt || Math.round(srcAmount * config.bestRate * 0.02),
        score: data.risk_score,
        status: data.status,
        reasonCodes: data.reason_codes || ['CORRIDOR_VERIFIED'],
        method: 'Visa •••• 4242'
      };

      APP_STATE.transfers.unshift(localTrx);
      renderLedgerTable();
      renderAnalystAlerts();

      if (data.status === 'completed') {
        showReceiptModal(localTrx);
        showAppToast(`Payment of ${localTrx.amountSrc} Authorized via FastAPI Backend! Status: COMPLETED`);
      } else {
        showAppToast(`Payment of ${localTrx.amountSrc} Processed! Isolation Forest Risk Score: ${data.risk_score}. Routed to Review.`);
        document.querySelector('.app-nav-tab[data-view="analyst"]')?.click();
      }
      return;
    }
  } catch (err) {
    console.warn('Backend not responding, falling back to local simulation:', err);
  }

  // Local fallback
  const rate = APP_STATE.selectedTiming === 'best' ? config.bestRate : config.nowRate;
  const netBDT = Math.round(srcAmount * rate * 0.98);
  const riskScore = simulateAnomaly || srcAmount >= 6000 ? 78 : 16;
  const status = riskScore >= 40 ? 'in_review' : 'completed';

  const newTrx = {
    id: `TRX-${Math.floor(1000 + Math.random() * 9000)}`,
    date: new Date().toISOString().replace('T', ' ').substring(0, 16),
    sender: 'Rahim Sheikh (Dubai)',
    receiver: receiverName,
    corridor: APP_STATE.activeCorridor,
    amountSrc: `${srcAmount.toLocaleString()} ${config.symbol}`,
    amountBDT: netBDT,
    feeBDT: Math.round(srcAmount * rate * 0.02),
    score: riskScore,
    status: status,
    reasonCodes: riskScore >= 40 ? ['NEW_DEVICE', 'VELOCITY_3X'] : ['CORRIDOR_VERIFIED'],
    method: 'Visa •••• 4242'
  };

  APP_STATE.transfers.unshift(newTrx);
  renderLedgerTable();
  renderAnalystAlerts();

  if (status === 'completed') {
    showReceiptModal(newTrx);
    showAppToast(`Payment of ${newTrx.amountSrc} Authorized! Instant Delivery Confirmed.`);
  } else {
    showAppToast(`Payment of ${newTrx.amountSrc} Received! Routed to Risk Analyst Queue.`);
    document.querySelector('.app-nav-tab[data-view="analyst"]')?.click();
  }
}

function showReceiptModal(trx) {
  const modal = document.getElementById('receipt-modal');
  if (!modal) return;

  document.getElementById('rec-trx-id').innerText = trx.id;
  document.getElementById('rec-amount-src').innerText = trx.amountSrc;
  document.getElementById('rec-amount-bdt').innerText = `BDT ${trx.amountBDT.toLocaleString()}`;
  document.getElementById('rec-receiver').innerText = trx.receiver;
  document.getElementById('rec-status').innerText = 'COMPLETED';

  modal.classList.add('open');

  document.getElementById('btn-close-receipt')?.addEventListener('click', () => {
    modal.classList.remove('open');
  });
}

/* ==========================================================================
   5. Analyst Operations Console & Adversarial Attack Studio
   ========================================================================== */
function initAnalystQueue() {
  renderAnalystAlerts();
}

async function renderAnalystAlerts() {
  const container = document.getElementById('analyst-queue-container');
  const countEl = document.getElementById('analyst-queue-count');
  if (!container) return;

  // Try fetching alerts from backend /api/v1/analyst/alerts
  try {
    const res = await fetch(`${API_BASE}/api/v1/analyst/alerts?status=open`);
    if (res.ok) {
      const serverAlerts = await res.json();
      if (countEl) countEl.innerText = `${serverAlerts.length} Active Interceptions`;
      if (serverAlerts.length > 0) {
        container.innerHTML = '';
        serverAlerts.forEach(alert => {
          const card = document.createElement('div');
          card.className = 'step-card';
          card.style.marginBottom = '16px';
          card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
              <div>
                <span style="font-family:var(--font-mono); font-size:0.8rem; color:var(--ai-cyan); font-weight:700;">${alert.alert_id} &bull; ${alert.transfer_id}</span>
                <h4 style="font-size:1.1rem; color:var(--text-primary); margin-top:2px;">${alert.sender_id} &rarr; ${alert.receiver_id}</h4>
                <span style="font-size:0.82rem; color:var(--text-secondary);">Payout: BDT ${alert.amount_bdt.toLocaleString()}</span>
              </div>
              <div style="text-align:right;">
                <span class="risk-status-badge risk-badge-high">Anomaly Score: ${alert.score}</span>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">${alert.model_version}</div>
              </div>
            </div>

            <div style="margin-bottom:14px;">
              <span style="font-size:0.75rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase;">Extracted Anomaly Reasons:</span>
              <div class="reason-codes-grid">
                ${(alert.reason_codes || []).map(r => `<span class="reason-tag">${r}</span>`).join('')}
              </div>
            </div>

            <div class="action-buttons-row">
              <button class="btn btn-secondary btn-sm" onclick="window.openSarModal('${alert.alert_id}', '${alert.transfer_id}', ${alert.score}, ${JSON.stringify(alert.reason_codes || []).replace(/"/g, '&quot;')})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <span>Inspect Forensic SAR</span>
              </button>
              <button class="btn btn-approve btn-sm" onclick="analystResolve('${alert.alert_id}', 'approve')">
                <span>Approve & Release</span>
              </button>
              <button class="btn btn-hold btn-sm" onclick="analystResolve('${alert.alert_id}', 'hold')">
                <span>Hold (24h)</span>
              </button>
              <button class="btn btn-escalate btn-sm" onclick="analystResolve('${alert.alert_id}', 'escalate')">
                <span>Escalate</span>
              </button>
            </div>
          `;
          container.appendChild(card);
        });
        return;
      }
    }
  } catch (e) {
    // Fall back to local queue
  }

  // Local fallback
  const flagged = APP_STATE.transfers.filter(t => t.status === 'in_review' || t.score >= 40);
  if (countEl) countEl.innerText = `${flagged.length} Active Cases`;

  if (flagged.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:40px; color:var(--text-muted);">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:12px; color:var(--upay-emerald);"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <div style="font-weight:700;">Risk Review Queue is Empty</div>
        <p style="font-size:0.85rem;">All incoming transfers have cleared automated safety thresholds.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = '';
  flagged.forEach(alert => {
    const card = document.createElement('div');
    card.className = 'step-card';
    card.style.marginBottom = '16px';
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
        <div>
          <span style="font-family:var(--font-mono); font-size:0.8rem; color:var(--ai-cyan); font-weight:700;">${alert.id}</span>
          <h4 style="font-size:1.1rem; color:var(--text-primary); margin-top:2px;">${alert.sender} &rarr; ${alert.receiver}</h4>
          <span style="font-size:0.82rem; color:var(--text-secondary);">${alert.amountSrc} &bull; Payout: BDT ${alert.amountBDT.toLocaleString()}</span>
        </div>
        <div style="text-align:right;">
          <span class="risk-status-badge risk-badge-high">Anomaly Score: ${alert.score}</span>
          <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Isolation Forest v1.0</div>
        </div>
      </div>

      <div style="margin-bottom:14px;">
        <span style="font-size:0.75rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase;">Extracted Anomaly Reasons:</span>
        <div class="reason-codes-grid">
          ${alert.reasonCodes.map(r => `<span class="reason-tag">${r}</span>`).join('')}
        </div>
      </div>

      <div class="action-buttons-row">
        <button class="btn btn-secondary btn-sm" onclick="window.openSarModal('${alert.id}', '${alert.id}', ${alert.score}, ${JSON.stringify(alert.reasonCodes).replace(/"/g, '&quot;')})">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          <span>Inspect Forensic SAR</span>
        </button>
        <button class="btn btn-approve btn-sm" onclick="analystResolve('${alert.id}', 'approve')">
          <span>Approve & Release</span>
        </button>
        <button class="btn btn-hold btn-sm" onclick="analystResolve('${alert.id}', 'hold')">
          <span>Hold for 24h</span>
        </button>
        <button class="btn btn-escalate btn-sm" onclick="analystResolve('${alert.id}', 'escalate')">
          <span>Escalate to Crimes Unit</span>
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

window.replayAttackScenario = async function(scenarioType) {
  showAppToast(`Replaying Adversarial Attack: ${scenarioType.replace('_', ' ').toUpperCase()}...`);

  try {
    const res = await fetch(`${API_BASE}/api/v1/dev/replay-attack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ attack_type: scenarioType })
    });

    if (res.ok) {
      const data = await res.json();
      renderWaterfallAttribution(data);

      const newTrx = {
        id: data.transfer_id,
        date: new Date().toISOString().replace('T', ' ').substring(0, 16),
        sender: scenarioType === 'account_takeover' ? 'Rahim Sheikh (Proxy ATO)' : (scenarioType === 'mule_fan_in' ? 'Mule Node 04' : 'Social Target'),
        receiver: scenarioType === 'mule_fan_in' ? 'Syndicate Wallet (u_recv_001)' : 'Unverified Beneficiary',
        corridor: data.corridor,
        amountSrc: `${data.corridor.split('_')[0]} ${data.amount_bdt.toLocaleString()}`,
        amountBDT: data.amount_bdt,
        feeBDT: Math.round(data.amount_bdt * 0.02),
        score: data.risk_score,
        status: data.decision,
        reasonCodes: data.reason_codes,
        method: 'GCC Mada •••• 1120'
      };

      APP_STATE.transfers.unshift(newTrx);
      renderLedgerTable();
      renderAnalystAlerts();

      showAppToast(`Attack Flagged! Hybrid Radar Score: ${data.risk_score}/100. Primary Code: ${data.reason_codes[0]}`);

      if (data.alert_id) {
        window.openSarModal(data.alert_id, data.transfer_id, data.risk_score, data.reason_codes, data.explanation);
      }
      return;
    }
  } catch (err) {
    console.warn("Backend attack replay error, using local simulation:", err);
  }

  // Local fallback simulation
  const localScore = scenarioType === 'mule_fan_in' ? 92 : (scenarioType === 'account_takeover' ? 88 : 76);
  const localReasons = scenarioType === 'mule_fan_in' 
    ? ['MULE_CLUSTER_FAN_IN', 'NEW_RECEIVER', 'VELOCITY_3X']
    : (scenarioType === 'account_takeover' ? ['NEW_DEVICE', 'VELOCITY_3X', 'AMOUNT_DEVIATION'] : ['OFF_HOURS_ANOMALY', 'NEW_RECEIVER']);

  const mockData = {
    scenario: scenarioType,
    transfer_id: `t_sim_${Math.floor(1000 + Math.random() * 9000)}`,
    risk_score: localScore,
    reason_codes: localReasons,
    amount_bdt: 95000,
    feature_attribution: [
      { feature: 'Velocity Acceleration', impact_points: 35 },
      { feature: 'Device Fingerprint Discrepancy', impact_points: 30 },
      { feature: 'Beneficiary Tenure', impact_points: 25 },
      { feature: 'Amount Deviation from Baseline', impact_points: 20 },
      { feature: 'Corridor Historical Prior', impact_points: -15 }
    ]
  };

  renderWaterfallAttribution(mockData);

  const fallbackTrx = {
    id: mockData.transfer_id,
    date: new Date().toISOString().replace('T', ' ').substring(0, 16),
    sender: 'Simulated Adversary',
    receiver: 'Flagged Wallet',
    corridor: 'AED_BDT',
    amountSrc: '3,200 AED',
    amountBDT: 95000,
    feeBDT: 1900,
    score: localScore,
    status: 'in_review',
    reasonCodes: localReasons,
    method: 'Visa •••• 9901'
  };
  APP_STATE.transfers.unshift(fallbackTrx);
  renderLedgerTable();
  renderAnalystAlerts();
  showAppToast(`Scenario Replayed: ${scenarioType} -> Intercepted with Score ${localScore}/100`);
};

function renderWaterfallAttribution(data) {
  const container = document.getElementById('attack-waterfall-container');
  if (!container) return;

  const attribution = data.feature_attribution || [];
  container.style.display = 'block';
  container.innerHTML = `
    <div class="waterfall-card">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
        <div>
          <span class="ticker-badge" style="background:rgba(244,63,94,0.18); color:var(--accent-rose); font-size:0.75rem;">
            Anomaly Score: ${data.risk_score} / 100
          </span>
          <h4 style="font-size:1.05rem; color:var(--text-primary); margin:6px 0 2px 0;">
            Feature Attribution Waterfall &bull; ${data.transfer_id}
          </h4>
          <span style="font-size:0.78rem; color:var(--text-secondary);">${data.note || 'Isolation Forest marginal risk contributions.'}</span>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="this.closest('#attack-waterfall-container').style.display='none'">
          Dismiss Waterfall
        </button>
      </div>

      <div style="display:flex; flex-direction:column;">
        ${attribution.map(row => {
          const isDanger = row.impact_points >= 0;
          const pct = Math.min(100, Math.abs(row.impact_points) * 2.5);
          return `
            <div class="waterfall-row">
              <span style="font-weight:600; color:var(--text-primary); width:230px;">${row.feature}</span>
              <div class="waterfall-bar-track">
                <div class="waterfall-bar-fill" style="width:${pct}%; background:${isDanger ? 'var(--accent-rose)' : 'var(--upay-emerald)'};"></div>
              </div>
              <span class="waterfall-pts ${isDanger ? 'pts-danger' : 'pts-safe'}">
                ${row.impact_points > 0 ? '+' : ''}${row.impact_points} pts
              </span>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

window.openSarModal = async function(alertId, transferId, score, reasonCodes, cachedExplanation) {
  const modal = document.getElementById('sar-modal');
  const narrativeBox = document.getElementById('sar-narrative-content');
  const caseRef = document.getElementById('sar-case-ref');
  const closeBtn = document.getElementById('btn-close-sar');
  const approveBtn = document.getElementById('btn-sar-approve');
  const holdBtn = document.getElementById('btn-sar-hold');
  const escalateBtn = document.getElementById('btn-sar-escalate');

  if (!modal || !narrativeBox) return;

  if (caseRef) caseRef.innerText = `${alertId} (${transferId})`;
  modal.classList.add('open');

  if (closeBtn) {
    closeBtn.onclick = () => modal.classList.remove('open');
  }

  if (approveBtn) {
    approveBtn.onclick = () => {
      window.analystResolve(alertId, 'approve');
      modal.classList.remove('open');
    };
  }
  if (holdBtn) {
    holdBtn.onclick = () => {
      window.analystResolve(alertId, 'hold');
      modal.classList.remove('open');
    };
  }
  if (escalateBtn) {
    escalateBtn.onclick = () => {
      window.analystResolve(alertId, 'escalate');
      modal.classList.remove('open');
    };
  }

  if (cachedExplanation) {
    narrativeBox.innerText = cachedExplanation;
    return;
  }

  narrativeBox.innerText = "Querying Gemini 1.5 Pro Forensic Copilot for grounded AML brief...";

  try {
    const res = await fetch(`${API_BASE}/api/v1/ai/explain-risk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transfer_id: transferId,
        score: score,
        reason_codes: reasonCodes || [],
        corridor: 'AED_BDT',
        amount_bdt: 95000.0,
        model: 'gemini-1.5-pro'
      })
    });

    if (res.ok) {
      const data = await res.json();
      narrativeBox.innerText = data.narrative;
      return;
    }
  } catch (err) {}

  narrativeBox.innerText = `COMPLIANCE FORENSIC REPORT — CASE ${alertId}\n` +
    `Reference Transfer: ${transferId} | Composite Anomaly Score: ${score}/100\n` +
    `Primary Anomaly Drivers: ${(reasonCodes || []).join(', ')}\n\n` +
    `Analyst Finding: Multiple risk vector deviations detected exceeding safe operational threshold (40.0).\n` +
    `In accordance with Zero Auto-Blocking policy, transaction is placed in human review queue.\n` +
    `Recommended Action: Request biometric National ID verification before fund disbursement.`;
};

window.analystResolve = async function(id, decision) {
  try {
    await fetch(`${API_BASE}/api/v1/analyst/alerts/${id}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': 'upay-risk-secret' },
      body: JSON.stringify({ decision: decision, is_fraud: decision !== 'approve' })
    });
  } catch (e) {}

  const item = APP_STATE.transfers.find(t => t.id === id);
  if (item) {
    item.status = decision === 'approve' ? 'completed' : (decision === 'hold' ? 'held' : 'escalated');
  }
  renderAnalystAlerts();
  renderLedgerTable();
  showAppToast(`Decision: ${decision.toUpperCase()} recorded for ${id}. Label saved into review_actions.`);
};

/* ==========================================================================
   6. Receiver Portal in App
   ========================================================================== */
function initReceiverApp() {
  const langToggle = document.getElementById('app-rcv-lang-toggle');
  const audioBtn = document.getElementById('app-btn-voice');

  if (langToggle) {
    langToggle.addEventListener('change', async (e) => {
      const isEnglish = e.target.checked;
      const textEl = document.getElementById('app-rcv-statement');
      
      try {
        const res = await fetch(`${API_BASE}/api/v1/receiver/u_recv_001/summary?lang=${isEnglish ? 'en' : 'bn'}`);
        if (res.ok) {
          const data = await res.json();
          textEl.innerText = data.summary;
          return;
        }
      } catch (err) {}

      if (isEnglish) {
        textEl.innerText = 'A total of BDT 67,780 was safely received from Rahim Sheikh in Dubai. Prepaid by sender with zero hidden charges.';
      } else {
        textEl.innerText = 'দুবাই থেকে রহিম ভাইয়ের পাঠানো মোট ৬৭,৭৮০ টাকা নিরাপদে আপনার উপায় একাউন্টে জমা হয়েছে। কোনো লুকানো চার্জ কাটা হয়নি।';
      }
    });
  }

  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      if ('speechSynthesis' in window) {
        const text = 'দুবাই থেকে রহিম ভাইয়ের পাঠানো মোট ৬৭,৭৮০ টাকা নিরাপদে আপনার উপায় একাউন্টে জমা হয়েছে।';
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'bn-BD';
        window.speechSynthesis.speak(utterance);
      }
      showAppToast('Bangla voice summary played.');
    });
  }
}

/* ==========================================================================
   7. Agent Liquidity in App
   ========================================================================== */
function initAgentApp() {
  const slider = document.getElementById('app-agent-slider');
  const valText = document.getElementById('app-agent-cash-val');

  if (slider && valText) {
    slider.addEventListener('input', (e) => {
      const val = Number(e.target.value);
      valText.innerText = `BDT ${val.toLocaleString()}`;
      const peakEid = 420000;
      const shortfall = Math.max(0, peakEid - val);
      const deficitEl = document.getElementById('app-agent-deficit');
      if (deficitEl) {
        deficitEl.innerText = shortfall > 0 ? `BDT ${shortfall.toLocaleString()} Shortfall` : 'Adequate Liquidity';
        deficitEl.style.color = shortfall > 0 ? 'var(--accent-rose)' : 'var(--upay-emerald-light)';
      }
    });
  }
}

/* ==========================================================================
   8. Full Audit Ledger Sync
   ========================================================================== */
async function syncTransfersWithBackend() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/transfers?limit=25`);
    if (res.ok) {
      const serverTrx = await res.json();
      if (serverTrx.length > 0) {
        APP_STATE.transfers = serverTrx.map(t => ({
          id: t.id,
          date: t.created_at ? t.created_at.substring(0, 16) : '2026-10-03 20:00',
          sender: t.sender_id,
          receiver: t.receiver_id,
          corridor: t.corridor,
          amountSrc: `${t.amount_src} ${t.corridor.split('_')[0]}`,
          amountBDT: t.amount_bdt || 67780,
          feeBDT: t.fee_bdt || 1220,
          score: t.risk_score || 15,
          status: t.status || 'completed',
          reasonCodes: ['AUDITED'],
          method: 'Visa •••• 4242'
        }));
      }
    }
  } catch (err) {
    // Offline mode continues with local transfers
  }
  renderLedgerTable();
}

function renderLedgerTable() {
  const tbody = document.getElementById('ledger-tbody');
  if (!tbody) return;

  tbody.innerHTML = '';
  APP_STATE.transfers.forEach(trx => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-family:var(--font-mono); font-weight:700; color:var(--ai-cyan);">${trx.id}</td>
      <td style="font-size:0.8rem; color:var(--text-muted);">${trx.date}</td>
      <td><strong>${trx.sender}</strong></td>
      <td>${trx.receiver}</td>
      <td><strong>${trx.amountSrc}</strong> <span style="font-size:0.75rem; color:var(--text-secondary);">(BDT ${trx.amountBDT.toLocaleString()})</span></td>
      <td>
        <span class="badge-status ${trx.status}">
          ${trx.status.replace('_', ' ')}
        </span>
      </td>
      <td style="font-family:var(--font-mono); font-weight:700; color:${trx.score >= 40 ? 'var(--accent-rose)' : 'var(--upay-emerald-light)'};">
        ${trx.score}/100
      </td>
      <td>
        ${trx.status === 'in_review' ? `
          <button class="btn btn-secondary btn-sm" onclick="document.querySelector('.app-nav-tab[data-view=\\'analyst\\']').click();">Inspect</button>
        ` : `<span style="font-size:0.75rem; color:var(--text-muted);">Audited</span>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function showAppToast(msg) {
  let toast = document.getElementById('toast-notification');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = 'toast-notice';
    document.body.appendChild(toast);
  }
  toast.innerText = msg;
  toast.style.display = 'flex';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 4000);
}

/* ==========================================================================
   9. AI Copilot & Conversational Intelligence (Grounded LLM)
   ========================================================================== */
function initCopilot() {
  const modelSelect = document.getElementById('copilot-model-select');
  // Load models if endpoint available
  fetch(`${API_BASE}/api/v1/ai/models`)
    .then(r => r.json())
    .then(models => {
      if (modelSelect && Array.isArray(models) && models.length > 0) {
        modelSelect.innerHTML = models.map(m => `<option value="${m.id}">${m.name}</option>`).join('');
      }
    })
    .catch(() => {});
}

window.toggleCopilotDrawer = function(forceOpen) {
  const drawer = document.getElementById('copilot-drawer');
  if (!drawer) return;
  if (typeof forceOpen === 'boolean') {
    if (forceOpen) drawer.classList.add('open');
    else drawer.classList.remove('open');
  } else {
    drawer.classList.toggle('open');
  }
  if (drawer.classList.contains('open')) {
    document.getElementById('copilot-user-input')?.focus();
  }
};

window.askCopilotDirect = function(promptText) {
  window.toggleCopilotDrawer(true);
  const input = document.getElementById('copilot-user-input');
  if (input) {
    input.value = promptText;
    window.sendCopilotMsg();
  }
};

window.sendCopilotMsg = async function() {
  const input = document.getElementById('copilot-user-input');
  const messagesArea = document.getElementById('copilot-messages-area');
  const modelSelect = document.getElementById('copilot-model-select');
  if (!input || !messagesArea) return;

  const userText = input.value.trim();
  if (!userText) return;

  const selectedModel = modelSelect ? modelSelect.value : 'gemini-1.5-flash';

  // 1. Render user message
  const userMsgEl = document.createElement('div');
  userMsgEl.className = 'copilot-msg user';
  userMsgEl.innerText = userText;
  messagesArea.appendChild(userMsgEl);
  input.value = '';
  messagesArea.scrollTop = messagesArea.scrollHeight;

  // 2. Render typing indicator
  const botMsgEl = document.createElement('div');
  botMsgEl.className = 'copilot-msg bot';
  botMsgEl.innerHTML = `<span style="color:var(--text-muted); font-style:italic;">RemitMind AI (${selectedModel}) thinking...</span>`;
  messagesArea.appendChild(botMsgEl);
  messagesArea.scrollTop = messagesArea.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/api/v1/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userText,
        model: selectedModel,
        language: /[\u0980-\u09FF]/.test(userText) ? 'bn' : 'en'
      })
    });

    if (res.ok) {
      const data = await res.json();
      const factsHtml = (data.grounded_facts && data.grounded_facts.length > 0)
        ? `<div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:10px;">` +
          data.grounded_facts.map(f => `<span class="ticker-badge" style="background:rgba(6,182,212,0.12); color:var(--ai-cyan); font-size:0.7rem; padding:2px 8px;">${f}</span>`).join('') +
          `</div>`
        : '';
      
      botMsgEl.innerHTML = `
        <div style="font-size:0.75rem; color:var(--upay-emerald-light); font-weight:700; margin-bottom:6px;">
          ${data.model_used} &bull; Grounded Evidence
        </div>
        <div style="white-space:pre-wrap; line-height:1.5;">${data.reply}</div>
        ${factsHtml}
      `;
      messagesArea.scrollTop = messagesArea.scrollHeight;
      return;
    }
  } catch (err) {
    // Offline local intelligent fallback
  }

  // Fallback response generator
  let fallbackReply = "I am operating in local fallback mode. RemitMind AI analyzes 14-day FX trends, isolates transaction outliers without auto-blocking, and predicts agent cash-out demand.";
  const lower = userText.toLowerCase();
  if (lower.includes("aed") || lower.includes("when") || lower.includes("rate") || lower.includes("send")) {
    fallbackReply = "Optimal Window: Thursday (Oct 08) with guaranteed 1 AED = BDT 33.85. Transfer fee discounted to 1.8% (+ BDT 1,380 extra payout).";
  } else if (lower.includes("risk") || lower.includes("trx") || lower.includes("flag") || lower.includes("why")) {
    fallbackReply = "TRX-9803 flagged with Anomaly Score 78/100 due to rapid velocity acceleration and unverified hardware fingerprint. Routed to analyst queue under Zero Auto-Blocking policy.";
  } else if (userText.includes("বাংলা") || userText.includes("টাকা") || lower.includes("bangla")) {
    fallbackReply = "দুবাই থেকে রহিম ভাইয়ের পাঠানো মোট ৬৭,৭৮০ টাকা নিরাপদে আপনার একাউন্টে জমা হয়েছে। কোনো লুকানো চার্জ কাটা হয়নি।";
  } else if (lower.includes("agent") || lower.includes("eid") || lower.includes("cash")) {
    fallbackReply = "Agent #AG-05 Balaganj: Current Cash BDT 300,000 vs. Projected Eid Peak Demand BDT 420,000. Shortfall of BDT 120,000 detected. Regional vault dispatch recommended.";
  }

  botMsgEl.innerHTML = `
    <div style="font-size:0.75rem; color:var(--text-muted); font-weight:700; margin-bottom:6px;">
      RemitMind Local Engine &bull; Zero Downtime Fallback
    </div>
    <div style="white-space:pre-wrap; line-height:1.5;">${fallbackReply}</div>
  `;
  messagesArea.scrollTop = messagesArea.scrollHeight;
};

