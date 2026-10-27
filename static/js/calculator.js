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
    { pct: 100, label: "Absolute 1RM", reps: "1 Rep", desc: "Max Effort / Testing", color: "#FF3366", highlight: false },
    { pct: 95, label: "Peak Power", reps: "1 - 2 Reps", desc: "Neural recruitment", color: "#FF5722", highlight: false },
    { pct: 90, label: "Heavy Strength", reps: "3 - 4 Reps", desc: "Maximum Strength", color: "#FFD700", highlight: true }, // Requested in brief
    { pct: 85, label: "Strength Hypertrophy", reps: "5 - 6 Reps", desc: "Myofibrillar building", color: "#CCFF00", highlight: true }, // Requested in brief
    { pct: 80, label: "Hypertrophy", reps: "7 - 8 Reps", desc: "Optimal Muscle Growth", color: "#00E5FF", highlight: false },
    { pct: 75, label: "Work Capacity", reps: "9 - 10 Reps", desc: "Hypertrophy & Volume", color: "#00FF88", highlight: true }, // Requested in brief
    { pct: 70, label: "Muscular Endurance", reps: "11 - 12 Reps", desc: "Conditioning & Density", color: "#76FF03", highlight: false },
    { pct: 60, label: "Dynamic Speed", reps: "12 - 15 Reps", desc: "Explosive bar speed", color: "#64B5F6", highlight: false },
    { pct: 50, label: "Recovery / Deload", reps: "15 - 20 Reps", desc: "Technique & Blood Flow", color: "#B0BEC5", highlight: true } // Requested in brief
  ];

  container.innerHTML = zones.map((z) => {
    const targetWeight = Math.round(oneRM * (z.pct / 100.0) * 10) / 10;
    return `
      <div class="gt-card p-4 border ${z.highlight ? 'border-[#CCFF00]/50 bg-[#1E1E1E]' : 'border-gray-800 bg-[#171717]'} transition hover:border-[#CCFF00]/60">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="text-xs font-black px-2 py-0.5 rounded-full" style="background-color: ${z.color}20; color: ${z.color}; border: 1px solid ${z.color}40;">
              ${z.pct}%
            </span>
            <span class="text-sm font-bold text-white">${z.label}</span>
          </div>
          <div class="text-right">
            <span class="text-lg font-black text-white">${targetWeight}</span>
            <span class="text-xs text-gray-400 font-bold ml-0.5">${unit}</span>
          </div>
        </div>

        <div class="w-full bg-gray-800 rounded-full h-1.5 mb-2 overflow-hidden">
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

document.addEventListener('DOMContentLoaded', initOneRepMaxCalculator);
