/**
 * Gym Tracker Pro - Smart Pedometer & Biomechanical Activity Engine
 * Real-time accelerometer peak detection, iOS motion permission handling,
 * adaptive stride calculation, and automated server synchronization.
 */

(function () {
  'use strict';

  // Global State
  let isTracking = false;
  let currentSteps = window.INITIAL_STEPS || 0;
  let currentGoal = window.INITIAL_GOAL || 10000;
  const userHeight = window.USER_HEIGHT || 175.0;
  const userWeight = window.USER_WEIGHT || 75.0;
  const userUnit = window.USER_UNIT || 'kg';

  // Motion Detection Variables
  let lastStepTime = 0;
  let stepDebounceMs = 280; // Minimum time between consecutive steps
  let threshold = 2.2;      // Acceleration delta threshold in m/s^2
  let gravityBaseline = 9.8;
  const filterFactor = 0.1; // Low-pass filter for gravity adaptation

  // Sync Debouncing
  let syncTimer = null;
  let hasPendingSync = false;

  // DOM Elements Cache
  const el = {};

  function init() {
    cacheElements();
    restoreLocalSteps();
    setupEventListeners();
    updateUI();
    initChart();
    checkSensorAvailability();

    // Auto-resume tracking if active prior to reload/navigation
    if (localStorage.getItem('gymtracker_pedometer_active') === 'true') {
      startTracking(true);
    }
  }

  function getTodayString() {
    return new Date().toISOString().split('T')[0];
  }

  function restoreLocalSteps() {
    try {
      const todayKey = 'gymtracker_steps_' + getTodayString();
      const cached = parseInt(localStorage.getItem(todayKey) || '0', 10);
      if (cached > currentSteps) {
        currentSteps = cached;
      }
    } catch (e) {
      console.warn('LocalStorage error reading steps:', e);
    }
  }

  function cacheElements() {
    el.stepCount = document.getElementById('pedometer-step-count');
    el.goalCount = document.getElementById('pedometer-goal-count');
    el.goalPct = document.getElementById('pedometer-goal-pct');
    el.distanceVal = document.getElementById('pedometer-distance-val');
    el.caloriesVal = document.getElementById('pedometer-calories-val');
    el.activeTimeVal = document.getElementById('pedometer-active-time-val');
    el.progressRing = document.getElementById('pedometer-progress-ring');
    el.toggleBtn = document.getElementById('btn-toggle-pedometer');
    el.toggleText = document.getElementById('pedometer-toggle-text');
    el.toggleIcon = document.getElementById('pedometer-toggle-icon');
    el.liveIndicator = document.getElementById('pedometer-live-indicator');
    el.stepPulse = document.getElementById('pedometer-step-pulse');
    el.permissionBanner = document.getElementById('pedometer-permission-banner');
    el.btnRequestPermission = document.getElementById('btn-request-motion-permission');
    el.sensitivitySelect = document.getElementById('pedometer-sensitivity');
    el.manualStepsInput = document.getElementById('manual-steps-input');
    el.btnSubmitManual = document.getElementById('btn-submit-manual-steps');
  }

  function setupEventListeners() {
    // Toggle Live Pedometer
    el.toggleBtn?.addEventListener('click', toggleTracking);

    // iOS Motion Permission button
    el.btnRequestPermission?.addEventListener('click', requestMotionPermission);

    // Sensitivity Adjustment
    el.sensitivitySelect?.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val === 'high') {
        threshold = 1.6;
        stepDebounceMs = 250;
      } else if (val === 'low') {
        threshold = 3.0;
        stepDebounceMs = 320;
      } else {
        threshold = 2.2;
        stepDebounceMs = 280;
      }
      showToast(`Pedometer sensitivity set to: ${val.toUpperCase()}`, 'info');
    });

    // Quick Add Buttons (+500, +1000, +2500, +5000)
    document.querySelectorAll('.btn-quick-add-steps').forEach((btn) => {
      btn.addEventListener('click', () => {
        const delta = parseInt(btn.dataset.steps, 10);
        if (delta && delta > 0) {
          addSteps(delta);
        }
      });
    });

    // Manual Steps Submission
    el.btnSubmitManual?.addEventListener('click', () => {
      const delta = parseInt(el.manualStepsInput?.value, 10);
      if (delta && delta > 0) {
        addSteps(delta);
        if (el.manualStepsInput) el.manualStepsInput.value = '';
      } else {
        showToast('Please enter a valid step number (e.g. 1500)', 'error');
      }
    });

    // Quick Goal Selector Pills
    document.querySelectorAll('.btn-set-step-goal').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const newGoal = parseInt(btn.dataset.goal, 10);
        if (newGoal && newGoal >= 1000) {
          await updateGoal(newGoal);
        }
      });
    });

    // Auto-save on page exit
    window.addEventListener('beforeunload', () => {
      if (hasPendingSync) {
        syncToServer(currentSteps);
      }
    });

    // PWA & Mobile Background Sync on tab visibility change
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        restoreLocalSteps();
        updateUI();
        if (hasPendingSync) {
          syncToServer(currentSteps);
        }
      }
    });

    // Network reconnect sync
    window.addEventListener('online', () => {
      if (hasPendingSync) {
        syncToServer(currentSteps);
      }
    });
  }

  function checkSensorAvailability() {
    if (typeof DeviceMotionEvent === 'undefined') {
      if (el.permissionBanner) {
        el.permissionBanner.innerHTML = `
          <div class="flex items-center justify-between text-xs text-amber-200">
            <span>ℹ️ Motion sensor not available in desktop browser. You can still use the <strong>Quick Step Adjuster</strong> to log steps!</span>
          </div>
        `;
        el.permissionBanner.classList.remove('hidden');
      }
      return;
    }

    // Check if iOS 13+ permission is required
    if (typeof DeviceMotionEvent.requestPermission === 'function') {
      el.permissionBanner?.classList.remove('hidden');
    }
  }

  async function requestMotionPermission() {
    if (typeof DeviceMotionEvent.requestPermission === 'function') {
      try {
        const response = await DeviceMotionEvent.requestPermission();
        if (response === 'granted') {
          el.permissionBanner?.classList.add('hidden');
          showToast('Motion sensor access granted! You can now start live tracking.', 'success');
          startTracking();
        } else {
          showToast('Motion permission denied. You can still log steps manually.', 'warning');
        }
      } catch (err) {
        console.error('Error requesting motion permission:', err);
        showToast('Could not request motion permission.', 'error');
      }
    }
  }

  function toggleTracking() {
    if (isTracking) {
      stopTracking();
    } else {
      if (typeof DeviceMotionEvent?.requestPermission === 'function') {
        requestMotionPermission();
      } else {
        startTracking();
      }
    }
  }

  function startTracking(isResume = false) {
    if (isTracking) return;
    try {
      window.addEventListener('devicemotion', handleMotion, false);
      isTracking = true;
      localStorage.setItem('gymtracker_pedometer_active', 'true');
      updateTrackingStateUI(true);
      if (!isResume) {
        showToast('Pedometer active! Walk with your phone in your pocket or hand.', 'success');
      }
    } catch (e) {
      console.error('Failed to attach motion listener', e);
      showToast('Could not start motion listener.', 'error');
    }
  }

  function stopTracking() {
    if (!isTracking) return;
    window.removeEventListener('devicemotion', handleMotion, false);
    isTracking = false;
    localStorage.removeItem('gymtracker_pedometer_active');
    updateTrackingStateUI(false);
    showToast('Pedometer paused. Steps saved.', 'info');
    syncToServer(currentSteps);
  }

  function handleMotion(e) {
    let acc = e.accelerationIncludingGravity || e.acceleration;
    if (!acc || acc.x === null || acc.y === null || acc.z === null) {
      return;
    }

    const x = acc.x;
    const y = acc.y;
    const z = acc.z;

    // Magnitude of 3D acceleration vector
    const totalAcc = Math.sqrt(x * x + y * y + z * z);

    // Adaptive low-pass baseline filter for gravity
    gravityBaseline = gravityBaseline * (1.0 - filterFactor) + totalAcc * filterFactor;
    const delta = Math.abs(totalAcc - gravityBaseline);

    const now = Date.now();
    if (delta > threshold && (now - lastStepTime) > stepDebounceMs) {
      lastStepTime = now;
      onStepDetected();
    }
  }

  function onStepDetected() {
    currentSteps += 1;
    saveLocalSteps();
    updateUI();
    flashStepPulse();

    // Haptic feedback if enabled/supported
    if (navigator.vibrate) {
      navigator.vibrate(15);
    }

    scheduleSync();
  }

  function saveLocalSteps() {
    try {
      localStorage.setItem('gymtracker_steps_' + getTodayString(), currentSteps.toString());
    } catch (e) {
      // ignore localstorage quota error
    }
  }

  function flashStepPulse() {
    if (el.stepPulse) {
      el.stepPulse.classList.remove('opacity-0', 'scale-90');
      el.stepPulse.classList.add('opacity-100', 'scale-110');
      setTimeout(() => {
        el.stepPulse.classList.remove('opacity-100', 'scale-110');
        el.stepPulse.classList.add('opacity-0', 'scale-90');
      }, 180);
    }
  }

  function addSteps(delta) {
    currentSteps += delta;
    saveLocalSteps();
    updateUI();
    showToast(`Added +${delta.toLocaleString()} steps!`, 'success');
    syncToServer(currentSteps);
  }

  function scheduleSync() {
    hasPendingSync = true;
    if (syncTimer) clearTimeout(syncTimer);
    // Debounce server sync every 8 seconds while continuously walking
    syncTimer = setTimeout(() => {
      syncToServer(currentSteps);
    }, 8000);
  }

  async function syncToServer(steps) {
    hasPendingSync = false;
    saveLocalSteps();

    // Trigger Service Worker background sync if supported
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
      navigator.serviceWorker.ready.then((reg) => {
        reg.sync.register('sync-steps').catch(() => {});
      }).catch(() => {});
    }

    try {
      const todayStr = getTodayString();
      const res = await fetch('/api/steps/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          steps: steps,
          date: todayStr
        })
      });
      const data = await res.json();
      if (res.ok && data.success && data.data) {
        // Update with verified server metrics
        currentSteps = data.data.steps;
        currentGoal = data.data.goal;
        updateUI(data.data);
      }
    } catch (err) {
      console.warn('Steps sync delayed (offline or busy network):', err);
    }
  }

  async function updateGoal(newGoal) {
    try {
      const res = await fetch('/api/steps/goal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: newGoal })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        currentGoal = newGoal;
        updateUI();
        highlightActiveGoalPill(newGoal);
        showToast(`Daily step goal set to ${newGoal.toLocaleString()} steps!`, 'success');
      }
    } catch (err) {
      showToast('Could not update goal.', 'error');
    }
  }

  function highlightActiveGoalPill(goal) {
    document.querySelectorAll('.btn-set-step-goal').forEach((btn) => {
      const g = parseInt(btn.dataset.goal, 10);
      if (g === goal) {
        btn.classList.add('bg-[#E6D5B8]', 'text-[#0A1128]', 'border-[#E6D5B8]');
        btn.classList.remove('bg-gray-800/80', 'text-gray-300', 'border-gray-700');
      } else {
        btn.classList.remove('bg-[#E6D5B8]', 'text-[#0A1128]', 'border-[#E6D5B8]');
        btn.classList.add('bg-gray-800/80', 'text-gray-300', 'border-gray-700');
      }
    });
  }

  function updateUI(metrics) {
    // Stride calculation
    const strideM = Math.max(0.5, Math.min(1.0, (userHeight * 0.414) / 100.0));
    const distKm = (currentSteps * strideM) / 1000.0;
    const distMiles = distKm * 0.621371;
    const weightKg = userUnit === 'lbs' ? userWeight / 2.20462 : userWeight;
    const cals = Math.round(currentSteps * 0.045 * (weightKg / 75.0));
    const activeMins = Math.round(currentSteps / 105.0);
    const pct = Math.min(100, Math.round((currentSteps / currentGoal) * 100));

    // Update numbers
    if (el.stepCount) el.stepCount.textContent = currentSteps.toLocaleString();
    if (el.goalCount) el.goalCount.textContent = currentGoal.toLocaleString();
    if (el.goalPct) el.goalPct.textContent = `${pct}%`;
    if (el.distanceVal) {
      el.distanceVal.textContent = userUnit === 'kg' ? `${distKm.toFixed(2)} km` : `${distMiles.toFixed(2)} mi`;
    }
    if (el.caloriesVal) el.caloriesVal.textContent = `${cals} kcal`;
    if (el.activeTimeVal) el.activeTimeVal.textContent = `${activeMins} min`;

    // Circular progress SVG: stroke-dashoffset
    if (el.progressRing) {
      const radius = 90;
      const circumference = 2 * Math.PI * radius; // ~565.48
      const offset = circumference - (pct / 100) * circumference;
      el.progressRing.style.strokeDashoffset = offset;
    }
  }

  function updateTrackingStateUI(active) {
    if (active) {
      if (el.toggleBtn) {
        el.toggleBtn.classList.remove('bg-[#2563EB]', 'hover:bg-[#1d4ed8]');
        el.toggleBtn.classList.add('bg-amber-600', 'hover:bg-amber-500');
      }
      if (el.toggleText) el.toggleText.textContent = 'PAUSE LIVE TRACKING';
      if (el.toggleIcon) el.toggleIcon.textContent = '⏸';
      if (el.liveIndicator) {
        el.liveIndicator.classList.remove('hidden');
        el.liveIndicator.classList.add('flex');
      }
    } else {
      if (el.toggleBtn) {
        el.toggleBtn.classList.remove('bg-amber-600', 'hover:bg-amber-500');
        el.toggleBtn.classList.add('bg-[#2563EB]', 'hover:bg-[#1d4ed8]');
      }
      if (el.toggleText) el.toggleText.textContent = 'START LIVE SENSING';
      if (el.toggleIcon) el.toggleIcon.textContent = '▶';
      if (el.liveIndicator) {
        el.liveIndicator.classList.add('hidden');
        el.liveIndicator.classList.remove('flex');
      }
    }
  }

  function initChart() {
    const canvas = document.getElementById('pedometer-history-chart');
    if (!canvas || !window.STEP_HISTORY) return;

    const labels = window.STEP_HISTORY.map((h) => h.day_name);
    const stepsData = window.STEP_HISTORY.map((h) => h.steps);
    const goalData = window.STEP_HISTORY.map((h) => h.goal);

    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Daily Steps',
            data: stepsData,
            backgroundColor: '#2563EB', // Royal Blue
            hoverBackgroundColor: '#3B82F6',
            borderRadius: 8,
            borderSkipped: false
          },
          {
            type: 'line',
            label: 'Daily Goal',
            data: goalData,
            borderColor: '#E6D5B8', // Warm Beige
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#94A3B8',
              font: { size: 11, weight: 'bold' }
            }
          },
          tooltip: {
            backgroundColor: '#101C3D',
            titleColor: '#E6D5B8',
            bodyColor: '#FAF7F2',
            borderColor: '#E6D5B8',
            borderWidth: 1,
            padding: 10
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#94A3B8', font: { size: 11 } }
          },
          y: {
            grid: { color: 'rgba(230, 213, 184, 0.08)' },
            ticks: { color: '#94A3B8', font: { size: 11 } },
            beginAtZero: true
          }
        }
      }
    });
  }

  function showToast(message, type = 'info') {
    if (window.showToast) {
      window.showToast(message, type);
    }
  }

  // Auto initialize on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
