/**
 * RemitMind - Frontend Interactive Engine
 * Zero emojis - Pure clean typography and vector iconography.
 * Full dual theme support (Light Mode / Dark Mode) with localStorage persistence.
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initCorridorRates();
  initSenderCalculator();
  initRiskRadar();
  initReceiverPortal();
  initAgentForecast();
  initApiTabs();
});

/* ==========================================================================
   1. Theme Management (Light / Dark Mode)
   ========================================================================== */
function initThemeToggle() {
  const themeBtn = document.getElementById('theme-toggle-btn');
  const storedTheme = localStorage.getItem('remitmind_theme') || 'dark';

  document.documentElement.setAttribute('data-theme', storedTheme);
  updateThemeIcon(storedTheme);

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('remitmind_theme', newTheme);
      updateThemeIcon(newTheme);
      showToast(`Switched to ${newTheme === 'dark' ? 'Dark' : 'Light'} Mode`);
    });
  }
}

function updateThemeIcon(theme) {
  const iconContainer = document.getElementById('theme-icon-container');
  if (!iconContainer) return;

  if (theme === 'light') {
    // Show Moon icon to indicate switch to dark
    iconContainer.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    `;
  } else {
    // Show Sun icon to indicate switch to light
    iconContainer.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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
   2. Corridor FX Rates & Trends Data
   ========================================================================== */
const CORRIDOR_DATA = {
  AED_BDT: {
    name: 'UAE Dirham (AED)',
    symbol: 'AED',
    currentRate: 32.85,
    forecast: [
      { day: 'Mon', date: 'Oct 05', rate: 32.85, isBest: false },
      { day: 'Tue', date: 'Oct 06', rate: 33.10, isBest: false },
      { day: 'Wed', date: 'Oct 07', rate: 33.45, isBest: false },
      { day: 'Thu', date: 'Oct 08', rate: 33.85, isBest: true },
      { day: 'Fri', date: 'Oct 09', rate: 33.60, isBest: false }
    ],
    baseFeePct: 0.02,
    bestFeePct: 0.018,
    confidence: '82%',
    aiNote: 'AED/BDT shows steady upward drift over the past 4 days. Peak liquidity window expected on Thursday before weekend settlement.'
  },
  SAR_BDT: {
    name: 'Saudi Riyal (SAR)',
    symbol: 'SAR',
    currentRate: 32.10,
    forecast: [
      { day: 'Mon', date: 'Oct 05', rate: 32.10, isBest: false },
      { day: 'Tue', date: 'Oct 06', rate: 32.30, isBest: false },
      { day: 'Wed', date: 'Oct 07', rate: 32.95, isBest: true },
      { day: 'Thu', date: 'Oct 08', rate: 32.70, isBest: false },
      { day: 'Fri', date: 'Oct 09', rate: 32.50, isBest: false }
    ],
    baseFeePct: 0.022,
    bestFeePct: 0.019,
    confidence: '78%',
    aiNote: 'SAR rates driven by mid-week GCC interbank clearing. Wednesday provides optimal BDT conversion efficiency.'
  },
  MYR_BDT: {
    name: 'Malaysian Ringgit (MYR)',
    symbol: 'MYR',
    currentRate: 27.40,
    forecast: [
      { day: 'Mon', date: 'Oct 05', rate: 27.40, isBest: false },
      { day: 'Tue', date: 'Oct 06', rate: 27.55, isBest: false },
      { day: 'Wed', date: 'Oct 07', rate: 27.80, isBest: false },
      { day: 'Thu', date: 'Oct 08', rate: 28.15, isBest: true },
      { day: 'Fri', date: 'Oct 09', rate: 27.90, isBest: false }
    ],
    baseFeePct: 0.019,
    bestFeePct: 0.016,
    confidence: '85%',
    aiNote: 'High remittance volume window for Malaysia corridor favors Thursday dispatch before bank cutoff.'
  },
  EUR_BDT: {
    name: 'Euro / Italy (EUR)',
    symbol: 'EUR',
    currentRate: 133.50,
    forecast: [
      { day: 'Mon', date: 'Oct 05', rate: 133.50, isBest: false },
      { day: 'Tue', date: 'Oct 06', rate: 134.20, isBest: false },
      { day: 'Wed', date: 'Oct 07', rate: 135.10, isBest: false },
      { day: 'Thu', date: 'Oct 08', rate: 135.80, isBest: false },
      { day: 'Fri', date: 'Oct 09', rate: 136.40, isBest: true }
    ],
    baseFeePct: 0.015,
    bestFeePct: 0.013,
    confidence: '80%',
    aiNote: 'European corridor rates gain momentum heading into Friday settlement. Recommended wait time is 4 days.'
  }
};

let currentCorridorKey = 'AED_BDT';

function initCorridorRates() {
  const corridorSelect = document.getElementById('calc-corridor');
  if (!corridorSelect) return;

  corridorSelect.addEventListener('change', (e) => {
    currentCorridorKey = e.target.value;
    updateSenderCalculations();
  });
}

/* ==========================================================================
   3. Sender Plan Optimizer Calculator
   ========================================================================== */
function initSenderCalculator() {
  const amountInput = document.getElementById('calc-amount');
  const amountSlider = document.getElementById('calc-slider');
  const rentInput = document.getElementById('goal-rent');
  const schoolInput = document.getElementById('goal-school');
  const savingsInput = document.getElementById('goal-savings');

  if (!amountInput || !amountSlider) return;

  amountSlider.addEventListener('input', (e) => {
    amountInput.value = e.target.value;
    updateSenderCalculations();
  });

  amountInput.addEventListener('input', (e) => {
    let val = Math.max(100, Math.min(20000, Number(e.target.value) || 100));
    amountSlider.value = val;
    updateSenderCalculations();
  });

  const goalInputs = [rentInput, schoolInput, savingsInput];
  goalInputs.forEach(input => {
    if (input) {
      input.addEventListener('input', () => {
        balanceGoals(input);
        updateSenderCalculations();
      });
    }
  });

  updateSenderCalculations();
}

function balanceGoals(changedInput) {
  const rent = document.getElementById('goal-rent');
  const school = document.getElementById('goal-school');
  const savings = document.getElementById('goal-savings');
  if (!rent || !school || !savings) return;

  let total = Number(rent.value) + Number(school.value) + Number(savings.value);
  if (total !== 100) {
    let diff = 100 - total;
    if (changedInput !== savings) {
      let currentSav = Number(savings.value);
      savings.value = Math.max(0, Math.min(100, currentSav + diff));
    } else {
      let currentRent = Number(rent.value);
      rent.value = Math.max(0, Math.min(100, currentRent + diff));
    }
  }

  document.getElementById('val-rent').innerText = rent.value + '%';
  document.getElementById('val-school').innerText = school.value + '%';
  document.getElementById('val-savings').innerText = savings.value + '%';
}

function updateSenderCalculations() {
  const corridor = CORRIDOR_DATA[currentCorridorKey];
  const amountInput = document.getElementById('calc-amount');
  if (!corridor || !amountInput) return;

  const amountSrc = parseFloat(amountInput.value) || 2000;

  const nowRate = corridor.currentRate;
  const bestDayObj = corridor.forecast.find(f => f.isBest) || corridor.forecast[3];
  const bestRate = bestDayObj.rate;

  const sendNowGross = amountSrc * nowRate;
  const sendNowFee = sendNowGross * corridor.baseFeePct;
  const sendNowNet = Math.round(sendNowGross - sendNowFee);

  const sendBestGross = amountSrc * bestRate;
  const sendBestFee = sendBestGross * corridor.bestFeePct;
  const sendBestNet = Math.round(sendBestGross - sendBestFee);

  const netSavings = Math.max(0, sendBestNet - sendNowNet);

  document.getElementById('disp-send-now').innerText = `BDT ${sendNowNet.toLocaleString()}`;
  document.getElementById('disp-send-best').innerText = `BDT ${sendBestNet.toLocaleString()}`;
  document.getElementById('disp-best-day-name').innerText = `Send on ${bestDayObj.day} (${bestDayObj.date})`;
  document.getElementById('disp-net-savings').innerText = `+ BDT ${netSavings.toLocaleString()} Saved`;
  document.getElementById('disp-confidence-score').innerText = corridor.confidence;
  document.getElementById('disp-ai-note').innerText = corridor.aiNote;

  renderForecastCells(corridor.forecast);

  const rentPct = Number(document.getElementById('goal-rent')?.value || 50) / 100;
  const schoolPct = Number(document.getElementById('goal-school')?.value || 30) / 100;
  const savingsPct = Number(document.getElementById('goal-savings')?.value || 20) / 100;

  const rentBDT = Math.round(sendBestNet * rentPct);
  const schoolBDT = Math.round(sendBestNet * schoolPct);
  const savingsBDT = Math.round(sendBestNet * savingsPct);

  const segRent = document.getElementById('seg-rent');
  const segSchool = document.getElementById('seg-school');
  const segSavings = document.getElementById('seg-savings');
  if (segRent) segRent.style.width = (rentPct * 100) + '%';
  if (segSchool) segSchool.style.width = (schoolPct * 100) + '%';
  if (segSavings) segSavings.style.width = (savingsPct * 100) + '%';

  if (document.getElementById('disp-bdt-rent')) document.getElementById('disp-bdt-rent').innerText = `BDT ${rentBDT.toLocaleString()}`;
  if (document.getElementById('disp-bdt-school')) document.getElementById('disp-bdt-school').innerText = `BDT ${schoolBDT.toLocaleString()}`;
  if (document.getElementById('disp-bdt-savings')) document.getElementById('disp-bdt-savings').innerText = `BDT ${savingsBDT.toLocaleString()}`;
}

function renderForecastCells(forecastList) {
  const container = document.getElementById('forecast-cells-container');
  if (!container) return;

  container.innerHTML = '';
  forecastList.forEach(item => {
    const cell = document.createElement('div');
    cell.className = `forecast-day-cell ${item.isBest ? 'best-day' : ''}`;
    cell.innerHTML = `
      ${item.isBest ? '<div class="best-badge-mini">Peak Rate</div>' : ''}
      <span class="day-label">${item.day}</span>
      <div class="day-rate">${item.rate.toFixed(2)}</div>
      <span style="font-size:0.68rem; color:${item.isBest ? 'var(--upay-emerald)' : 'var(--text-muted)'};">${item.date}</span>
    `;
    container.appendChild(cell);
  });
}

/* ==========================================================================
   4. Analyst Risk Radar Simulator (Zero Emoji)
   ========================================================================== */
const RISK_SCENARIOS = {
  normal: {
    title: 'Standard Monthly Family Remittance',
    score: 14,
    status: 'completed',
    level: 'Low Risk',
    sender: 'Rahim Sheikh (Dubai)',
    receiver: 'Amina Begum (Sylhet)',
    amount: 'AED 1,500 (BDT 49,275)',
    reasons: ['RECURRING_CORRIDOR_MATCH', 'VERIFIED_DEVICE', 'NORMAL_VELOCITY'],
    explanation: 'Transfer aligns with Rahim\'s 18-month historical pattern to his verified spouse in Sylhet. Normal banking hours, trusted device biometric handshake intact.',
    suggestedAction: 'approve'
  },
  mule_ring: {
    title: 'Mule Ring Structuring Pattern (Flagged)',
    score: 78,
    status: 'in_review',
    level: 'High Risk',
    sender: 'New Expat Account #8812',
    receiver: 'First-Time Receiver #904',
    amount: 'AED 2,800 (BDT 92,400)',
    reasons: ['NEW_RECEIVER', 'VELOCITY_3X', 'NEW_DEVICE', 'BURST_PATTERN'],
    explanation: '3 separate transfers totaling BDT 2.7 Lakh in 45 minutes to a recipient registered today. Correlates with synthetic syndicate ring cluster #14.',
    suggestedAction: 'hold'
  },
  account_takeover: {
    title: 'Account Takeover Attempt (Flagged)',
    score: 89,
    status: 'in_review',
    level: 'Critical Risk',
    sender: 'Rahim Sheikh (Dubai)',
    receiver: 'Unknown Wallet #554',
    amount: 'AED 8,500 (BDT 279,225)',
    reasons: ['NEW_DEVICE', 'ODD_HOURS_03AM', 'AMOUNT_4.2X_DEVIATION', 'GEO_ANOMALY'],
    explanation: 'Attempted dispatch at 03:15 AM UAE time from an unverified Android emulator with 4.2x sender standard deviation. No prior link to recipient.',
    suggestedAction: 'escalate'
  }
};

function initRiskRadar() {
  const scenarioBtns = document.querySelectorAll('.scenario-picker-btn');
  scenarioBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      scenarioBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadRiskScenario(btn.dataset.scenario);
    });
  });

  const btnApprove = document.getElementById('btn-analyst-approve');
  const btnHold = document.getElementById('btn-analyst-hold');
  const btnEscalate = document.getElementById('btn-analyst-escalate');

  if (btnApprove) btnApprove.addEventListener('click', () => handleAnalystDecision('Approved', 'Transfer released to payout queue. Decision saved to review_actions table with is_fraud_label=0.'));
  if (btnHold) btnHold.addEventListener('click', () => handleAnalystDecision('Placed on Hold', 'Transfer temporarily held for 24h SMS and agent verification.'));
  if (btnEscalate) btnEscalate.addEventListener('click', () => handleAnalystDecision('Escalated', 'Alert escalated to upay Anti-Financial Crimes Unit (AFCU).'));

  loadRiskScenario('mule_ring');
}

function loadRiskScenario(key) {
  const scenario = RISK_SCENARIOS[key] || RISK_SCENARIOS.normal;

  const dial = document.getElementById('risk-dial-indicator');
  const scoreNum = document.getElementById('risk-score-display');
  const statusBadge = document.getElementById('risk-status-badge');
  const levelText = document.getElementById('risk-level-display');
  const reasonsContainer = document.getElementById('risk-reasons-container');
  const explanationText = document.getElementById('risk-explanation-text');
  const suggestedActionBadge = document.getElementById('risk-suggested-action');
  const txInfo = document.getElementById('risk-tx-info');

  if (!dial || !scoreNum) return;

  scoreNum.innerText = scenario.score;
  levelText.innerText = scenario.level;
  explanationText.innerText = scenario.explanation;
  if (suggestedActionBadge) suggestedActionBadge.innerText = `Suggested: ${scenario.suggestedAction.toUpperCase()}`;

  if (txInfo) {
    txInfo.innerHTML = `<strong>${scenario.sender}</strong> &rarr; <strong>${scenario.receiver}</strong> (${scenario.amount})`;
  }

  dial.className = 'risk-dial';
  statusBadge.className = 'risk-status-badge';

  if (scenario.score < 40) {
    dial.classList.add('low');
    statusBadge.classList.add('risk-badge-low');
    statusBadge.innerText = 'Status: Completed (Instant)';
  } else if (scenario.score < 70) {
    dial.classList.add('medium');
    statusBadge.classList.add('risk-badge-medium');
    statusBadge.innerText = 'Status: In Review';
  } else {
    dial.classList.add('high');
    statusBadge.classList.add('risk-badge-high');
    statusBadge.innerText = 'Status: Flagged for Review';
  }

  if (reasonsContainer) {
    reasonsContainer.innerHTML = '';
    scenario.reasons.forEach(r => {
      const span = document.createElement('span');
      span.className = 'reason-tag';
      span.innerText = r;
      reasonsContainer.appendChild(span);
    });
  }
}

function handleAnalystDecision(decisionName, detailMsg) {
  showToast(`Analyst Decision: ${decisionName}. ${detailMsg}`);
}

/* ==========================================================================
   5. Village Receiver Portal (Zero Emoji)
   ========================================================================== */
function initReceiverPortal() {
  const langToggle = document.getElementById('receiver-lang-toggle');
  const audioBtn = document.getElementById('btn-play-voice-summary');

  if (langToggle) {
    langToggle.addEventListener('change', (e) => {
      toggleReceiverLanguage(e.target.checked);
    });
  }

  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      playAudioSimulation();
    });
  }
}

function toggleReceiverLanguage(isEnglish) {
  const title = document.getElementById('rcv-title');
  const summary = document.getElementById('rcv-summary-text');
  const feeInfo = document.getElementById('rcv-fee-info');
  const agentTip = document.getElementById('rcv-agent-tip');

  if (isEnglish) {
    if (title) title.innerText = 'Remittance Received Notification';
    if (summary) summary.innerText = 'A total of BDT 67,780 has safely arrived from Rahim in Dubai. No hidden deductions were made.';
    if (feeInfo) feeInfo.innerText = 'Transfer Fee: BDT 0 (Prepaid by sender) | Network: upay Bangladesh';
    if (agentTip) agentTip.innerText = 'Nearest cash-out point: Karim Store (Sylhet Bazar) has sufficient verified liquidity.';
  } else {
    if (title) title.innerText = 'টাকা আসার সহজ বিবরণ (upay রেমিট্যান্স)';
    if (summary) summary.innerText = 'আপনার কাছে দুবাই থেকে রহিম ভাইয়ের পাঠানো মোট ৬৭,৭৮০ টাকা নিরাপদে পৌঁছেছে।';
    if (feeInfo) feeInfo.innerText = 'কোনো গোপন বা বাড়তি চার্জ কাটা হয়নি | নেটওয়ার্ক: উপায় বাংলাদেশ';
    if (agentTip) agentTip.innerText = 'কাছের উপায় এজেন্ট করিম চাচার দোকানে পর্যাপ্ত ক্যাশ টাকা প্রস্তুত আছে।';
  }
}

function playAudioSimulation() {
  const audioBtn = document.getElementById('btn-play-voice-summary');
  const originalText = audioBtn.innerHTML;
  audioBtn.innerHTML = `<span>Audio Playback Active...</span>`;

  if ('speechSynthesis' in window) {
    const textToSpeak = 'আপনার কাছে দুবাই থেকে রহিম ভাইয়ের পাঠানো মোট ৬৭,৭৮০ টাকা নিরাপদে পৌঁছেছে।';
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = 'bn-BD';
    utterance.rate = 0.95;
    utterance.onend = () => { audioBtn.innerHTML = originalText; };
    utterance.onerror = () => { audioBtn.innerHTML = originalText; };
    window.speechSynthesis.speak(utterance);
  } else {
    setTimeout(() => {
      audioBtn.innerHTML = originalText;
      showToast('Audio narration completed.');
    }, 2000);
  }
}

/* ==========================================================================
   6. Agent Liquidity Forecaster
   ========================================================================== */
function initAgentForecast() {
  const cashSlider = document.getElementById('agent-cash-slider');
  const cashInput = document.getElementById('agent-cash-val');

  if (!cashSlider || !cashInput) return;

  cashSlider.addEventListener('input', (e) => {
    cashInput.innerText = `BDT ${Number(e.target.value).toLocaleString()}`;
    recomputeAgentLiquidity(Number(e.target.value));
  });

  recomputeAgentLiquidity(300000);
}

function recomputeAgentLiquidity(cashOnHand) {
  const peakDemand = 420000;
  const shortfall = Math.max(0, peakDemand - cashOnHand);

  const topupBadge = document.getElementById('agent-topup-status');
  const topupText = document.getElementById('agent-topup-needed');

  if (topupBadge && topupText) {
    if (shortfall > 0) {
      topupBadge.className = 'floating-pill';
      topupBadge.style.borderColor = 'rgba(244, 63, 94, 0.4)';
      topupBadge.style.color = 'var(--accent-rose)';
      topupBadge.innerHTML = `<span class="pulse-dot" style="background:var(--accent-rose); box-shadow:0 0 10px var(--accent-rose);"></span> Top-up Alert: Shortfall of BDT ${shortfall.toLocaleString()} by Eid Eve`;
      topupText.innerText = `BDT ${shortfall.toLocaleString()}`;
    } else {
      topupBadge.className = 'floating-pill';
      topupBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      topupBadge.style.color = 'var(--upay-emerald-light)';
      topupBadge.innerHTML = `<span class="pulse-dot"></span> Liquidity Safe: Adequate cash for peak Eid rush`;
      topupText.innerText = 'BDT 0 (Surplus Available)';
    }
  }
}

/* ==========================================================================
   7. API Playground & Sandbox Navigation Tabs
   ========================================================================== */
function initApiTabs() {
  const apiBtns = document.querySelectorAll('.api-tab-btn');
  const codeDisplay = document.getElementById('api-code-snippet');

  const API_SNIPPETS = {
    plan: `// POST /api/v1/plans/recommend
{
  "sender_id": "u_101",
  "receiver_id": "u_202",
  "corridor": "AED_BDT",
  "amount_src": 2000,
  "goals": [
    { "name": "rent", "share_pct": 50 },
    { "name": "school", "share_pct": 30 },
    { "name": "savings", "share_pct": 20 }
  ]
}

// Response 200 OK
{
  "best_day": "2026-10-08",
  "send_now": { "amount_bdt": 66400, "fee_bdt": 1328 },
  "send_best": { "amount_bdt": 67780, "fee_bdt": 1220 },
  "expected_saving_bdt": 1380,
  "confidence": 0.82,
  "split": [
    { "name": "rent", "bdt": 33890 },
    { "name": "school", "bdt": 20334 },
    { "name": "savings", "bdt": 13556 }
  ],
  "explanation": "AED/BDT has gained momentum for 4 consecutive days. Sending Thursday saves BDT 1,380."
}`,

    transfer: `// POST /api/v1/transfers
{
  "sender_id": "u_101",
  "receiver_id": "u_202",
  "corridor": "AED_BDT",
  "amount_src": 2000,
  "device_id": "dev_dubai_77",
  "channel": "app"
}

// Response 201 Created (Flagged for Review)
{
  "transfer_id": "t_9001",
  "status": "in_review",
  "risk_score": 78,
  "reason_codes": ["NEW_RECEIVER", "VELOCITY_3X", "NEW_DEVICE"],
  "message": "Transaction routed to human risk analyst queue for safety verification."
}`,

    alert: `// GET /api/v1/analyst/alerts/a_55
// Headers: { "X-API-Key": "upay-risk-secret" }

// Response 200 OK
{
  "alert_id": "a_55",
  "transfer_id": "t_9001",
  "score": 78,
  "reason_codes": ["NEW_RECEIVER", "VELOCITY_3X", "NEW_DEVICE"],
  "what_happened": "3 transfers in 40 minutes to a receiver first seen today.",
  "why_risky": "Matches structuring pattern seen in synthetic mule rings.",
  "suggested_action": "hold",
  "model_version": "risk-v1.0"
}`
  };

  apiBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      apiBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const snippetKey = btn.dataset.endpoint;
      if (codeDisplay && API_SNIPPETS[snippetKey]) {
        codeDisplay.innerText = API_SNIPPETS[snippetKey];
      }
    });
  });
}

window.switchSandboxTab = function(tabId) {
  const tabs = document.querySelectorAll('.sandbox-tab-btn');
  const panels = document.querySelectorAll('.sandbox-panel');

  tabs.forEach(t => {
    if (t.dataset.tab === tabId) {
      t.classList.add('active');
    } else {
      t.classList.remove('active');
    }
  });

  panels.forEach(p => {
    if (p.id === `panel-${tabId}`) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });
};

function showToast(msg) {
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
