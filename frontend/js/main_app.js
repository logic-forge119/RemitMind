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
  initUserSession();
  syncTransfersWithBackend();
});

/* ==========================================================================
   0. User Session Management
   ========================================================================== */
function initUserSession() {
  const sessionBadge = document.getElementById('user-session-badge');
  const loginBtn = document.getElementById('btn-app-login');
  const avatarInitial = document.getElementById('user-avatar-initial');
  const displayName = document.getElementById('user-display-name');

  const storedUser = localStorage.getItem('remitmind_user');
  if (storedUser) {
    try {
      const user = JSON.parse(storedUser);
      if (sessionBadge && loginBtn) {
        sessionBadge.style.display = 'inline-flex';
        loginBtn.style.display = 'none';
        if (avatarInitial) avatarInitial.textContent = (user.name || 'U').charAt(0).toUpperCase();
        if (displayName) displayName.textContent = `${user.name} (${user.country || user.role})`;
      }
    } catch (e) {
      console.warn('Failed to parse user session:', e);
    }
  } else {
    if (sessionBadge) sessionBadge.style.display = 'none';
    if (loginBtn) loginBtn.style.display = 'inline-flex';
  }
}

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
  const themeBtn = document.getElementById('app-theme-btn');

  if (themeBtn) {
    const isDark = theme === 'dark';
    themeBtn.setAttribute('title', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
    themeBtn.setAttribute('aria-label', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
  }

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

      if (targetView === 'syndicate') loadGraphIntelligence();
      else if (targetView === 'resilience') loadResilienceDivisions();
      else if (targetView === 'simulator') updateThreatMeter();
    });
  });

  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get('view');
  const hash = window.location.hash.replace('#', '');
  const activeView = viewParam || hash;

  if (activeView) {
    const matchingTab = document.querySelector(`.app-nav-tab[data-view="${activeView}"]`);
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
      const disp = document.getElementById('disp-card-number');
      if (disp) disp.innerText = formatted || '•••• •••• •••• ••••';
    });
  }

  if (cardHolderInput) {
    cardHolderInput.addEventListener('input', (e) => {
      const disp = document.getElementById('disp-card-holder');
      if (disp) disp.innerText = e.target.value.toUpperCase() || 'RAHIM SHEIKH';
    });
  }

  if (cardExpiryInput) {
    cardExpiryInput.addEventListener('input', (e) => {
      let val = e.target.value.replace(/\D/g, '').substring(0, 4);
      if (val.length >= 2) val = val.substring(0, 2) + '/' + val.substring(2);
      e.target.value = val;
      const disp = document.getElementById('disp-card-expiry');
      if (disp) disp.innerText = val || 'MM/YY';
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
    payBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      await triggerPreFlightShieldCheck();
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
    const res = await fetch(`${API_BASE}/api/v1/analyst/alerts?status=open`, {
      headers: { 'X-API-Key': 'upay-risk-secret' }
    });
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
                <span>Forensic SAR</span>
              </button>
              <button class="btn btn-secondary btn-sm" onclick="openBfiuModal('${alert.alert_id}', '${alert.transfer_id}', ${alert.score}, ${alert.amount_bdt || 95000}, ${JSON.stringify(alert.reason_codes || []).replace(/"/g, '&quot;')})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--upay-emerald-light)" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                <span>BFIU Form 2</span>
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

      if (audioBtn && !audioBtn.classList.contains('playing')) {
        const span = audioBtn.querySelector('span');
        if (span) span.innerText = isEnglish ? 'Play Voice Summary (English)' : 'Play Voice Summary (বাংলায় শুনুন)';
      }
    });
  }

  let currentAppAudio = null;

  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      const isEnglish = langToggle?.checked || false;
      const originalHtml = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <span>${isEnglish ? 'Play Voice Summary (English)' : 'Play Voice Summary (বাংলায় শুনুন)'}</span>
      `;

      // Pause if already playing
      if (currentAppAudio && !currentAppAudio.paused) {
        currentAppAudio.pause();
        currentAppAudio.currentTime = 0;
        currentAppAudio = null;
        audioBtn.innerHTML = originalHtml;
        audioBtn.classList.remove('playing');
        showAppToast(isEnglish ? 'Voice playback paused.' : 'ভয়েস প্লেব্যাক থামানো হয়েছে।');
        return;
      }

      audioBtn.classList.add('playing');
      audioBtn.innerHTML = `
        <span class="voice-wave-bars">
          <span class="voice-wave-bar"></span>
          <span class="voice-wave-bar"></span>
          <span class="voice-wave-bar"></span>
          <span class="voice-wave-bar"></span>
        </span>
        <span>${isEnglish ? 'Playing Audio... (Click to Pause)' : 'ভয়েস অডিও বাজছে... (থামাতে ক্লিক করুন)'}</span>
      `;

      const audioSrc = isEnglish ? 'assets/english_voice_summary.mp3' : 'assets/bangla_voice_summary.mp3';
      const audio = new Audio(audioSrc);
      currentAppAudio = audio;

      const resetBtn = () => {
        audioBtn.innerHTML = originalHtml;
        audioBtn.classList.remove('playing');
        currentAppAudio = null;
      };

      audio.onended = () => {
        resetBtn();
        showAppToast(isEnglish ? 'Voice summary finished.' : 'বাংলা ভয়েস বিবরণ সমাপ্ত হয়েছে।');
      };

      audio.onerror = (err) => {
        console.warn('Audio play error, falling back to Web Speech Synthesis:', err);
        fallbackAppSpeech(isEnglish, audioBtn, originalHtml);
      };

      audio.play().catch((err) => {
        console.warn('Audio play blocked, falling back to Web Speech Synthesis:', err);
        fallbackAppSpeech(isEnglish, audioBtn, originalHtml);
      });
    });
  }
}

function fallbackAppSpeech(isEnglish, btn, originalHtml) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const text = isEnglish 
      ? 'A total of 67,780 Taka was safely received from Rahim Sheikh in Dubai. Prepaid by sender with zero hidden charges.'
      : 'দুবাই থেকে রহিম ভাইয়ের পাঠানো মোট ৬৭ হাজার ৭৮০ টাকা নিরাপদে আপনার উপায় একাউন্টে জমা হয়েছে। কোনো লুকানো চার্জ কাটা হয়নি।';

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = isEnglish ? 'en-US' : 'bn-BD';
    utterance.rate = 0.95;

    const voices = window.speechSynthesis.getVoices();
    if (isEnglish) {
      const enVoice = voices.find(v => v.lang.startsWith('en'));
      if (enVoice) utterance.voice = enVoice;
    } else {
      const bnVoice = voices.find(v => v.lang.startsWith('bn') || v.name.includes('Bangla') || v.name.includes('Bengali'));
      if (bnVoice) utterance.voice = bnVoice;
    }

    utterance.onend = () => {
      btn.innerHTML = originalHtml;
      btn.classList.remove('playing');
    };
    utterance.onerror = () => {
      btn.innerHTML = originalHtml;
      btn.classList.remove('playing');
    };

    window.speechSynthesis.speak(utterance);
    showAppToast(isEnglish ? 'Speech synthesis active.' : 'বাংলা ভয়েস প্লে হচ্ছে।');
  } else {
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.classList.remove('playing');
      showAppToast('Voice summary completed.');
    }, 2500);
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

/* ==========================================================================
   AegisRisk Platform Extensions
   ========================================================================== */

/* --------------------------------------------------------------------------
   1. AegisShield Pre-Flight Safety Interception & 30s Cooling Window
   -------------------------------------------------------------------------- */
let shieldCountdownInterval = null;

async function triggerPreFlightShieldCheck() {
  const amountInput = document.getElementById('pay-amount');
  const srcAmount = parseFloat(amountInput ? amountInput.value : 0) || 2000;
  const memoInput = document.getElementById('pay-memo');
  const memoVal = memoInput ? memoInput.value : '';
  const simulateAnomaly = document.getElementById('chk-simulate-anomaly')?.checked || false;

  const payload = {
    sender_id: 'u_101',
    receiver_id: simulateAnomaly ? 'u_mule_scam_99' : 'u_recv_001',
    amount: srcAmount,
    corridor: APP_STATE.activeCorridor,
    memo: memoVal,
    device_id: simulateAnomaly ? 'dev_emulator_suspicious' : 'dev_dubai_trusted'
  };

  try {
    const res = await fetch(`${API_BASE}/api/v1/scamshield/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      if (data.intercept) {
        openShieldModal(data);
        return;
      }
    }
  } catch (err) {
    console.warn('ScamShield API check fallback:', err);
    const lower = memoVal.toLowerCase();
    if (lower.includes('lottery') || lower.includes('prize') || lower.includes('hospital') || lower.includes('emergency') || lower.includes('police') || lower.includes('refund')) {
      openShieldModal({
        risk_level: 'critical',
        warning_message_en: 'CRITICAL ALERT: Transfer memo matches known social engineering scam signatures. Legitimate organizations never demand immediate upfront transfers.',
        warning_message_bn: 'জরুরি সতর্কতা: টাকা পাঠানোর কারণে প্রতারণামূলক ভাষা শনাক্ত হয়েছে। কোনো বৈধ প্রতিষ্ঠান কখনো অগ্রিম টাকা দাবি করে না।',
        cooling_off_seconds: 30
      });
      return;
    }
  }

  // If no intercept triggered, proceed directly to OTP
  openOtpModal();
}

function openShieldModal(data) {
  const modal = document.getElementById('shield-modal');
  if (!modal) {
    openOtpModal();
    return;
  }

  const badge = document.getElementById('shield-risk-badge');
  if (badge) {
    badge.innerText = (data.risk_level || 'critical').toUpperCase() + ' FRAUD RISK';
    badge.className = data.risk_level === 'high' ? 'shield-badge-high' : 'shield-badge-critical';
  }

  const msgEn = document.getElementById('shield-msg-en');
  if (msgEn) msgEn.innerText = data.warning_message_en || 'Elevated risk detected.';

  const msgBn = document.getElementById('shield-msg-bn');
  if (msgBn) msgBn.innerText = data.warning_message_bn || 'অতিরিক্ত ঝুঁকি শনাক্ত হয়েছে।';

  let remaining = data.cooling_off_seconds || 30;
  const countDisplay = document.getElementById('shield-countdown-display');
  const proceedBtn = document.getElementById('btn-shield-proceed');

  if (proceedBtn) {
    proceedBtn.disabled = true;
    proceedBtn.style.opacity = '0.5';
    proceedBtn.style.cursor = 'not-allowed';
    proceedBtn.innerText = `I Understand, Proceed (${remaining}s)`;
  }

  if (countDisplay) countDisplay.innerText = `${remaining}s`;

  if (shieldCountdownInterval) clearInterval(shieldCountdownInterval);

  shieldCountdownInterval = setInterval(() => {
    remaining -= 1;
    if (countDisplay) countDisplay.innerText = `${remaining}s`;
    if (proceedBtn) proceedBtn.innerText = `I Understand, Proceed (${remaining}s)`;

    if (remaining <= 0) {
      clearInterval(shieldCountdownInterval);
      if (countDisplay) countDisplay.innerText = '0s (Cooling Complete)';
      if (proceedBtn) {
        proceedBtn.disabled = false;
        proceedBtn.style.opacity = '1';
        proceedBtn.style.cursor = 'pointer';
        proceedBtn.innerText = 'I Understand, Proceed with Caution';
      }
    }
  }, 1000);

  modal.classList.add('open');
}

function cancelShieldTransfer() {
  if (shieldCountdownInterval) clearInterval(shieldCountdownInterval);
  const modal = document.getElementById('shield-modal');
  if (modal) modal.classList.remove('open');
  alert('Transfer Cancelled: Your funds remain completely safe in your account.');
}

function confirmShieldProceed() {
  if (shieldCountdownInterval) clearInterval(shieldCountdownInterval);
  const modal = document.getElementById('shield-modal');
  if (modal) modal.classList.remove('open');
  openOtpModal();
}

/* --------------------------------------------------------------------------
   2. SyndicateRadar & Mule Network Graph Visualization
   -------------------------------------------------------------------------- */
let graphDecloaked = false;
let graphAnimationReq = null;
let cachedGraphNodes = [];
let cachedGraphLinks = [];
let simNodesCache = [];

async function loadGraphIntelligence() {
  const nodesPill = document.getElementById('graph-stat-nodes');
  const linksPill = document.getElementById('graph-stat-links');
  const clustersPill = document.getElementById('graph-stat-clusters');
  const clustersList = document.getElementById('syndicate-clusters-list');
  const pagerankTbody = document.getElementById('pagerank-tbody');

  try {
    const headers = graphDecloaked ? { 'X-API-Key': 'upay-risk-secret' } : {};
    const res = await fetch(`${API_BASE}/api/v1/graph/network?decloak=${graphDecloaked}&limit=60`, { headers });
    if (!res.ok) throw new Error('Graph fetch failed');
    const data = await res.json();

    cachedGraphNodes = data.nodes || [];
    cachedGraphLinks = data.links || [];

    if (nodesPill) nodesPill.innerText = `Nodes: ${data.total_nodes}`;
    if (linksPill) linksPill.innerText = `Edges: ${data.total_links}`;
    if (clustersPill) clustersPill.innerText = `Syndicates: ${data.syndicates_detected}`;

    // Render Canvas Force Graph
    renderGraphCanvas(cachedGraphNodes, cachedGraphLinks);

    // Render Clusters
    if (clustersList) {
      if (!data.clusters || data.clusters.length === 0) {
        clustersList.innerHTML = '<div style="color:var(--text-muted); font-size:0.82rem; padding:16px 0;">No active clusters.</div>';
      } else {
        clustersList.innerHTML = data.clusters.map(c => `
          <div class="cluster-card" style="border-left: 4px solid ${c.is_syndicate ? '#ef4444' : '#10b981'};">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
              <div>
                <strong style="color:var(--text-primary); font-size:0.88rem;">Cluster #${c.cluster_id}</strong>
                <span style="font-size:0.72rem; color:var(--text-muted); margin-left:6px;">(${c.member_count} accounts)</span>
              </div>
              <span class="ticker-badge" style="background:${c.is_syndicate ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)'}; color:${c.is_syndicate ? '#f87171' : '#34d399'}; font-size:0.7rem;">
                ${c.threat_level.toUpperCase()}
              </span>
            </div>
            <div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom:8px;">
              Mules: <strong>${c.mules_detected}</strong> &bull; Volume: <strong>BDT ${Number(c.total_volume_bdt).toLocaleString()}</strong>
            </div>
            <button class="btn btn-secondary btn-sm" style="width:100%; border-color:rgba(239,68,68,0.4); color:#f87171; font-size:0.75rem; padding:4px 8px;" onclick="quarantineCluster(${c.cluster_id})">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:-1px; margin-right:4px;"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
              <span>Quarantine Cluster</span>
            </button>
          </div>
        `).join('');
      }
    }

    // Render Centrality (PageRank) Table
    if (pagerankTbody) {
      const topNodes = (data.nodes || []).slice(0, 12);
      pagerankTbody.innerHTML = topNodes.map(n => `
        <tr>
          <td><strong style="font-family:var(--font-mono); color:var(--ai-cyan);">${n.display_id || n.id}</strong></td>
          <td><span class="ticker-badge" style="background:rgba(255,255,255,0.06); font-size:0.72rem;">${n.role}</span></td>
          <td>#${n.cluster_id}</td>
          <td><strong style="font-family:var(--font-mono);">${n.pagerank}</strong></td>
          <td>${n.in_degree} &darr; / ${n.out_degree} &uarr;</td>
          <td>BDT ${Number(n.total_sent + n.total_received).toLocaleString()}</td>
          <td>${n.is_quarantined ? '<span style="color:#f87171; font-weight:700;">QUARANTINED</span>' : '<span style="color:#34d399;">Active</span>'}</td>
          <td>
            <button class="btn btn-secondary btn-sm" style="font-size:0.72rem; padding:3px 8px;" onclick="quarantineSingleNode('${n.real_id || n.id}')">Freeze</button>
          </td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error('Failed to load graph intelligence:', err);
  }
}

function renderGraphCanvas(nodes, links) {
  const canvas = document.getElementById('syndicate-graph-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  if (rect.width === 0) return;
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;

  const simNodes = nodes.map((n, i) => {
    const angle = (i / Math.max(1, nodes.length)) * Math.PI * 2;
    const radius = 90 + (n.cluster_id % 4) * 45 + Math.random() * 30;
    return {
      ...n,
      x: width / 2 + Math.cos(angle) * radius + (Math.random() - 0.5) * 15,
      y: height / 2 + Math.sin(angle) * radius + (Math.random() - 0.5) * 15,
      radius: Math.max(5, Math.min(16, 5 + (n.pagerank || 0) * 110))
    };
  });

  simNodesCache = simNodes;

  const nodeMap = {};
  simNodes.forEach(sn => { nodeMap[sn.display_id || sn.id] = sn; });

  const simLinks = links.map(l => ({
    source: nodeMap[l.source],
    target: nodeMap[l.target],
    amount: l.amount_bdt
  })).filter(l => l.source && l.target);

  // Attach interactive node inspector click handler and resize handler once
  if (!canvas.dataset.hasListener) {
    canvas.dataset.hasListener = 'true';
    canvas.addEventListener('click', (e) => {
      const crect = canvas.getBoundingClientRect();
      const clickX = e.clientX - crect.left;
      const clickY = e.clientY - crect.top;

      let closest = null;
      let minDist = 22;
      simNodesCache.forEach(n => {
        const dx = n.x - clickX;
        const dy = n.y - clickY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < minDist) {
          minDist = dist;
          closest = n;
        }
      });

      const inspector = document.getElementById('graph-node-inspector');
      if (closest && inspector) {
        document.getElementById('insp-node-id').innerText = closest.display_id || closest.id;
        document.getElementById('insp-node-role').innerText = closest.role.toUpperCase();
        document.getElementById('insp-node-cluster').innerText = `#${closest.cluster_id}`;
        document.getElementById('insp-node-volume').innerText = `BDT ${Number(closest.total_sent + closest.total_received).toLocaleString()}`;
        inspector.style.display = 'block';
      } else if (inspector) {
        inspector.style.display = 'none';
      }
    });

    window.addEventListener('resize', () => {
      const view = document.getElementById('view-syndicate');
      if (view && view.classList.contains('active') && cachedGraphNodes.length > 0) {
        renderGraphCanvas(cachedGraphNodes, cachedGraphLinks);
      }
    });
  }

  let frameCount = 0;
  if (graphAnimationReq) cancelAnimationFrame(graphAnimationReq);

  function step() {
    ctx.clearRect(0, 0, width, height);

    // Draw Edges
    ctx.lineWidth = 1;
    simLinks.forEach(l => {
      ctx.beginPath();
      ctx.moveTo(l.source.x, l.source.y);
      ctx.lineTo(l.target.x, l.target.y);
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.22)';
      ctx.stroke();
    });

    // Draw Nodes
    simNodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);

      let color = '#10b981';
      if (n.role === 'mule_cashout') color = '#ef4444';
      else if (n.role === 'layering') color = '#f59e0b';
      else if (n.role === 'mastermind' || n.role === 'syndicate_hub') color = '#8b5cf6';

      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // Label
      ctx.fillStyle = '#94a3b8';
      ctx.font = '9px monospace';
      ctx.fillText((n.display_id || n.id).substring(0, 11), n.x + n.radius + 3, n.y + 3);
    });

    frameCount++;
    if (frameCount < 60) {
      simLinks.forEach(l => {
        const dx = l.target.x - l.source.x;
        const dy = l.target.y - l.source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 80) * 0.005;
        l.source.x += (dx / dist) * force;
        l.source.y += (dy / dist) * force;
        l.target.x -= (dx / dist) * force;
        l.target.y -= (dy / dist) * force;
      });
      graphAnimationReq = requestAnimationFrame(step);
    }
  }

  step();
}

async function quarantineCluster(clusterId) {
  if (!confirm(`Are you sure you want to quarantine all accounts in Cluster #${clusterId}? This will freeze all funds and outgoing transfers.`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/graph/quarantine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cluster_id: clusterId, reason: 'Mule syndicate detected via Louvain graph analysis' })
    });
    if (res.ok) {
      const data = await res.json();
      alert(`Cluster #${clusterId} Quarantined: ${data.frozen_users_count} users frozen, ${data.frozen_transfers_count} transfers held.`);
      loadGraphIntelligence();
    }
  } catch (err) {
    alert('Quarantine failed: ' + err.message);
  }
}

async function quarantineSingleNode(nodeId) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/graph/quarantine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: nodeId, reason: 'High-centrality hub frozen by risk analyst' })
    });
    if (res.ok) {
      alert(`Node ${nodeId} frozen.`);
      loadGraphIntelligence();
    }
  } catch (err) {
    alert('Failed: ' + err.message);
  }
}

function toggleGraphDecloak() {
  graphDecloaked = !graphDecloaked;
  const label = document.getElementById('decloak-btn-label');
  if (label) label.innerText = graphDecloaked ? 'Cloak PII (Anonymized)' : 'Decloak PII (Analyst)';
  loadGraphIntelligence();
}

/* --------------------------------------------------------------------------
   3. DivisionalStressRadar & Macro Resilience
   -------------------------------------------------------------------------- */
async function loadResilienceDivisions() {
  const container = document.getElementById('divisions-cards-grid');
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/resilience/divisions`);
    if (!res.ok) throw new Error('Failed to load divisions');
    const data = await res.json();

    container.innerHTML = data.divisions.map(d => `
      <div class="division-card">
        <div class="division-header">
          <div>
            <div class="division-name-en">${d.name}</div>
            <div class="division-name-bn">${d.bengali_name}</div>
          </div>
          <span class="ticker-badge" style="background:${d.stress_grade === 'A' ? 'rgba(16,185,129,0.2)' : (d.stress_grade === 'B' ? 'rgba(245,158,11,0.2)' : 'rgba(239,68,68,0.2)')}; color:${d.stress_grade === 'A' ? '#34d399' : (d.stress_grade === 'B' ? '#fbbf24' : '#f87171')};">
            Grade ${d.stress_grade}
          </span>
        </div>
        <div style="font-size:0.8rem; color:var(--text-secondary);">
          <div>Reserves: <strong style="color:var(--text-primary); font-family:var(--font-mono);">BDT ${(d.total_division_cash_bdt / 1000000).toFixed(1)}M</strong></div>
          <div>Agents: <strong>${d.agent_count}</strong> &bull; 7d Alerts: <strong style="color:${d.fraud_frequency_7d > 10 ? '#f87171' : 'inherit'};">${d.fraud_frequency_7d}</strong></div>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted); display:flex; gap:4px; flex-wrap:wrap;">
          ${(d.vulnerability_factors || []).map(v => `<span style="background:rgba(255,255,255,0.05); padding:2px 6px; border-radius:4px;">${v.replace(/_/g, ' ')}</span>`).join('')}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load resilience divisions:', err);
  }
}

async function executeStressSimulation() {
  const scenario = document.getElementById('stress-scenario-select')?.value || 'flash_flood';
  const severity = parseFloat(document.getElementById('stress-severity-slider')?.value || 0.8);
  const duration = parseInt(document.getElementById('stress-duration-select')?.value || 48);

  const payload = {
    scenario: scenario,
    severity: severity,
    affected_divisions: ['Sylhet', 'Chittagong'],
    duration_hours: duration
  };

  try {
    const res = await fetch(`${API_BASE}/api/v1/resilience/stress-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      const resultsBox = document.getElementById('stress-results-box');
      if (resultsBox) resultsBox.style.display = 'block';

      document.getElementById('stress-resilience-index').innerText = `${data.resilience_index} / 100`;
      document.getElementById('stress-total-shortfall').innerText = `BDT ${Number(data.total_network_shortfall_bdt).toLocaleString()}`;
      document.getElementById('stress-affected-count').innerText = `${data.affected_divisions_count} / 8`;

      const tbody = document.getElementById('stress-injection-tbody');
      if (tbody) {
        tbody.innerHTML = data.emergency_injection_schedule.map(inj => `
          <tr>
            <td>${inj.from_source}</td>
            <td><strong style="color:var(--text-primary);">${inj.to_division}</strong></td>
            <td><strong style="color:var(--upay-emerald-light); font-family:var(--font-mono);">BDT ${Number(inj.injection_amount_bdt).toLocaleString()}</strong></td>
            <td><span class="ticker-badge" style="background:${inj.priority === 'immediate' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)'}; color:${inj.priority === 'immediate' ? '#f87171' : '#fbbf24'};">${inj.priority.toUpperCase()}</span></td>
            <td>${inj.transit_hours} Hours</td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    alert('Simulation error: ' + err.message);
  }
}

async function loadRebalanceSchedule() {
  const container = document.getElementById('rebalance-schedule-container');
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/resilience/rebalance`);
    if (res.ok) {
      const data = await res.json();
      container.innerHTML = `
        <div style="margin-bottom:12px; font-size:0.84rem; color:var(--upay-emerald-light); font-weight:700;">
          Network Stability Score: ${data.network_stability_score}% &bull; Total Float Reallocated: BDT ${Number(data.total_rebalanced_bdt).toLocaleString()}
        </div>
        <div class="alerts-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Source Vault</th>
                <th>Destination</th>
                <th>Rebalance Amount</th>
                <th>Mode</th>
                <th>Transit Time</th>
                <th>Rationale</th>
              </tr>
            </thead>
            <tbody>
              ${data.transfers.map(t => `
                <tr>
                  <td><strong>${t.source_division}</strong></td>
                  <td><strong style="color:var(--ai-cyan);">${t.target_division}</strong></td>
                  <td><strong style="color:var(--upay-emerald-light); font-family:var(--font-mono);">BDT ${Number(t.amount_bdt).toLocaleString()}</strong></td>
                  <td>${t.mode.replace(/_/g, ' ')}</td>
                  <td>${t.estimated_transit_hours}h</td>
                  <td style="font-size:0.78rem; color:var(--text-secondary);">${t.rationale}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }
  } catch (err) {
    container.innerHTML = '<div style="color:var(--accent-rose); font-size:0.84rem;">Failed to load rebalance schedule.</div>';
  }
}

/* --------------------------------------------------------------------------
   4. AegisLab Gamified Threat Simulator
   -------------------------------------------------------------------------- */
const SIMULATOR_STATE = {
  score: 15,
  answers: {}
};

function handleSimulatorChoice(scenarioNum, choice) {
  SIMULATOR_STATE.answers[scenarioNum] = choice;
  const feedbackBox = document.getElementById(`sim${scenarioNum}-feedback`);
  if (!feedbackBox) return;

  if (scenarioNum === 1) {
    if (choice === 'A') {
      SIMULATOR_STATE.score = Math.min(95, SIMULATOR_STATE.score + 50);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(239,68,68,0.15)';
      feedbackBox.style.color = '#f87171';
      feedbackBox.innerHTML = '<span class="status-chip chip-trapped">TRAPPED</span> You sent 2,500 AED! In reality, there is no prize. Fraudsters vanish with your cash. Legitimate rewards never ask for fees.';
    } else if (choice === 'B') {
      SIMULATOR_STATE.score = Math.min(85, SIMULATOR_STATE.score + 25);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(245,158,11,0.15)';
      feedbackBox.style.color = '#fbbf24';
      feedbackBox.innerHTML = '<span class="status-chip chip-risky">RISKY</span> Engaging confirms your number is active. They will invent new excuses why the fee must be paid first.';
    } else {
      SIMULATOR_STATE.score = Math.max(5, SIMULATOR_STATE.score - 10);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(16,185,129,0.15)';
      feedbackBox.style.color = '#34d399';
      feedbackBox.innerHTML = '<span class="status-chip chip-safe">SAFE</span> Correct! You recognized the advance-fee scam signature and protected your hard-earned money.';
    }
  } else if (scenarioNum === 2) {
    if (choice === 'A') {
      SIMULATOR_STATE.score = Math.min(95, SIMULATOR_STATE.score + 55);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(239,68,68,0.15)';
      feedbackBox.style.color = '#f87171';
      feedbackBox.innerHTML = '<span class="status-chip chip-trapped">TRAPPED</span> Panic-induced transfer! Hospital impersonators exploit fear of family tragedy. Always verify with your family directly.';
    } else if (choice === 'B') {
      SIMULATOR_STATE.score = Math.min(85, SIMULATOR_STATE.score + 20);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(245,158,11,0.15)';
      feedbackBox.style.color = '#fbbf24';
      feedbackBox.innerHTML = '<span class="status-chip chip-risky">RISKY</span> Fraudsters often possess stolen photos of accident scenes from social media to trick victims.';
    } else {
      SIMULATOR_STATE.score = Math.max(5, SIMULATOR_STATE.score - 10);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(16,185,129,0.15)';
      feedbackBox.style.color = '#34d399';
      feedbackBox.innerHTML = '<span class="status-chip chip-safe">SAFE</span> Excellent! Calling your brother reveals he is safely having tea at home and his name was falsely used.';
    }
  } else if (scenarioNum === 3) {
    if (choice === 'A') {
      SIMULATOR_STATE.score = Math.min(95, SIMULATOR_STATE.score + 45);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(239,68,68,0.15)';
      feedbackBox.style.color = '#f87171';
      feedbackBox.innerHTML = '<span class="status-chip chip-trapped">TRAPPED</span> Overpayment trap! The original SMS was fake or funded with a stolen credit card that gets charged back, leaving you out 20,000 BDT.';
    } else if (choice === 'B') {
      SIMULATOR_STATE.score = Math.min(85, SIMULATOR_STATE.score + 15);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(245,158,11,0.15)';
      feedbackBox.style.color = '#fbbf24';
      feedbackBox.innerHTML = '<span class="status-chip chip-risky">UNRESOLVED</span> Delaying without verification still leaves you exposed.';
    } else {
      SIMULATOR_STATE.score = Math.max(5, SIMULATOR_STATE.score - 10);
      feedbackBox.style.display = 'block';
      feedbackBox.style.background = 'rgba(16,185,129,0.15)';
      feedbackBox.style.color = '#34d399';
      feedbackBox.innerHTML = '<span class="status-chip chip-safe">SAFE</span> Masterful compliance! You checked your official balance and directed genuine errors to bank customer care.';
    }
  }

  updateThreatMeter();
}

function updateThreatMeter() {
  const display = document.getElementById('threat-score-display');
  const fill = document.getElementById('threat-meter-fill');
  const summary = document.getElementById('threat-verdict-summary');

  if (!display || !fill) return;

  const score = SIMULATOR_STATE.score;
  fill.style.width = `${score}%`;

  if (score >= 70) {
    display.innerText = `${score}% (CRITICAL THREAT)`;
    display.style.color = '#f87171';
    fill.style.background = '#ef4444';
    if (summary) summary.innerText = 'High vulnerability detected. Susceptible to emotional urgency and advance-fee social engineering.';
  } else if (score >= 40) {
    display.innerText = `${score}% (ELEVATED RISK)`;
    display.style.color = '#fbbf24';
    fill.style.background = '#f59e0b';
    if (summary) summary.innerText = 'Moderate vulnerability. Remember to verify claims offline before authorizing funds.';
  } else {
    display.innerText = `${score}% (PROTECTED)`;
    display.style.color = '#34d399';
    fill.style.background = '#10b981';
    if (summary) summary.innerText = 'Strong defense instincts. Vigilance successfully prevents fraud loss.';
  }
}

function resetThreatSimulator() {
  SIMULATOR_STATE.score = 15;
  SIMULATOR_STATE.answers = {};
  for (let i = 1; i <= 3; i++) {
    const fb = document.getElementById(`sim${i}-feedback`);
    if (fb) fb.style.display = 'none';
    const inputs = document.querySelectorAll(`input[name="sim${i}"]`);
    inputs.forEach(inp => { inp.checked = false; });
  }
  updateThreatMeter();
}

/* --------------------------------------------------------------------------
   5. BFIU Form 2 STR Regulatory Filing Modal
   -------------------------------------------------------------------------- */
async function openBfiuModal(alertId, transferId, score, amountBDT, reasons) {
  const modal = document.getElementById('bfiu-modal');
  if (!modal) return;

  try {
    const res = await fetch(`${API_BASE}/api/v1/compliance/generate-str`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId, analyst_id: 'u_analyst_01' })
    });

    if (res.ok) {
      const data = await res.json();
      document.getElementById('bfiu-str-ref').innerText = data.str_reference;
      document.getElementById('bfiu-date').innerText = data.filing_date;
      document.getElementById('bfiu-entity').innerText = data.reporting_entity;
      document.getElementById('bfiu-account').innerText = data.subject_account;
      document.getElementById('bfiu-amount').innerText = `BDT ${Number(data.transaction_amount_bdt).toLocaleString()}`;
      document.getElementById('bfiu-alert-id').innerText = alertId;
      document.getElementById('bfiu-risk').innerText = `${data.risk_score} / 100`;
      document.getElementById('bfiu-narrative').innerText = data.narrative;
      document.getElementById('bfiu-sha256').innerText = data.sha256_hash;

      const chipsBox = document.getElementById('bfiu-indicators-chips');
      if (chipsBox) {
        chipsBox.innerHTML = (data.anomaly_indicators || []).map(ind => `
          <span style="background:rgba(239,68,68,0.2); color:#f87171; border:1px solid rgba(239,68,68,0.4); padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:700;">
            ${ind}
          </span>
        `).join('');
      }

      modal.classList.add('open');
    }
  } catch (err) {
    alert('Error generating STR: ' + err.message);
  }
}

window.triggerPreFlightShieldCheck = triggerPreFlightShieldCheck;
window.cancelShieldTransfer = cancelShieldTransfer;
window.confirmShieldProceed = confirmShieldProceed;
window.loadGraphIntelligence = loadGraphIntelligence;
window.quarantineCluster = quarantineCluster;
window.quarantineSingleNode = quarantineSingleNode;
window.toggleGraphDecloak = toggleGraphDecloak;
window.loadResilienceDivisions = loadResilienceDivisions;
window.executeStressSimulation = executeStressSimulation;
window.loadRebalanceSchedule = loadRebalanceSchedule;
window.handleSimulatorChoice = handleSimulatorChoice;
window.resetThreatSimulator = resetThreatSimulator;
window.openBfiuModal = openBfiuModal;


