/**
 * Travel Connect & RemitMind Authentication Engine
 * Faithful implementation of 21st.dev / coderislive07 / travel-connect-signin-1
 * Interactive Canvas World Map Animation + Seamless Auth Flow
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeSupport();
  initWorldMapCanvas();
  initPasswordToggle();
  initAuthForm();
  initPersonaShortcuts();
  checkLogoutQuery();
});

/* ==========================================================================
   1. Theme Synchronization
   ========================================================================== */
function initThemeSupport() {
  const storedTheme = localStorage.getItem('remitmind_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', storedTheme);
  updateThemeToggleIcon(storedTheme);

  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const target = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', target);
      localStorage.setItem('remitmind_theme', target);
      updateThemeToggleIcon(target);
      // Redraw canvas with new palette
      if (window.redrawWorldMap) window.redrawWorldMap();
    });
  }
}

function updateThemeToggleIcon(theme) {
  const container = document.getElementById('theme-icon-container');
  if (!container) return;

  if (theme === 'light') {
    container.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    `;
  } else {
    container.innerHTML = `
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
   2. Interactive World Map Animation (21st.dev faithful engine)
   ========================================================================== */
function initWorldMapCanvas() {
  const canvas = document.getElementById('travel-map-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  let width = 0;
  let height = 0;
  let animId = null;
  let startTime = Date.now();
  let continentDots = [];

  // Generate continent dots matching 21st.dev logic
  function generateDots(w, h) {
    const dots = [];
    const step = 11;
    for (let x = 0; x < w; x += step) {
      for (let y = 0; y < h; y += step) {
        const inNA = (x < w * 0.28 && x > w * 0.06 && y < h * 0.42 && y > h * 0.12);
        const inSA = (x < w * 0.28 && x > w * 0.14 && y < h * 0.82 && y > h * 0.44);
        const inEU = (x < w * 0.48 && x > w * 0.31 && y < h * 0.36 && y > h * 0.14);
        const inAF = (x < w * 0.52 && x > w * 0.34 && y < h * 0.68 && y > h * 0.36);
        const inAS = (x < w * 0.76 && x > w * 0.44 && y < h * 0.54 && y > h * 0.12);
        const inAU = (x < w * 0.86 && x > w * 0.68 && y < h * 0.82 && y > h * 0.60);

        if ((inNA || inSA || inEU || inAF || inAS || inAU) && Math.random() > 0.28) {
          dots.push({
            x,
            y,
            radius: 1.15,
            opacity: Math.random() * 0.45 + 0.18
          });
        }
      }
    }
    return dots;
  }

  // Active travel connection routes (Dubai -> BD, Riyadh -> BD, KL -> BD, London -> BD)
  function getRoutes(w, h) {
    const dhaka = { x: w * 0.63, y: h * 0.38 }; // Bangladesh destination
    return [
      {
        id: 'DXB-DAC',
        start: { x: w * 0.49, y: h * 0.37 }, // Dubai UAE
        end: dhaka,
        delay: 0,
        duration: 3.2,
        color: '#3b82f6',
        label: 'DXB ➔ DAC'
      },
      {
        id: 'RUH-DAC',
        start: { x: w * 0.45, y: h * 0.42 }, // Riyadh KSA
        end: dhaka,
        delay: 1.8,
        duration: 3.5,
        color: '#6366f1',
        label: 'RUH ➔ DAC'
      },
      {
        id: 'KUL-DAC',
        start: { x: w * 0.68, y: h * 0.52 }, // Kuala Lumpur MYS
        end: dhaka,
        delay: 0.8,
        duration: 2.8,
        color: '#06b6d4',
        label: 'KUL ➔ DAC'
      },
      {
        id: 'LHR-DAC',
        start: { x: w * 0.35, y: h * 0.22 }, // London UK
        end: dhaka,
        delay: 2.6,
        duration: 4.2,
        color: '#3b82f6',
        label: 'LHR ➔ DAC'
      },
      {
        id: 'JFK-DAC',
        start: { x: w * 0.22, y: h * 0.28 }, // New York USA
        end: { x: w * 0.49, y: h * 0.37 },   // To Dubai Hub
        delay: 1.2,
        duration: 4.0,
        color: '#8b5cf6',
        label: 'JFK ➔ DXB'
      }
    ];
  }

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    width = rect.width;
    height = rect.height;

    // High DPI crispness
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    continentDots = generateDots(width, height);
  }

  function render() {
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    const dotColor = isDark ? '59, 130, 246' : '37, 99, 235';

    ctx.clearRect(0, 0, width, height);

    // 1. Draw Continent Dots
    for (let i = 0; i < continentDots.length; i++) {
      const dot = continentDots[i];
      ctx.beginPath();
      ctx.arc(dot.x, dot.y, dot.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${dotColor}, ${dot.opacity})`;
      ctx.fill();
    }

    // 2. Animate Travel Route Arcs & Pulses
    const elapsed = (Date.now() - startTime) / 1000;
    const routes = getRoutes(width, height);

    routes.forEach(route => {
      const cycleTime = 12; // Loop cycle seconds
      const currentRel = (elapsed % cycleTime) - route.delay;
      if (currentRel <= 0) return;

      const progress = Math.min(currentRel / route.duration, 1);

      // Arc control point for graceful curvature
      const midX = (route.start.x + route.end.x) / 2;
      const midY = Math.min(route.start.y, route.end.y) - 35; // Curve upward

      // Draw faint route trajectory
      ctx.beginPath();
      ctx.moveTo(route.start.x, route.start.y);
      ctx.quadraticCurveTo(midX, midY, route.end.x, route.end.y);
      ctx.strokeStyle = isDark ? 'rgba(59, 130, 246, 0.22)' : 'rgba(37, 99, 235, 0.18)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Compute current position along Quadratic Bezier curve
      const t = progress;
      const invT = 1 - t;
      const currX = invT * invT * route.start.x + 2 * invT * t * midX + t * t * route.end.x;
      const currY = invT * invT * route.start.y + 2 * invT * t * midY + t * t * route.end.y;

      // Draw traveled line segment
      ctx.beginPath();
      ctx.moveTo(route.start.x, route.start.y);
      // Intermediate arc up to t
      const curMidX = (route.start.x + currX) / 2;
      const curMidY = ((route.start.y + currY) / 2) - (35 * t);
      ctx.quadraticCurveTo(curMidX, curMidY, currX, currY);
      ctx.strokeStyle = route.color;
      ctx.lineWidth = 1.8;
      ctx.stroke();

      // Origin station node
      ctx.beginPath();
      ctx.arc(route.start.x, route.start.y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = route.color;
      ctx.fill();

      // Moving Head Pulsing Light
      ctx.beginPath();
      ctx.arc(currX, currY, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.shadowColor = route.color;
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.shadowBlur = 0; // reset

      // Moving Head Halo
      ctx.beginPath();
      ctx.arc(currX, currY, 8, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(59, 130, 246, 0.28)';
      ctx.fill();

      // Destination station ripple when reached
      if (progress >= 1) {
        ctx.beginPath();
        ctx.arc(route.end.x, route.end.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#10b981'; // Green arrival
        ctx.fill();

        // Ripple beacon
        const ripple = (elapsed * 2) % 1;
        ctx.beginPath();
        ctx.arc(route.end.x, route.end.y, 4 + ripple * 10, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(16, 185, 129, ${1 - ripple})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    });

    animId = requestAnimationFrame(render);
  }

  // Observe resize of parent
  const observer = new ResizeObserver(() => {
    resize();
  });
  observer.observe(canvas.parentElement);

  resize();
  render();

  window.redrawWorldMap = () => {
    continentDots = generateDots(width, height);
  };
}

/* ==========================================================================
   3. Password Visibility Toggle
   ========================================================================== */
function initPasswordToggle() {
  const toggleBtn = document.getElementById('toggle-password-btn');
  const passwordInput = document.getElementById('password');
  if (!toggleBtn || !passwordInput) return;

  toggleBtn.addEventListener('click', () => {
    const isPassword = passwordInput.getAttribute('type') === 'password';
    passwordInput.setAttribute('type', isPassword ? 'text' : 'password');

    // Update icon (Eye vs Eye-Off)
    toggleBtn.innerHTML = isPassword ? `
      <!-- Eye-Off icon -->
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
        <line x1="1" y1="1" x2="23" y2="23"></line>
      </svg>
    ` : `
      <!-- Eye icon -->
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>
    `;
    toggleBtn.setAttribute('title', isPassword ? 'Hide password' : 'Show password');
  });
}

/* ==========================================================================
   4. Form Submission & Mock / Real Authentication
   ========================================================================== */
function initAuthForm() {
  const form = document.getElementById('login-form');
  const googleBtn = document.getElementById('btn-google-login');

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;

      if (!email || !password) {
        showToast('Please provide both email and password.', 'error');
        return;
      }

      handleLoginSuccess(email);
    });
  }

  if (googleBtn) {
    googleBtn.addEventListener('click', () => {
      showToast('Connecting with Google Secure OAuth...', 'success');
      setTimeout(() => {
        handleLoginSuccess('gajiulislam@gmail.com', 'Gajiul Islam');
      }, 700);
    });
  }
}

function handleLoginSuccess(email, customName = null) {
  const submitBtn = document.getElementById('btn-submit-signin');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
        <path d="M12 2a10 10 0 0 1 10 10" stroke="#ffffff"></path>
      </svg>
      <span>Authenticating...</span>
    `;
  }

  // Detect persona based on email or defaults
  let user = {
    id: 'u_send_001',
    name: customName || 'Gajiul Islam',
    role: 'sender',
    country: 'UAE',
    corridor: 'AED_BDT',
    email: email,
    avatar: 'assets/remitmind-emblem.png'
  };

  const lowerEmail = email.toLowerCase();
  let targetView = 'pay';

  if (lowerEmail.includes('analyst') || lowerEmail.includes('nusrat')) {
    user = {
      id: 'u_analyst_01',
      name: 'Nusrat Jahan',
      role: 'analyst',
      country: 'Bangladesh',
      corridor: 'Dhaka HQ',
      email: email,
      avatar: 'assets/remitmind-emblem.png'
    };
    targetView = 'analyst';
  } else if (lowerEmail.includes('agent') || lowerEmail.includes('karim')) {
    user = {
      id: 'u_agent_01',
      name: 'Karim Ahmed',
      role: 'agent',
      country: 'Bangladesh',
      corridor: 'Balaganj, Sylhet',
      email: email,
      avatar: 'assets/remitmind-emblem.png'
    };
    targetView = 'agent';
  } else if (lowerEmail.includes('amina') || lowerEmail.includes('receiver')) {
    user = {
      id: 'u_recv_001',
      name: 'Amina Begum',
      role: 'receiver',
      country: 'Bangladesh',
      corridor: 'Sylhet',
      email: email,
      avatar: 'assets/remitmind-emblem.png'
    };
    targetView = 'receiver';
  }

  // Save to localStorage
  localStorage.setItem('remitmind_user', JSON.stringify(user));

  showToast(`Welcome back, ${user.name}! Redirecting...`, 'success');

  // Check URL redirect param or go to app.html
  const urlParams = new URLSearchParams(window.location.search);
  const redirectTarget = urlParams.get('redirect') || `app.html?view=${targetView}`;

  setTimeout(() => {
    window.location.href = redirectTarget;
  }, 950);
}

/* ==========================================================================
   5. Persona 1-Click Shortcuts (Hackathon Quick Demo)
   ========================================================================== */
function initPersonaShortcuts() {
  const chips = document.querySelectorAll('.persona-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const email = chip.getAttribute('data-email');
      const password = chip.getAttribute('data-pass') || 'password123';
      const name = chip.getAttribute('data-name');

      const emailInput = document.getElementById('email');
      const passInput = document.getElementById('password');

      if (emailInput && passInput) {
        emailInput.value = email;
        passInput.value = password;
        showToast(`Auto-filled: ${name} (${chip.getAttribute('data-role')})`, 'success');
        
        // Auto trigger submit after 300ms for delightful quick login experience
        setTimeout(() => {
          handleLoginSuccess(email, name);
        }, 350);
      }
    });
  });
}

/* ==========================================================================
   6. Logout Check
   ========================================================================== */
function checkLogoutQuery() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('logout') === 'true') {
    localStorage.removeItem('remitmind_user');
    showToast('You have been logged out securely.', 'success');
  }
}

/* ==========================================================================
   Toast Helper
   ========================================================================== */
function showToast(msg, type = 'success') {
  let container = document.getElementById('login-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'login-toast-container';
    container.className = 'login-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `login-toast toast-${type}`;
  
  const icon = type === 'success' ? `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
  ` : `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
  `;

  toast.innerHTML = `${icon}<span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(15px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}
