/**
 * CreditCardForm Engine (inspired by rahil1202/credit-card-form from 21st.dev)
 * Features:
 * - 3D Card flip with perspective on CVV focus/blur
 * - 16-slot animated rolling digit mechanism
 * - Dynamic gliding highlight border box (#highlight) tracking active field
 * - Live Card Number formatting (#### #### #### ####) & middle masking
 * - Cardholder uppercase synchronization
 * - Expiration Month & Year dropdown generation and live preview
 * - Field validity checks and seamless payment submission
 */

document.addEventListener('DOMContentLoaded', () => {
  initCreditCardForm();
});

function clampDigits(val, maxLen) {
  return (val || '').replace(/\D/g, '').slice(0, maxLen);
}

function formatCardNumber(val) {
  const digits = clampDigits(val, 16);
  const parts = [];
  for (let i = 0; i < digits.length; i += 4) {
    parts.push(digits.slice(i, i + 4));
  }
  return parts.join(' ');
}

function initCreditCardForm() {
  const cardEl = document.getElementById('creditCard');
  if (!cardEl) return;

  const highlightEl = document.getElementById('highlight');
  const numberInput = document.getElementById('card-number');
  const holderInput = document.getElementById('card-holder');
  const monthSelect = document.getElementById('expiration_month');
  const yearSelect = document.getElementById('expiration_year');
  const cvvInput = document.getElementById('card-cvv');
  const numberSlotsContainer = document.getElementById('card_number_slots');
  const holderDisplay = document.getElementById('card_holder_display');
  const monthDisplay = document.getElementById('card_expires_month_display');
  const yearDisplay = document.getElementById('card_expires_year_display');
  const cvvDisplay = document.getElementById('card_cvv_display');
  const numErrorMsg = document.getElementById('card-number-error');

  // Populate expiration year options if empty
  if (yearSelect && yearSelect.options.length <= 1) {
    const currentYear = new Date().getFullYear();
    for (let i = 0; i < 10; i++) {
      const yr = String(currentYear + i);
      const opt = document.createElement('option');
      opt.value = yr;
      opt.textContent = yr;
      yearSelect.appendChild(opt);
    }
  }

  // Set default state
  let cardNumber = clampDigits(numberInput ? numberInput.value : '4242881299014242', 16);
  let cardHolder = (holderInput ? holderInput.value : 'RAHIM SHEIKH').toUpperCase();
  let expMonth = monthSelect ? monthSelect.value || '10' : '10';
  let expYear = yearSelect ? yearSelect.value || '2028' : '2028';
  let cardCVV = clampDigits(cvvInput ? cvvInput.value : '789', 4);
  let maskMiddle = true;

  // Render Initial 16 slots with rolling digits
  function renderCardNumberSlots() {
    if (!numberSlotsContainer) return;
    numberSlotsContainer.innerHTML = '';

    for (let i = 0; i < 16; i++) {
      const slot = document.createElement('span');
      slot.className = 'slot';

      const digit = document.createElement('span');
      digit.className = 'digit';

      const isFiled = i < cardNumber.length;
      if (isFiled) {
        digit.classList.add('filed');
      }

      let char = '#';
      if (isFiled) {
        if (maskMiddle && i >= 4 && i <= 11) {
          char = '*';
        } else {
          char = cardNumber[i];
        }
      }

      digit.innerHTML = `
        <span class="row placeholder">#</span>
        <span class="row value">${char}</span>
      `;

      slot.appendChild(digit);
      numberSlotsContainer.appendChild(slot);
    }
  }

  // Update Highlight Box position & class
  function setHighlight(focusTarget) {
    if (!highlightEl) return;
    highlightEl.className = '';
    switch (focusTarget) {
      case 'number':
        highlightEl.className = 'highlight__number';
        break;
      case 'holder':
        highlightEl.className = 'highlight__holder';
        break;
      case 'expire':
        highlightEl.className = 'highlight__expire';
        break;
      case 'cvv':
        highlightEl.className = 'highlight__cvv';
        break;
      default:
        highlightEl.className = 'hidden';
    }
  }

  // Validation Check
  function updateValidation() {
    const isNumValid = cardNumber.length >= 13;
    const isHolderValid = cardHolder.trim().length >= 2;
    const isMonthValid = !!expMonth && Number(expMonth) >= 1 && Number(expMonth) <= 12;
    const isYearValid = !!expYear && Number(expYear) >= new Date().getFullYear();
    const isCvvValid = /^\d{3,4}$/.test(cardCVV);
    const allValid = isNumValid && isHolderValid && isMonthValid && isYearValid && isCvvValid;

    if (numErrorMsg) {
      if (!isNumValid && cardNumber.length > 0) {
        numErrorMsg.style.display = 'block';
      } else {
        numErrorMsg.style.display = 'none';
      }
    }

    const submitBtn = document.getElementById('btn-submit-payment');
    if (submitBtn) {
      submitBtn.disabled = !allValid;
      submitBtn.style.opacity = allValid ? '1' : '0.65';
    }
  }

  // Event Listeners for Number Input
  if (numberInput) {
    numberInput.value = formatCardNumber(cardNumber);
    numberInput.addEventListener('input', (e) => {
      cardNumber = clampDigits(e.target.value, 16);
      e.target.value = formatCardNumber(cardNumber);
      renderCardNumberSlots();
      updateValidation();
    });

    numberInput.addEventListener('focus', () => {
      cardEl.classList.remove('flip');
      setHighlight('number');
    });

    numberInput.addEventListener('blur', () => {
      setHighlight(null);
      updateValidation();
    });
  }

  // Event Listeners for Holder Input
  if (holderInput) {
    holderInput.value = cardHolder;
    holderInput.addEventListener('input', (e) => {
      cardHolder = e.target.value.toUpperCase();
      if (holderDisplay) {
        holderDisplay.textContent = cardHolder || 'NAME ON CARD';
      }
      updateValidation();
    });

    holderInput.addEventListener('focus', () => {
      cardEl.classList.remove('flip');
      setHighlight('holder');
    });

    holderInput.addEventListener('blur', () => {
      setHighlight(null);
      updateValidation();
    });
  }

  // Event Listeners for Expiration Month
  if (monthSelect) {
    monthSelect.value = expMonth;
    monthSelect.addEventListener('change', (e) => {
      expMonth = e.target.value;
      if (monthDisplay) {
        monthDisplay.textContent = expMonth || 'MM';
      }
      updateValidation();
    });

    monthSelect.addEventListener('focus', () => {
      cardEl.classList.remove('flip');
      setHighlight('expire');
    });

    monthSelect.addEventListener('blur', () => {
      setHighlight(null);
      updateValidation();
    });
  }

  // Event Listeners for Expiration Year
  if (yearSelect) {
    yearSelect.value = expYear;
    yearSelect.addEventListener('change', (e) => {
      expYear = e.target.value;
      if (yearDisplay) {
        yearDisplay.textContent = expYear ? expYear.slice(-2) : 'YY';
      }
      updateValidation();
    });

    yearSelect.addEventListener('focus', () => {
      cardEl.classList.remove('flip');
      setHighlight('expire');
    });

    yearSelect.addEventListener('blur', () => {
      setHighlight(null);
      updateValidation();
    });
  }

  // Event Listeners for CVV Input (3D Back-Face Flip!)
  if (cvvInput) {
    cvvInput.value = cardCVV;
    cvvInput.addEventListener('input', (e) => {
      cardCVV = clampDigits(e.target.value, 4);
      e.target.value = cardCVV;
      if (cvvDisplay) {
        cvvDisplay.textContent = '*'.repeat(cardCVV.length) || '***';
      }
      updateValidation();
    });

    cvvInput.addEventListener('focus', () => {
      cardEl.classList.add('flip'); // 3D flip card to back!
      setHighlight('cvv');
    });

    cvvInput.addEventListener('blur', () => {
      cardEl.classList.remove('flip'); // 3D flip card back to front!
      setHighlight(null);
      updateValidation();
    });
  }

  // Allow clicking card to flip manually for 3D inspection
  cardEl.addEventListener('click', (e) => {
    // Only toggle if not clicking an interactive inner link/button
    if (document.activeElement !== cvvInput) {
      cardEl.classList.toggle('flip');
    }
  });

  // Initial runs
  renderCardNumberSlots();
  if (holderDisplay) holderDisplay.textContent = cardHolder || 'NAME ON CARD';
  if (monthDisplay) monthDisplay.textContent = expMonth || 'MM';
  if (yearDisplay) yearDisplay.textContent = expYear ? expYear.slice(-2) : 'YY';
  if (cvvDisplay) cvvDisplay.textContent = '*'.repeat(cardCVV.length) || '***';
  updateValidation();
}
