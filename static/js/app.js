/**
 * Gym Tracker Pro - Core Application Scripts
 * Handles Theme Toggling (Dark/Light), 3D card tilt interactions,
 * dynamic motivational quotes, and global toast notifications.
 */

// 0. Theme Switcher Engine (Dark Theme ↔ White/Light Theme)
function initThemeToggle() {
  const savedTheme = localStorage.getItem('gym_theme') || 'dark';
  applyTheme(savedTheme);

  document.querySelectorAll('.btn-theme-toggle').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const isLight = document.documentElement.classList.contains('light');
      const nextTheme = isLight ? 'dark' : 'light';
      applyTheme(nextTheme);
      localStorage.setItem('gym_theme', nextTheme);
      if (typeof showToast === 'function') {
        showToast(`Switched to ${nextTheme === 'light' ? 'Light Theme' : 'Dark Theme'}`, 'info');
      }
    });
  });
}

function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.classList.remove('dark');
    document.documentElement.classList.add('light');
    document.querySelectorAll('.theme-icon').forEach(el => el.textContent = '🌙');
    document.querySelectorAll('.theme-label').forEach(el => el.textContent = 'Dark');
  } else {
    document.documentElement.classList.remove('light');
    document.documentElement.classList.add('dark');
    document.querySelectorAll('.theme-icon').forEach(el => el.textContent = '☀️');
    document.querySelectorAll('.theme-label').forEach(el => el.textContent = 'Light');
  }
}

// 1. 3D Card Tilt Interaction Engine (Safe for mobile: only activates on mouse devices)
function init3DTiltCards() {
  // Disable on touch screens to prevent interference with mobile scrolling
  if (!window.matchMedia('(pointer: fine)').matches) return;

  const cards = document.querySelectorAll('.tilt-card');

  cards.forEach((card) => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const cardWidth = rect.width;
      const cardHeight = rect.height;
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const rotateY = ((mouseX / cardWidth) - 0.5) * 14;
      const rotateX = ((mouseY / cardHeight) - 0.5) * -14;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });
  });
}

// 2. Motivational Quotes Library & Engine
const MOTIVATIONAL_QUOTES = [
  { quote: "The only bad workout is the one that didn't happen.", author: "Gym Proverb" },
  { quote: "Strength does not come from physical capacity. It comes from an indomitable will.", author: "Mahatma Gandhi" },
  { quote: "Success starts with self-discipline.", author: "Dwayne Johnson" },
  { quote: "The resistance that you fight physically in the gym and the resistance that you fight in life can only build a strong character.", author: "Arnold Schwarzenegger" },
  { quote: "Action is the foundational key to all success.", author: "Pablo Picasso" },
  { quote: "Don't count the days, make the days count.", author: "Muhammad Ali" },
  { quote: "Discipline is choosing between what you want now and what you want most.", author: "Abraham Lincoln" },
  { quote: "Today I will do what others won't, so tomorrow I can accomplish what others can't.", author: "Jerry Rice" },
  { quote: "The last three or four reps is what makes the muscle grow. This area of pain divides a champion from someone who is not a champion.", author: "Arnold Schwarzenegger" },
  { quote: "Small disciplines repeated with consistency every day lead to great achievements.", author: "John C. Maxwell" }
];

function setDynamicMotivationalQuote() {
  const quoteElem = document.getElementById('motivational-quote-text');
  const authorElem = document.getElementById('motivational-quote-author');
  if (!quoteElem) return;

  // Use day of the year to provide a stable daily quote, or random
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 0);
  const diff = now - startOfYear;
  const dayOfYear = Math.floor(diff / (1000 * 60 * 60 * 24));
  const selected = MOTIVATIONAL_QUOTES[dayOfYear % MOTIVATIONAL_QUOTES.length];

  quoteElem.textContent = `"${selected.quote}"`;
  if (authorElem) {
    authorElem.textContent = `— ${selected.author}`;
  }
}

function refreshRandomQuote() {
  const quoteElem = document.getElementById('motivational-quote-text');
  const authorElem = document.getElementById('motivational-quote-author');
  if (!quoteElem) return;

  const randIdx = Math.floor(Math.random() * MOTIVATIONAL_QUOTES.length);
  const selected = MOTIVATIONAL_QUOTES[randIdx];

  quoteElem.style.opacity = '0';
  setTimeout(() => {
    quoteElem.textContent = `"${selected.quote}"`;
    if (authorElem) authorElem.textContent = `— ${selected.author}`;
    quoteElem.style.opacity = '1';
  }, 200);
}

// 3. Global Toast System
function showToast(message, type = 'success', title = null) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';

  let iconHtml = '';
  let borderColor = '#333';

  if (type === 'success') {
    borderColor = '#CCFF00';
    iconHtml = `<div class="w-8 h-8 rounded-full bg-[#CCFF00]/10 flex items-center justify-center text-[#CCFF00] font-bold">✓</div>`;
  } else if (type === 'pr') {
    borderColor = '#FFD700';
    iconHtml = `<div class="w-8 h-8 rounded-full bg-[#FFD700]/20 flex items-center justify-center text-[#FFD700] text-lg font-bold">🏆</div>`;
  } else if (type === 'error') {
    borderColor = '#FF3366';
    iconHtml = `<div class="w-8 h-8 rounded-full bg-[#FF3366]/10 flex items-center justify-center text-[#FF3366] font-bold">✕</div>`;
  } else {
    iconHtml = `<div class="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400 font-bold">i</div>`;
  }

  toast.style.borderColor = borderColor;
  toast.innerHTML = `
    ${iconHtml}
    <div class="flex-1">
      ${title ? `<div class="text-xs font-bold uppercase tracking-wider text-gray-400">${title}</div>` : ''}
      <div class="text-sm font-semibold text-white">${message}</div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// 4. Initialize DOM triggers
document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  init3DTiltCards();
  setDynamicMotivationalQuote();

  const quoteRefreshBtn = document.getElementById('btn-refresh-quote');
  if (quoteRefreshBtn) {
    quoteRefreshBtn.addEventListener('click', refreshRandomQuote);
  }

  // Mobile menu toggle
  const mobileToggle = document.getElementById('mobile-menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  if (mobileToggle && mobileMenu) {
    mobileToggle.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
    });
  }
});
