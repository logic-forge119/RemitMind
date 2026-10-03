/**
 * AppleStyleDock Engine
 * Implements macOS / Magic UI Apple Style Dock with:
 * - Buttery-smooth magnification physics on mouse movement
 * - Floating DockLabel tooltips
 * - Native Lucide icons (Home, Package, Component, Activity, ScrollText, Mail, SunMoon)
 * - Synchronized Light/Dark theme switching
 * - Interactive Change Log & Email modals
 * - Seamless view switching on app.html and section scrolling on index.html
 */

document.addEventListener('DOMContentLoaded', () => {
  initAppleDock();
  initDockModals();
});

function initAppleDock() {
  const dock = document.querySelector('.apple-dock');
  if (!dock) return;

  const items = dock.querySelectorAll('.dock-item');
  const maxDistance = 120; // Radius of magnification influence in px
  const maxScale = 1.42;   // Peak magnification scale

  // Magnification Physics on Mouse Move (Supports Vertical Left Dock & Horizontal Modes)
  dock.addEventListener('mousemove', (e) => {
    const isVertical = window.getComputedStyle(dock).flexDirection === 'column';
    const mouseCoord = isVertical ? e.clientY : e.clientX;

    items.forEach((item) => {
      const rect = item.getBoundingClientRect();
      const itemCenter = isVertical ? (rect.top + rect.height / 2) : (rect.left + rect.width / 2);
      const distance = Math.abs(mouseCoord - itemCenter);

      if (distance < maxDistance) {
        // Cosine falloff curve for natural Apple-style spring feeling
        const factor = Math.cos((distance / maxDistance) * (Math.PI / 2));
        const scale = 1 + (maxScale - 1) * factor;
        const offset = (scale - 1) * 18;

        if (isVertical) {
          // Push outward to the right when docked vertically on the left
          item.style.transform = `scale(${scale.toFixed(3)}) translateX(${offset.toFixed(1)}px)`;
        } else {
          // Lift upward when docked horizontally
          item.style.transform = `scale(${scale.toFixed(3)}) translateY(-${offset.toFixed(1)}px)`;
        }
        item.classList.add('dock-magnified');
      } else {
        item.style.transform = 'scale(1) translate(0, 0)';
        item.classList.remove('dock-magnified');
      }
    });
  });

  // Smooth reset on mouse leave
  dock.addEventListener('mouseleave', () => {
    items.forEach((item) => {
      item.style.transform = 'scale(1) translate(0, 0)';
      item.classList.remove('dock-magnified');
    });
  });

  // Theme Toggle Button in Dock
  const dockThemeBtn = document.getElementById('dock-theme');
  if (dockThemeBtn) {
    dockThemeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      toggleSystemTheme();
    });
  }

  // Change Log Button
  const dockChangelogBtn = document.getElementById('dock-changelog');
  if (dockChangelogBtn) {
    dockChangelogBtn.addEventListener('click', (e) => {
      e.preventDefault();
      openDockModal('dock-changelog-modal');
    });
  }

  // Email Button
  const dockEmailBtn = document.getElementById('dock-email');
  if (dockEmailBtn) {
    dockEmailBtn.addEventListener('click', (e) => {
      e.preventDefault();
      openDockModal('dock-email-modal');
    });
  }

  // If on app.html, integrate dock items directly with app view tabs
  if (window.location.pathname.includes('app.html')) {
    const viewMapping = {
      'dock-products': 'pay',
      'dock-components': 'receiver',
      'dock-activity': 'analyst',
      'dock-home': null // Links to index.html
    };

    Object.entries(viewMapping).forEach(([dockId, viewName]) => {
      const el = document.getElementById(dockId);
      if (el && viewName) {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          const targetTab = document.querySelector(`.app-nav-tab[data-view="${viewName}"]`);
          if (targetTab) {
            targetTab.click();
            // Highlight active in dock
            items.forEach(i => i.classList.remove('active'));
            el.classList.add('active');
          }
        });
      }
    });

    // Synchronize top navigation tab clicks back to the Apple Dock
    const topNavTabs = document.querySelectorAll('.app-nav-tab');
    topNavTabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const view = tab.dataset.view;
        items.forEach(i => i.classList.remove('active'));
        if (view === 'pay') document.getElementById('dock-products')?.classList.add('active');
        else if (view === 'receiver') document.getElementById('dock-components')?.classList.add('active');
        else if (view === 'analyst') document.getElementById('dock-activity')?.classList.add('active');
      });
    });
  } else {
    // Smooth scroll for in-page anchors on index.html
    const anchorItems = dock.querySelectorAll('a[href^="#"]');
    anchorItems.forEach((anchor) => {
      anchor.addEventListener('click', (e) => {
        const targetId = anchor.getAttribute('href');
        if (targetId && targetId !== '#') {
          const targetEl = document.querySelector(targetId);
          if (targetEl) {
            e.preventDefault();
            targetEl.scrollIntoView({ behavior: 'smooth' });
            items.forEach(i => i.classList.remove('active'));
            anchor.classList.add('active');
          }
        }
      });
    });
  }
}

/**
 * Global Theme Toggler synced with existing state
 */
function toggleSystemTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('remitmind_theme', newTheme);

  // Trigger existing theme icon updates if functions exist
  if (typeof updateThemeIcon === 'function') {
    updateThemeIcon(newTheme);
  }
  if (typeof updateAppThemeIcon === 'function') {
    updateAppThemeIcon(newTheme);
  }

  // Toast notification
  if (typeof showToast === 'function') {
    showToast(`Switched to ${newTheme === 'dark' ? 'Dark' : 'Light'} Mode`);
  } else if (typeof showAppToast === 'function') {
    showAppToast(`Switched to ${newTheme === 'dark' ? 'Dark' : 'Light'} Mode`);
  }
}

/**
 * Dock Modals (Change Log & Email)
 */
function initDockModals() {
  // Close buttons
  document.querySelectorAll('.dock-modal-close, .dock-modal-backdrop').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const modal = e.target.closest('.dock-modal');
      if (modal) {
        closeDockModal(modal.id);
      }
    });
  });

  // ESC key to close
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.dock-modal.active').forEach((m) => {
        closeDockModal(m.id);
      });
    }
  });

  // Handle Email Form Submission
  const emailForm = document.getElementById('dock-email-form');
  if (emailForm) {
    emailForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const sendBtn = emailForm.querySelector('button[type="submit"]');
      const originalText = sendBtn.innerHTML;
      sendBtn.innerHTML = `<span>Sending Message...</span>`;
      sendBtn.disabled = true;

      setTimeout(() => {
        sendBtn.innerHTML = `<span>Message Sent Successfully</span>`;
        sendBtn.style.background = 'var(--upay-emerald, #10b981)';
        sendBtn.style.color = '#fff';

        setTimeout(() => {
          closeDockModal('dock-email-modal');
          emailForm.reset();
          sendBtn.innerHTML = originalText;
          sendBtn.disabled = false;
          sendBtn.style.background = '';
          sendBtn.style.color = '';
          if (typeof showToast === 'function') {
            showToast('Email sent to upay Remittance Operations Desk');
          } else if (typeof showAppToast === 'function') {
            showAppToast('Email sent to upay Remittance Operations Desk');
          }
        }, 1200);
      }, 800);
    });
  }
}

function openDockModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeDockModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}
