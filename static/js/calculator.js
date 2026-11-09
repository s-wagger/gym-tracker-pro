/**
 * Gym Tracker Pro - 1RM Analytical Engine
 * Live formula calculation, formula comparison (Epley, Brzycki, Lombardi),
 * training zone breakdown (50%, 75%, 85%, 90%, etc.), and periodization guidance.
 */

function initOneRepMaxCalculator() {
  const weightInput = document.getElementById('calc-weight');
  const repsInput = document.getElementById('calc-reps');
  const weightSlider = document.getElementById('calc-weight-slider');
  const repsSlider = document.getElementById('calc-reps-slider');
  const unitSelect = document.getElementById('calc-unit');

  if (!weightInput || !repsInput) return;

  function recalculateAll() {
    const weight = parseFloat(weightInput.value || 0);
    const reps = parseInt(repsInput.value || 0);
    const unit = unitSelect ? unitSelect.value : 'kg';

    // Synchronize sliders
    if (weightSlider && weightSlider.value != weight) weightSlider.value = weight;
    if (repsSlider && repsSlider.value != reps) repsSlider.value = reps;

    if (weight <= 0 || reps <= 0) {
      renderZeroState();
      return;
    }

    // Formulas
    // 1. Epley: 1RM = W * (1 + R / 30)
    let epley1RM = reps === 1 ? weight : weight * (1.0 + (reps / 30.0));
    epley1RM = Math.round(epley1RM * 10) / 10;

    // 2. Brzycki: W * (36 / (37 - R))
    let brzycki1RM = reps === 1 ? weight : (reps < 37 ? weight * (36.0 / (37.0 - reps)) : weight * 2);
    brzycki1RM = Math.round(brzycki1RM * 10) / 10;

    // 3. Lombardi: W * (R ^ 0.10)
    let lombardi1RM = reps === 1 ? weight : weight * Math.pow(reps, 0.10);
    lombardi1RM = Math.round(lombardi1RM * 10) / 10;

    // Update Big Display
    const main1RMDisplay = document.getElementById('display-1rm-val');
    const unitDisplay = document.getElementById('display-1rm-unit');
    const formulaDisplay = document.getElementById('display-formula-breakdown');
    
    if (main1RMDisplay) main1RMDisplay.textContent = epley1RM.toFixed(1);
    if (unitDisplay) unitDisplay.textContent = unit;
    if (formulaDisplay) {
      formulaDisplay.textContent = `${weight} × (1 + ${reps}/30) = ${epley1RM} ${unit}`;
    }

    // Comparisons
    const brzyckiElem = document.getElementById('display-brzycki-val');
    const lombardiElem = document.getElementById('display-lombardi-val');
    if (brzyckiElem) brzyckiElem.textContent = `${brzycki1RM} ${unit}`;
    if (lombardiElem) lombardiElem.textContent = `${lombardi1RM} ${unit}`;

    // Render Training Zones
    renderTrainingZones(epley1RM, unit);
  }

  // Initialize Barbell Plate Loader Engine
  initPlateLoader();

  function renderZeroState() {
    const main1RMDisplay = document.getElementById('display-1rm-val');
    if (main1RMDisplay) main1RMDisplay.textContent = '0.0';
    const container = document.getElementById('training-zones-container');
    if (container) container.innerHTML = `<div class="text-center py-8 text-gray-500">Enter weight and reps to generate training zones.</div>`;
  }

  // Event Listeners
  weightInput.addEventListener('input', recalculateAll);
  repsInput.addEventListener('input', recalculateAll);
  if (unitSelect) unitSelect.addEventListener('change', recalculateAll);

  if (weightSlider) {
    weightSlider.addEventListener('input', () => {
      weightInput.value = weightSlider.value;
      recalculateAll();
    });
  }
  if (repsSlider) {
    repsSlider.addEventListener('input', () => {
      repsInput.value = repsSlider.value;
      recalculateAll();
    });
  }

  // Initialize with initial values
  recalculateAll();

  // Save to PR button
  const savePrBtn = document.getElementById('btn-save-calc-pr');
  if (savePrBtn) {
    savePrBtn.addEventListener('click', saveCalculatedPR);
  }
}

function renderTrainingZones(oneRM, unit) {
  const container = document.getElementById('training-zones-container');
  if (!container) return;

  const zones = [
    { pct: 100, label: "Absolute 1RM", reps: "1 Rep", desc: "Max Effort / Testing", color: "#F43F5E", highlight: false },
    { pct: 95, label: "Peak Power", reps: "1 - 2 Reps", desc: "Neural recruitment", color: "#FB923C", highlight: false },
    { pct: 90, label: "Heavy Strength", reps: "3 - 4 Reps", desc: "Maximum Strength", color: "#E6D5B8", highlight: true },
    { pct: 85, label: "Strength Hypertrophy", reps: "5 - 6 Reps", desc: "Myofibrillar building", color: "#60A5FA", highlight: true },
    { pct: 80, label: "Hypertrophy", reps: "7 - 8 Reps", desc: "Optimal Muscle Growth", color: "#38BDF8", highlight: false },
    { pct: 75, label: "Work Capacity", reps: "9 - 10 Reps", desc: "Hypertrophy & Volume", color: "#2563EB", highlight: true },
    { pct: 70, label: "Muscular Endurance", reps: "11 - 12 Reps", desc: "Conditioning & Density", color: "#818CF8", highlight: false },
    { pct: 60, label: "Dynamic Speed", reps: "12 - 15 Reps", desc: "Explosive bar speed", color: "#A78BFA", highlight: false },
    { pct: 50, label: "Recovery / Deload", reps: "15 - 20 Reps", desc: "Technique & Blood Flow", color: "#CBD5E1", highlight: true }
  ];

  container.innerHTML = zones.map((z) => {
    const targetWeight = Math.round(oneRM * (z.pct / 100.0) * 10) / 10;
    return `
      <div class="gt-card p-4 rounded-xl border ${z.highlight ? 'border-[#2563EB]/60 bg-[#101C3D] shadow-md' : 'border-blue-900/30 bg-[#0A1128]'} transition hover:border-[#E6D5B8]/60">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="text-xs font-black px-2 py-0.5 rounded-full" style="background-color: ${z.color}25; color: ${z.color}; border: 1px solid ${z.color}50;">
              ${z.pct}%
            </span>
            <span class="text-sm font-bold text-white">${z.label}</span>
          </div>
          <div class="text-right">
            <span class="text-lg font-black text-white">${targetWeight}</span>
            <span class="text-xs text-gray-400 font-bold ml-0.5">${unit}</span>
          </div>
        </div>

        <div class="w-full bg-[#0A1128] border border-blue-900/30 rounded-full h-1.5 mb-2 overflow-hidden">
          <div class="h-full rounded-full" style="width: ${z.pct}%; background-color: ${z.color}"></div>
        </div>

        <div class="flex items-center justify-between text-xs text-gray-400">
          <span>Target: <strong class="text-gray-200">${z.reps}</strong></span>
          <span class="text-[11px] text-gray-400">${z.desc}</span>
        </div>
      </div>
    `;
  }).join('');
}

async function saveCalculatedPR() {
  const exercise = document.getElementById('calc-save-exercise')?.value;
  const weight = parseFloat(document.getElementById('calc-weight')?.value || 0);
  const reps = parseInt(document.getElementById('calc-reps')?.value || 0);

  if (!exercise) {
    showToast('Please pick an exercise to save.', 'error');
    return;
  }
  if (weight <= 0 || reps <= 0) {
    showToast('Please enter valid weight and reps.', 'error');
    return;
  }

  const est1RM = reps === 1 ? weight : Math.round(weight * (1.0 + reps / 30.0) * 10) / 10;
  const today = new Date().toISOString().split('T')[0];

  try {
    const res = await fetch('/api/prs/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exercise_name: exercise,
        weight: weight,
        reps: reps,
        estimated_1rm: est1RM,
        date: today
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Saved ${exercise} PR: ${est1RM} 1RM!`, 'pr', 'RECORD SAVED');
    } else {
      showToast(data.error || 'Failed to save record.', 'error');
    }
  } catch (err) {
    showToast('Network error while saving PR.', 'error');
  }
}

// -------------------------------------------------------------
// Interactive Barbell Plate Loader Engine (Offline Ready)
// -------------------------------------------------------------
function initPlateLoader() {
  const targetInput = document.getElementById('plate-target-weight');
  const slider = document.getElementById('plate-weight-slider');
  const barSelect = document.getElementById('plate-bar-weight');
  const unitSelect = document.getElementById('calc-unit');
  const zoneBtns = document.querySelectorAll('.btn-zone-preset');

  if (!targetInput) return;

  function updatePlates() {
    const unit = unitSelect ? unitSelect.value : 'kg';
    const isLbs = unit === 'lbs';
    let target = parseFloat(targetInput.value || 0);
    const bar = parseFloat(barSelect?.value || (isLbs ? 45 : 20));

    // Update labels
    document.querySelectorAll('.plate-unit-label').forEach(el => el.textContent = unit);

    if (slider && slider.value != target) {
      slider.value = target;
    }

    const breakdown = calculatePlateStack(target, bar, unit);
    renderPlateVisuals(breakdown, unit);
  }

  targetInput.addEventListener('input', updatePlates);
  if (slider) {
    slider.addEventListener('input', () => {
      targetInput.value = slider.value;
      updatePlates();
    });
  }
  barSelect?.addEventListener('change', updatePlates);
  unitSelect?.addEventListener('change', () => {
    const isLbs = unitSelect.value === 'lbs';
    if (barSelect) {
      barSelect.value = isLbs ? '45' : '20';
    }
    updatePlates();
  });

  // Zone Presets (70%, 80%, 85%, 90%, 100% of current 1RM)
  zoneBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const pct = parseFloat(btn.getAttribute('data-pct') || 100);
      const oneRMText = document.getElementById('display-1rm-val')?.textContent || '100';
      const oneRM = parseFloat(oneRMText) || 100;
      let calculatedTarget = Math.round((oneRM * (pct / 100.0)) * 2) / 2;
      if (calculatedTarget < 20) calculatedTarget = 20;

      targetInput.value = calculatedTarget;
      if (slider) slider.value = calculatedTarget;
      updatePlates();
      showToast(`Loaded ${pct}% 1RM: ${calculatedTarget} ${unitSelect ? unitSelect.value : 'kg'}`, 'info');
    });
  });

  updatePlates();
}

function calculatePlateStack(target, bar, unit) {
  const isLbs = unit === 'lbs';
  const plates = isLbs
    ? [
        { w: 45, color: '#EF4444', height: 160, width: 22, text: '#FFF' },
        { w: 35, color: '#0066FF', height: 145, width: 20, text: '#FFF' },
        { w: 25, color: '#F59E0B', height: 130, width: 18, text: '#000' },
        { w: 10, color: '#10B981', height: 110, width: 15, text: '#FFF' },
        { w: 5, color: '#F8FAFC', height: 95, width: 13, text: '#000', border: '#CBD5E1' },
        { w: 2.5, color: '#1E293B', height: 80, width: 11, text: '#FFF' }
      ]
    : [
        { w: 25, color: '#EF4444', height: 160, width: 22, text: '#FFF' },
        { w: 20, color: '#0066FF', height: 150, width: 20, text: '#FFF' },
        { w: 15, color: '#F59E0B', height: 135, width: 18, text: '#000' },
        { w: 10, color: '#10B981', height: 115, width: 15, text: '#FFF' },
        { w: 5, color: '#F8FAFC', height: 95, width: 13, text: '#000', border: '#CBD5E1' },
        { w: 2.5, color: '#1E293B', height: 80, width: 11, text: '#FFF' },
        { w: 1.25, color: '#94A3B8', height: 68, width: 9, text: '#000' }
      ];

  if (target <= bar) {
    return {
      target: target,
      bar: bar,
      sideWeight: 0,
      totalLoaded: bar,
      platesPerSide: [],
      counts: {},
      remainder: 0
    };
  }

  const weightNeeded = target - bar;
  const perSide = weightNeeded / 2.0;
  let rem = perSide;
  const platesPerSide = [];
  const counts = {};

  for (const p of plates) {
    const c = Math.floor(rem / p.w);
    if (c > 0) {
      counts[p.w] = c;
      for (let i = 0; i < c; i++) {
        platesPerSide.push(p);
      }
      rem = Math.round((rem - (c * p.w)) * 100) / 100;
    }
  }

  const loadedSide = platesPerSide.reduce((sum, p) => sum + p.w, 0);
  const totalLoaded = bar + (loadedSide * 2);

  return {
    target: target,
    bar: bar,
    sideWeight: perSide,
    totalLoaded: totalLoaded,
    platesPerSide: platesPerSide,
    counts: counts,
    remainder: rem
  };
}

function getPlateColor(weight, unit) {
  if (unit === 'lbs') {
    if (weight >= 45) return '#EF4444';
    if (weight >= 35) return '#0066FF';
    if (weight >= 25) return '#F59E0B';
    if (weight >= 10) return '#10B981';
    if (weight >= 5) return '#E2E8F0';
    return '#1E293B';
  } else {
    if (weight >= 25) return '#EF4444';
    if (weight >= 20) return '#0066FF';
    if (weight >= 15) return '#F59E0B';
    if (weight >= 10) return '#10B981';
    if (weight >= 5) return '#E2E8F0';
    if (weight >= 2.5) return '#1E293B';
    return '#94A3B8';
  }
}

function renderPlateVisuals(breakdown, unit) {
  const totalElem = document.getElementById('plate-total-loaded');
  const perSideElem = document.getElementById('plate-per-side-display');
  const stackElem = document.getElementById('visual-plates-stack');
  const chipsElem = document.getElementById('plates-breakdown-chips');
  const remainderBadge = document.getElementById('plate-remainder-badge');

  if (totalElem) totalElem.textContent = breakdown.totalLoaded;
  if (perSideElem) perSideElem.textContent = breakdown.sideWeight.toFixed(1);

  if (remainderBadge) {
    if (breakdown.remainder > 0) {
      remainderBadge.textContent = `Unloaded: ${breakdown.remainder * 2} ${unit} (needs smaller micro-plates)`;
      remainderBadge.className = "text-[11px] font-semibold text-amber-500";
    } else {
      remainderBadge.textContent = "Exact match";
      remainderBadge.className = "text-[11px] font-semibold text-emerald-500";
    }
  }

  // Render Visual Diagram Plates
  if (stackElem) {
    if (breakdown.platesPerSide.length === 0) {
      stackElem.innerHTML = `<span class="text-xs text-slate-400 italic px-3">No plates loaded (Bar only)</span>`;
    } else {
      stackElem.innerHTML = breakdown.platesPerSide.map((p) => {
        return `
          <div class="relative flex items-center justify-center rounded-sm shadow-md transition-all duration-200 hover:scale-105"
               style="height: ${p.height}px; width: ${p.width}px; background-color: ${p.color}; border: 1.5px solid ${p.border || '#1E293B'};"
               title="${p.w} ${unit} Plate">
            <span class="text-[9px] font-black tracking-tighter select-none rotate-90"
                  style="color: ${p.text};">
              ${p.w}
            </span>
          </div>
        `;
      }).join('');
    }
  }

  // Render Chips breakdown
  if (chipsElem) {
    const keys = Object.keys(breakdown.counts).sort((a, b) => parseFloat(b) - parseFloat(a));
    if (keys.length === 0) {
      chipsElem.innerHTML = `<span class="text-xs text-slate-400">Empty bar (no plates required).</span>`;
    } else {
      chipsElem.innerHTML = keys.map(k => {
        const count = breakdown.counts[k];
        return `
          <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white dark:bg-[#101C3D] border border-slate-200 dark:border-blue-900/40 shadow-2xs text-xs font-bold text-slate-800 dark:text-slate-200">
            <span class="w-3 h-3 rounded-full inline-block" style="background-color: ${getPlateColor(parseFloat(k), unit)};"></span>
            <span>${count} × <strong class="text-[#0066FF] dark:text-blue-400">${k} ${unit}</strong></span>
            <span class="text-[10px] text-slate-400">(${count * 2} total)</span>
          </div>
        `;
      }).join('');
    }
  }
}

document.addEventListener('DOMContentLoaded', initOneRepMaxCalculator);
