/**
 * Gym Tracker Pro - MyFitnessPal-Style Nutrition & Macro Engine
 * Itemized categorized meal tracking, dynamic date switching,
 * Calorie remaining calculation (Goal - Food + Exercise = Remaining),
 * Server-side AI Vision food scanner, and Barcode scanner via Open Food Facts API.
 */

let activeNutritionDate = new Date().toISOString().split('T')[0];
let currentScannedData = null;
let currentBarcodeData = null;
let html5QrCodeScanner = null;
let isBarcodeCameraRunning = false;

// -------------------------------------------------------------
// 1. Initializer & Top Date Bar Navigation
// -------------------------------------------------------------
function initNutritionTracker() {
  const mealForm = document.getElementById('nutrition-log-form');
  const dateInput = document.getElementById('nutrition-active-date');
  const prevDayBtn = document.getElementById('btn-prev-day');
  const nextDayBtn = document.getElementById('btn-next-day');
  const todayBtn = document.getElementById('btn-today');
  const yesterdayBtn = document.getElementById('btn-yesterday');
  const tomorrowBtn = document.getElementById('btn-tomorrow');

  // URL query param support: ?date=YYYY-MM-DD
  const urlParams = new URLSearchParams(window.location.search);
  const paramDate = urlParams.get('date');
  if (paramDate) {
    activeNutritionDate = paramDate;
  } else if (dateInput && dateInput.value) {
    activeNutritionDate = dateInput.value;
  }

  if (dateInput) {
    dateInput.value = activeNutritionDate;
    dateInput.addEventListener('change', () => {
      if (dateInput.value) {
        setNutritionDate(dateInput.value);
      }
    });
  }

  prevDayBtn?.addEventListener('click', () => changeNutritionOffset(-1));
  nextDayBtn?.addEventListener('click', () => changeNutritionOffset(1));
  todayBtn?.addEventListener('click', () => {
    const today = new Date().toISOString().split('T')[0];
    setNutritionDate(today);
  });
  yesterdayBtn?.addEventListener('click', () => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    setNutritionDate(d.toISOString().split('T')[0]);
  });
  tomorrowBtn?.addEventListener('click', () => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    setNutritionDate(d.toISOString().split('T')[0]);
  });

  if (mealForm) {
    mealForm.addEventListener('submit', handleManualMealSubmit);
  }

  updateDisplayDateHeader(activeNutritionDate);
  initAiCameraScanner();
  initBarcodeScanner();
}

function changeNutritionOffset(deltaDays) {
  const current = new Date(activeNutritionDate + 'T00:00:00');
  current.setDate(current.getDate() + deltaDays);
  const yr = current.getFullYear();
  const mo = String(current.getMonth() + 1).padStart(2, '0');
  const da = String(current.getDate()).padStart(2, '0');
  setNutritionDate(`${yr}-${mo}-${da}`);
}

function setNutritionDate(dateStr) {
  activeNutritionDate = dateStr;
  const dateInput = document.getElementById('nutrition-active-date');
  if (dateInput) dateInput.value = dateStr;
  updateDisplayDateHeader(dateStr);

  // Update URL without full page reload
  const newUrl = window.location.pathname + '?date=' + encodeURIComponent(dateStr);
  window.history.pushState({ path: newUrl }, '', newUrl);

  fetchNutritionForDate(dateStr);
}

function updateDisplayDateHeader(dateStr) {
  const displayElem = document.getElementById('display-nutrition-date');
  const badgeElem = document.getElementById('nutrition-today-badge');
  const todayStr = new Date().toISOString().split('T')[0];

  if (displayElem) displayElem.textContent = dateStr;
  if (badgeElem) {
    if (dateStr === todayStr) {
      badgeElem.classList.remove('hidden');
    } else {
      badgeElem.classList.add('hidden');
    }
  }
}

// -------------------------------------------------------------
// 2. Data Fetching & MyFitnessPal Calorie Calculation
// -------------------------------------------------------------
async function fetchNutritionForDate(dateStr) {
  try {
    const res = await fetch(`/api/nutrition?date=${encodeURIComponent(dateStr)}`);
    const data = await res.json();
    if (res.ok && data.success) {
      updateNutritionUI(data);
    }
  } catch (err) {
    console.error('Error fetching nutrition for date:', err);
  }
}

function updateNutritionUI(data) {
  const totals = data.totals || { calories: 0, protein: 0, carbs: 0, fat: 0 };
  const targets = data.targets || { calories: 2000, protein: 150, carbs: 200, fat: 65 };
  const steps = data.steps || { calories_burned: 0, steps: 0 };

  const goal = Math.round(targets.calories);
  const food = Math.round(totals.calories);
  const exercise = Math.round(steps.calories_burned || 0);
  const remaining = goal - food + exercise;

  // 1. Top Equation Cards (Goal - Food + Exercise = Remaining)
  const calRemainingElem = document.getElementById('cal-remaining');
  const calRemainingSubElem = document.getElementById('cal-remaining-sub');
  const calTargetElem = document.getElementById('cal-target');
  const calConsumedElem = document.getElementById('cal-consumed');
  const calExerciseElem = document.getElementById('cal-exercise');
  const calExerciseSubtext = document.getElementById('cal-exercise-subtext');

  if (calRemainingElem) {
    calRemainingElem.textContent = remaining.toLocaleString();
    calRemainingElem.className = `text-4xl sm:text-5xl font-black tracking-tight ${remaining < 0 ? 'text-rose-600' : 'text-[#0066FF]'}`;
  }
  if (calRemainingSubElem) calRemainingSubElem.textContent = remaining.toLocaleString();
  if (calTargetElem) calTargetElem.textContent = goal.toLocaleString();
  if (calConsumedElem) calConsumedElem.textContent = food.toLocaleString();
  if (calExerciseElem) calExerciseElem.textContent = exercise.toLocaleString();
  if (calExerciseSubtext && steps.steps !== undefined) {
    calExerciseSubtext.textContent = `${(steps.steps || 0).toLocaleString()} steps logged`;
  }

  // Progress Bar
  const calBarElem = document.getElementById('cal-progress-bar');
  const calProgressLabel = document.getElementById('cal-progress-label');
  const calPct = Math.round((food / Math.max(1, goal)) * 100);
  if (calBarElem) {
    calBarElem.style.width = `${Math.min(100, calPct)}%`;
    calBarElem.className = `h-full rounded-full transition-all duration-700 ${calPct > 100 ? 'bg-red-500' : 'bg-gradient-to-r from-[#0066FF] to-[#1877F2]'}`;
  }
  if (calProgressLabel) {
    calProgressLabel.textContent = `${calPct}% of base goal`;
  }

  // 2. Macronutrient Indicators
  // Carbohydrates
  const cVal = Math.round(totals.carbs);
  const cTarget = Math.round(targets.carbs);
  const cLeft = Math.max(0, cTarget - cVal);
  const cPct = Math.min(100, Math.round((cVal / Math.max(1, cTarget)) * 100));
  setText('carbs-val', cVal);
  setText('carbs-target', cTarget);
  setText('carbs-left', `${cLeft}g left`);
  setText('carbs-pct', `${cPct}%`);
  setText('carbs-cals', `${cVal * 4} kcal`);
  setBarWidth('carbs-progress-bar', cPct);

  // Protein
  const pVal = Math.round(totals.protein);
  const pTarget = Math.round(targets.protein);
  const pLeft = Math.max(0, pTarget - pVal);
  const pPct = Math.min(100, Math.round((pVal / Math.max(1, pTarget)) * 100));
  setText('protein-val', pVal);
  setText('protein-target', pTarget);
  setText('protein-left', `${pLeft}g left`);
  setText('protein-pct', `${pPct}%`);
  setText('protein-cals', `${pVal * 4} kcal`);
  setBarWidth('protein-progress-bar', pPct);

  // Fat
  const fVal = Math.round(totals.fat);
  const fTarget = Math.round(targets.fat);
  const fLeft = Math.max(0, fTarget - fVal);
  const fPct = Math.min(100, Math.round((fVal / Math.max(1, fTarget)) * 100));
  setText('fat-val', fVal);
  setText('fat-target', fTarget);
  setText('fat-left', `${fLeft}g left`);
  setText('fat-pct', `${fPct}%`);
  setText('fat-cals', `${fVal * 9} kcal`);
  setBarWidth('fat-progress-bar', fPct);

  // 3. Update Water Intake
  if (data.water) {
    updateWaterUI(data.water);
  }

  // 4. Update Macro Energy Percentages
  if (data.macro_percentages) {
    const mp = data.macro_percentages;
    setBarWidth('macro-ratio-protein', mp.protein);
    setBarWidth('macro-ratio-carbs', mp.carbs);
    setBarWidth('macro-ratio-fat', mp.fat);
    setText('legend-pct-protein', `${mp.protein}%`);
    setText('legend-pct-carbs', `${mp.carbs}%`);
    setText('legend-pct-fat', `${mp.fat}%`);
  }

  // 5. Render Categorized Meal Sections
  renderCategorizedMealSections(data.grouped || {});
}

// -------------------------------------------------------------
// 2.1 Water Consumption Hydration Engine
// -------------------------------------------------------------
async function quickAddWater(deltaMl) {
  try {
    const res = await fetch('/api/nutrition/water', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: activeNutritionDate,
        delta_ml: deltaMl
      })
    });
    const data = await res.json();
    if (res.ok && data.success && data.water) {
      updateWaterUI(data.water);
      if (typeof showToast === 'function') {
        if (deltaMl > 0) {
          showToast(`+${deltaMl} ml logged! Stay hydrated 💧`, 'success');
        } else {
          showToast(`${deltaMl} ml adjusted.`, 'info');
        }
      }
    }
  } catch (err) {
    if (typeof showToast === 'function') showToast('Failed to update water intake.', 'error');
  }
}

async function resetWater() {
  if (!confirm("Reset today's logged water intake to 0 ml?")) return;
  try {
    const res = await fetch('/api/nutrition/water', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: activeNutritionDate,
        amount_ml: 0
      })
    });
    const data = await res.json();
    if (res.ok && data.success && data.water) {
      updateWaterUI(data.water);
      if (typeof showToast === 'function') showToast('Water intake reset to 0 ml.', 'info');
    }
  } catch (err) {
    if (typeof showToast === 'function') showToast('Failed to reset water.', 'error');
  }
}

function updateWaterUI(water) {
  if (!water) return;
  const amt = water.amount_ml || 0;
  const goal = water.goal_ml || 3000;
  const pct = Math.min(100, Math.round((amt / Math.max(1, goal)) * 100));
  const cups = (amt / 250.0).toFixed(1);
  const goalCups = (goal / 250.0).toFixed(1);

  setText('water-val', amt.toLocaleString());
  setText('water-target', goal.toLocaleString());
  setText('water-pct-badge', `${pct}%`);
  setText('water-cups-label', `(${cups} / ${goalCups} cups)`);
  setBarWidth('water-progress-bar', pct);

  const remLabel = document.getElementById('water-remaining-label');
  if (remLabel) {
    if (amt >= goal) {
      remLabel.textContent = '🎉 Daily Goal Reached!';
    } else {
      remLabel.textContent = `${(goal - amt).toLocaleString()} ml remaining`;
    }
  }
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setBarWidth(id, pct) {
  const el = document.getElementById(id);
  if (el) el.style.width = `${pct}%`;
}

// -------------------------------------------------------------
// 3. Categorized Meal Sections Display & Item Removal
// -------------------------------------------------------------
function renderCategorizedMealSections(grouped) {
  const categories = [
    { title: "Breakfast", icon: "🍳", key: "Breakfast" },
    { title: "Lunch", icon: "🥗", key: "Lunch" },
    { title: "Dinner", icon: "🥩", key: "Dinner" },
    { title: "Snacks", icon: "🍎", key: "Snack", extraKey: "Post-Workout" }
  ];

  const wrapper = document.getElementById('meal-sections-wrapper');
  if (!wrapper) return;

  let html = '';
  categories.forEach((cat) => {
    let items = grouped[cat.key] || [];
    if (cat.extraKey && grouped[cat.extraKey]) {
      items = items.concat(grouped[cat.extraKey]);
    }
    const catCals = items.reduce((sum, item) => sum + (parseFloat(item.calories) || 0), 0);

    html += `
      <div class="gt-card bg-white border border-[#E2E8F0] shadow-sm rounded-2xl overflow-hidden" data-category="${cat.key}">
        <!-- Section Header -->
        <div class="p-4 bg-slate-50 border-b border-[#E2E8F0] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <span class="text-2xl">${cat.icon}</span>
            <div>
              <h4 class="font-black text-slate-900 text-sm tracking-tight">${cat.title}</h4>
              <div class="text-[11px] text-slate-500 font-semibold">
                ${items.length} item${items.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          <!-- Subtotal & Actions -->
          <div class="flex items-center gap-3">
            <div class="text-right">
              <div class="text-sm font-black text-slate-900">
                ${Math.round(catCals)} <span class="text-xs font-semibold text-slate-500">kcal</span>
              </div>
            </div>
            <div class="flex items-center gap-1.5">
              <button type="button" onclick="openManualMealModal('${cat.key}')" class="px-2.5 py-1.5 rounded-lg text-xs font-bold bg-blue-50 hover:bg-blue-100 text-[#0066FF] border border-blue-200 transition flex items-center gap-1">
                <span>+</span> <span>Log Food</span>
              </button>
              <button type="button" onclick="openCameraModalForCategory('${cat.key}')" class="p-1.5 rounded-lg text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 border border-[#E2E8F0] transition" title="Scan with AI Camera">
                📸
              </button>
              <button type="button" onclick="openBarcodeModalForCategory('${cat.key}')" class="p-1.5 rounded-lg text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 border border-[#E2E8F0] transition" title="Scan Packaged Barcode">
                📷
              </button>
            </div>
          </div>
        </div>

        <!-- Items Table -->
        <div class="p-4">
          ${items.length === 0 ? `
            <div class="text-center py-4 text-xs text-slate-400 italic">
              No foods logged for ${cat.title} yet. Tap <strong>+ Log Food</strong> or scan your plate.
            </div>
          ` : `
            <div class="divide-y divide-[#E2E8F0]">
              ${items.map((item) => `
                <div class="flex items-center justify-between py-2.5 text-xs">
                  <div>
                    <div class="font-bold text-slate-800">${escapeHtml(item.food_name)}</div>
                    <div class="text-[11px] text-slate-500 mt-0.5">
                      P: <span class="text-blue-600 font-semibold">${item.protein}g</span> • 
                      C: <span class="text-amber-600 font-semibold">${item.carbs}g</span> • 
                      F: <span class="text-rose-600 font-semibold">${item.fat}g</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-3">
                    <span class="font-black text-slate-800">${Math.round(item.calories)} kcal</span>
                    <button onclick="deleteMealItem(${item.id})" class="text-slate-400 hover:text-red-500 p-1.5 rounded-lg hover:bg-red-50 transition" title="Delete entry">
                      ✕
                    </button>
                  </div>
                </div>
              `).join('')}
            </div>
          `}
        </div>
      </div>
    `;
  });

  wrapper.innerHTML = html;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

async function deleteMealItem(entryId) {
  try {
    const res = await fetch(`/api/nutrition/${entryId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast('Food entry removed.', 'success');
      fetchNutritionForDate(activeNutritionDate);
    } else {
      showToast(data.error || 'Failed to remove entry.', 'error');
    }
  } catch (err) {
    showToast('Error removing meal entry.', 'error');
  }
}

// -------------------------------------------------------------
// 4. Manual Food Log Modal
// -------------------------------------------------------------
function openManualMealModal(preferredCategory) {
  const modal = document.getElementById('manual-meal-modal');
  const typeSelect = document.getElementById('meal-type');
  if (preferredCategory && typeSelect) {
    typeSelect.value = preferredCategory;
  }
  if (modal) modal.classList.remove('hidden');
  document.getElementById('food-name')?.focus();
}

function closeManualMealModal() {
  const modal = document.getElementById('manual-meal-modal');
  if (modal) modal.classList.add('hidden');
}

async function handleManualMealSubmit(e) {
  e.preventDefault();
  const mealType = document.getElementById('meal-type').value;
  const foodName = document.getElementById('food-name').value.trim();
  const calories = parseFloat(document.getElementById('meal-calories').value || 0);
  const protein = parseFloat(document.getElementById('meal-protein').value || 0);
  const carbs = parseFloat(document.getElementById('meal-carbs').value || 0);
  const fat = parseFloat(document.getElementById('meal-fat').value || 0);

  if (!foodName) {
    showToast('Please enter a food or meal name.', 'error');
    return;
  }

  try {
    const res = await fetch('/api/nutrition/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: activeNutritionDate,
        meal_type: mealType,
        food_name: foodName,
        calories: calories,
        protein: protein,
        carbs: carbs,
        fat: fat
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Logged "${foodName}" (${calories} kcal)`, 'success');
      document.getElementById('food-name').value = '';
      document.getElementById('meal-calories').value = '';
      document.getElementById('meal-protein').value = '';
      document.getElementById('meal-carbs').value = '';
      document.getElementById('meal-fat').value = '';
      closeManualMealModal();
      fetchNutritionForDate(activeNutritionDate);
    } else {
      showToast(data.error || 'Failed to log meal.', 'error');
    }
  } catch (err) {
    showToast('Network error while logging food.', 'error');
  }
}

// -------------------------------------------------------------
// 5. Server-Side AI Food Camera Scanner (No client API key prompts!)
// -------------------------------------------------------------
function openCameraModalForCategory(catKey) {
  const modal = document.getElementById('ai-camera-modal');
  const typeSelect = document.getElementById('camera-meal-type');
  if (catKey && typeSelect) {
    typeSelect.value = catKey;
  }
  if (modal) {
    modal.classList.remove('hidden');
    resetCameraState();
  }
}

function initAiCameraScanner() {
  const openBtn = document.getElementById('btn-open-camera-modal');
  const closeBtn = document.getElementById('btn-close-camera-modal');
  const modal = document.getElementById('ai-camera-modal');
  const uploadZone = document.getElementById('camera-upload-zone');
  const fileInput = document.getElementById('camera-file-input');
  const previewZone = document.getElementById('camera-preview-zone');
  const imagePreview = document.getElementById('scanned-image-preview');
  const scanningIndicator = document.getElementById('scanning-indicator');
  const resultsZone = document.getElementById('scan-results-zone');
  const retakeBtn = document.getElementById('btn-retake-camera');
  const confirmBtn = document.getElementById('btn-confirm-scanned-meal');
  const errorBanner = document.getElementById('camera-error-banner');
  const errorMessage = document.getElementById('camera-error-message');
  const retakeErrorBtn = document.getElementById('btn-camera-retake-error');

  if (!modal) return;

  openBtn?.addEventListener('click', () => {
    modal.classList.remove('hidden');
    resetCameraState();
  });

  closeBtn?.addEventListener('click', () => {
    modal.classList.add('hidden');
    resetCameraState();
  });

  uploadZone?.addEventListener('click', () => {
    fileInput?.click();
  });

  retakeBtn?.addEventListener('click', () => {
    resetCameraState();
    fileInput?.click();
  });

  retakeErrorBtn?.addEventListener('click', () => {
    resetCameraState();
    fileInput?.click();
  });

  fileInput?.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show image preview immediately
    const reader = new FileReader();
    reader.onload = async (evt) => {
      imagePreview.src = evt.target.result;
      uploadZone?.classList.add('hidden');
      previewZone?.classList.remove('hidden');
      scanningIndicator?.classList.remove('hidden');
      resultsZone?.classList.add('hidden');
      errorBanner?.classList.add('hidden');

      const formData = new FormData();
      formData.append('meal_image', file);

      try {
        const res = await fetch('/api/nutrition/scan-meal', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        scanningIndicator?.classList.add('hidden');

        if (res.ok && data.success && data.analysis) {
          currentScannedData = data.analysis;
          renderScanResults(data.analysis);
          resultsZone?.classList.remove('hidden');
          errorBanner?.classList.add('hidden');
        } else if (data.is_pro_required) {
          if (errorBanner && errorMessage) {
            errorMessage.textContent = data.error;
            errorBanner.classList.remove('hidden');
          }
          showToast(data.error, 'warning');
          setTimeout(() => { window.location.href = '/subscription?required=camera'; }, 2500);
        } else {
          // Rejection or failure
          if (errorBanner && errorMessage) {
            errorMessage.textContent = data.error || 'Could not analyze food image. Please point at a real meal or snack.';
            errorBanner.classList.remove('hidden');
          } else {
            showToast(data.error || 'Could not process image.', 'error');
          }
        }
      } catch (err) {
        scanningIndicator?.classList.add('hidden');
        showToast('Network error while analyzing food photo.', 'error');
        resetCameraState();
      }
    };
    reader.readAsDataURL(file);
  });

  confirmBtn?.addEventListener('click', async () => {
    if (!currentScannedData) return;
    const mealType = document.getElementById('camera-meal-type')?.value || 'Lunch';

    try {
      const res = await fetch('/api/nutrition/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: activeNutritionDate,
          meal_type: mealType,
          food_name: currentScannedData.food_name,
          calories: currentScannedData.calories,
          protein: currentScannedData.protein,
          carbs: currentScannedData.carbs,
          fat: currentScannedData.fat
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`Logged "${currentScannedData.food_name}" (${currentScannedData.calories} kcal) to ${mealType}!`, 'success');
        modal.classList.add('hidden');
        resetCameraState();
        fetchNutritionForDate(activeNutritionDate);
      } else {
        showToast(data.error || 'Failed to save meal.', 'error');
      }
    } catch (err) {
      showToast('Error saving scanned meal.', 'error');
    }
  });
}

function resetCameraState() {
  const fileInput = document.getElementById('camera-file-input');
  if (fileInput) fileInput.value = '';
  currentScannedData = null;
  document.getElementById('camera-upload-zone')?.classList.remove('hidden');
  document.getElementById('camera-preview-zone')?.classList.add('hidden');
  document.getElementById('scan-results-zone')?.classList.add('hidden');
  document.getElementById('scanning-indicator')?.classList.add('hidden');
  document.getElementById('camera-error-banner')?.classList.add('hidden');
}

function renderScanResults(analysis) {
  setText('detected-food-name', analysis.food_name);
  setText('detected-food-desc', `${analysis.description || ''} (${analysis.portion_size || '~380g'})`);
  setText('detected-cals', Math.round(analysis.calories));
  setText('detected-protein', `${Math.round(analysis.protein)}g`);
  setText('detected-carbs', `${Math.round(analysis.carbs)}g`);
  setText('detected-fat', `${Math.round(analysis.fat)}g`);

  const breakdownContainer = document.getElementById('detected-breakdown-list');
  if (breakdownContainer && analysis.breakdown) {
    breakdownContainer.innerHTML = analysis.breakdown.map((item) => `
      <div class="flex items-center justify-between p-2 rounded-lg bg-white border border-[#E2E8F0] shadow-2xs">
        <span class="font-semibold text-slate-800">${escapeHtml(item.item)} (${escapeHtml(item.portion || '')})</span>
        <span class="font-bold text-slate-900">${Math.round(item.calories)} kcal • P: ${Math.round(item.protein)}g</span>
      </div>
    `).join('');
  }
}

// -------------------------------------------------------------
// 6. In-Browser Barcode Scanner (html5-qrcode, Open Food Facts & Local Custom DB + Gemini OCR)
// -------------------------------------------------------------
let activeScannedBarcode = null;

function openBarcodeModalForCategory(catKey) {
  const modal = document.getElementById('barcode-scanner-modal');
  const typeSelect = document.getElementById('barcode-meal-type');
  if (catKey && typeSelect) {
    typeSelect.value = catKey;
  }
  if (modal) {
    modal.classList.remove('hidden');
    resetBarcodeState();
  }
}

function initBarcodeScanner() {
  const openBtn = document.getElementById('btn-open-barcode-modal');
  const closeBtn = document.getElementById('btn-close-barcode-modal');
  const modal = document.getElementById('barcode-scanner-modal');
  const toggleCameraBtn = document.getElementById('btn-toggle-barcode-camera');
  const lookupBtn = document.getElementById('btn-lookup-barcode');
  const manualInput = document.getElementById('manual-barcode-input');
  const confirmBtn = document.getElementById('btn-confirm-barcode-item');

  // New Product Modal Elements
  const newProductModal = document.getElementById('new-product-modal');
  const closeNewProductBtn = document.getElementById('btn-close-new-product-modal');
  const cancelNewProductBtn = document.getElementById('btn-cancel-new-product');
  const snapNutritionBtn = document.getElementById('btn-snap-nutrition-label');
  const ocrFileInput = document.getElementById('barcode-ocr-file-input');
  const saveCustomBarcodeBtn = document.getElementById('btn-save-custom-barcode');

  if (!modal) return;

  openBtn?.addEventListener('click', () => {
    modal.classList.remove('hidden');
    resetBarcodeState();
  });

  closeBtn?.addEventListener('click', () => {
    stopBarcodeCamera();
    modal.classList.add('hidden');
    resetBarcodeState();
  });

  toggleCameraBtn?.addEventListener('click', () => {
    if (isBarcodeCameraRunning) {
      stopBarcodeCamera();
    } else {
      startBarcodeCamera();
    }
  });

  lookupBtn?.addEventListener('click', () => {
    const val = manualInput?.value?.trim();
    if (val) {
      queryBarcodeProduct(val);
    } else {
      showToast('Please type a numeric barcode (UPC / EAN).', 'error');
    }
  });

  manualInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      lookupBtn?.click();
    }
  });

  confirmBtn?.addEventListener('click', async () => {
    if (!currentBarcodeData) return;
    const mealType = document.getElementById('barcode-meal-type')?.value || 'Snack';

    try {
      const res = await fetch('/api/nutrition/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: activeNutritionDate,
          meal_type: mealType,
          food_name: currentBarcodeData.food_name,
          calories: currentBarcodeData.calories,
          protein: currentBarcodeData.protein,
          carbs: currentBarcodeData.carbs,
          fat: currentBarcodeData.fat
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`Logged "${currentBarcodeData.food_name}" (${currentBarcodeData.calories} kcal) to ${mealType}!`, 'success');
        stopBarcodeCamera();
        modal.classList.add('hidden');
        resetBarcodeState();
        fetchNutritionForDate(activeNutritionDate);
      } else {
        showToast(data.error || 'Failed to log scanned barcode item.', 'error');
      }
    } catch (err) {
      showToast('Error saving scanned food item.', 'error');
    }
  });

  // Wire New Product Modal handlers
  closeNewProductBtn?.addEventListener('click', () => {
    newProductModal?.classList.add('hidden');
  });

  cancelNewProductBtn?.addEventListener('click', () => {
    newProductModal?.classList.add('hidden');
  });

  snapNutritionBtn?.addEventListener('click', () => {
    ocrFileInput?.click();
  });

  ocrFileInput?.addEventListener('change', async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    const loadingElem = document.getElementById('barcode-ocr-loading');
    if (loadingElem) loadingElem.classList.remove('hidden');

    const formData = new FormData();
    formData.append('barcode', activeScannedBarcode || '000000000000');
    formData.append('image', file);

    try {
      showToast('Analyzing nutrition label photo with Gemini Vision OCR...', 'info');
      const res = await fetch('/api/barcodes/ocr', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (loadingElem) loadingElem.classList.add('hidden');

      if (res.ok && data.success && data.product) {
        const prod = data.product;
        const nameInput = document.getElementById('new-barcode-name');
        const brandInput = document.getElementById('new-barcode-brand');
        const servingInput = document.getElementById('new-barcode-serving');
        const calsInput = document.getElementById('new-barcode-cals');
        const proteinInput = document.getElementById('new-barcode-protein');
        const carbsInput = document.getElementById('new-barcode-carbs');
        const fatInput = document.getElementById('new-barcode-fat');

        if (nameInput) nameInput.value = prod.food_name || '';
        if (brandInput) brandInput.value = prod.brand || '';
        if (servingInput) servingInput.value = prod.serving_size || '100g';
        if (calsInput) calsInput.value = prod.calories || 0;
        if (proteinInput) proteinInput.value = prod.protein || 0;
        if (carbsInput) carbsInput.value = prod.carbs || 0;
        if (fatInput) fatInput.value = prod.fat || 0;

        showToast('Nutrition table scanned and parsed successfully!', 'success');
      } else {
        showToast(data.error || 'Could not parse nutrition facts from photo. You can fill the fields manually.', 'warning');
      }
    } catch (err) {
      if (loadingElem) loadingElem.classList.add('hidden');
      showToast('OCR processing failed. You can type in the numbers manually.', 'error');
    }
  });

  saveCustomBarcodeBtn?.addEventListener('click', async () => {
    const barcode = activeScannedBarcode || document.getElementById('manual-barcode-input')?.value?.trim();
    const name = document.getElementById('new-barcode-name')?.value?.trim();
    const brand = document.getElementById('new-barcode-brand')?.value?.trim() || 'Custom Item';
    const serving = document.getElementById('new-barcode-serving')?.value?.trim() || '100g';
    const calories = parseFloat(document.getElementById('new-barcode-cals')?.value || 0);
    const protein = parseFloat(document.getElementById('new-barcode-protein')?.value || 0);
    const carbs = parseFloat(document.getElementById('new-barcode-carbs')?.value || 0);
    const fat = parseFloat(document.getElementById('new-barcode-fat')?.value || 0);
    const mealType = document.getElementById('barcode-meal-type')?.value || 'Snack';

    if (!name) {
      showToast('Please provide a product name.', 'error');
      return;
    }

    try {
      // 1. Save permanently to database
      await fetch('/api/barcodes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          barcode: barcode,
          food_name: name,
          brand: brand,
          serving_size: serving,
          calories: calories,
          protein: protein,
          carbs: carbs,
          fat: fat,
          source: 'user_created'
        })
      });

      // 2. Log item to today's meal
      const logRes = await fetch('/api/nutrition/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: activeNutritionDate,
          meal_type: mealType,
          food_name: `${name} (${brand})`,
          calories: calories,
          protein: protein,
          carbs: carbs,
          fat: fat
        })
      });

      const logData = await logRes.json();
      if (logRes.ok && logData.success) {
        showToast(`Saved "${name}" and logged ${calories} kcal to ${mealType}!`, 'success');
        newProductModal?.classList.add('hidden');
        modal.classList.add('hidden');
        resetBarcodeState();
        fetchNutritionForDate(activeNutritionDate);
      } else {
        showToast(logData.error || 'Saved to barcode catalog, but could not log to today.', 'warning');
      }
    } catch (err) {
      showToast('Error saving custom barcode item.', 'error');
    }
  });
}

function startBarcodeCamera() {
  if (typeof Html5Qrcode === 'undefined') {
    showToast('Barcode scanner engine loading, please try again in a moment.', 'info');
    return;
  }

  const container = document.getElementById('barcode-interactive');
  const statusElem = document.getElementById('barcode-status-indicator');
  const toggleBtn = document.getElementById('btn-toggle-barcode-camera');

  if (!html5QrCodeScanner) {
    html5QrCodeScanner = new Html5Qrcode("barcode-interactive");
  }

  const config = {
    fps: 10,
    qrbox: { width: 250, height: 160 },
    aspectRatio: 1.333
  };

  if (statusElem) statusElem.textContent = "Requesting camera...";

  html5QrCodeScanner.start(
    { facingMode: "environment" },
    config,
    (decodedText) => {
      // Successful decode
      if (statusElem) statusElem.textContent = `Barcode detected: ${decodedText}`;
      stopBarcodeCamera();
      queryBarcodeProduct(decodedText);
    },
    (errorMessage) => {
      // Frame decode noise, ignore
    }
  ).then(() => {
    isBarcodeCameraRunning = true;
    if (statusElem) statusElem.textContent = "Scanning active — position barcode in frame";
    if (toggleBtn) {
      toggleBtn.textContent = "Stop Camera";
      toggleBtn.className = "px-3 py-1 bg-red-50 hover:bg-red-100 text-red-600 font-bold rounded-lg border border-red-200 transition";
    }
  }).catch((err) => {
    console.error("Camera start failed", err);
    if (statusElem) statusElem.textContent = "Camera access denied or unavailable";
    showToast("Could not access camera. You can still enter barcode manually.", "warning");
  });
}

function stopBarcodeCamera() {
  if (html5QrCodeScanner && isBarcodeCameraRunning) {
    html5QrCodeScanner.stop().then(() => {
      isBarcodeCameraRunning = false;
      const statusElem = document.getElementById('barcode-status-indicator');
      const toggleBtn = document.getElementById('btn-toggle-barcode-camera');
      if (statusElem) statusElem.textContent = "Camera paused";
      if (toggleBtn) {
        toggleBtn.textContent = "Start Camera";
        toggleBtn.className = "px-3 py-1 bg-blue-50 hover:bg-blue-100 text-[#0066FF] font-bold rounded-lg border border-blue-200 transition";
      }
    }).catch((err) => {
      console.warn("Failed to stop scanner", err);
    });
  }
}

async function queryBarcodeProduct(barcode) {
  const statusElem = document.getElementById('barcode-status-indicator');
  activeScannedBarcode = barcode;
  if (statusElem) statusElem.textContent = `Looking up barcode ${barcode}...`;
  showToast(`Looking up barcode ${barcode}...`, 'info');

  // Step 1: Query Open Food Facts API
  try {
    const url = `https://world.openfoodfacts.org/api/v2/product/${encodeURIComponent(barcode)}.json`;
    const res = await fetch(url);
    const data = await res.json();

    if (res.ok && data.status === 1 && data.product) {
      const p = data.product;
      const nutr = p.nutriments || {};

      const brand = p.brands || p.brand_owner || 'Packaged Food';
      const name = p.product_name || p.product_name_en || p.generic_name || `Barcode Item #${barcode}`;
      const serving = p.serving_size || p.quantity || '100g';

      let cals = nutr['energy-kcal_serving'] || nutr['energy-kcal_100g'] || nutr['energy-kcal'] || 0;
      if (!cals && nutr['energy-kj_100g']) {
        cals = Math.round(nutr['energy-kj_100g'] / 4.184);
      }
      cals = Math.round(parseFloat(cals) || 0);

      const protein = parseFloat(nutr['proteins_serving'] || nutr['proteins_100g'] || nutr['proteins'] || 0);
      const carbs = parseFloat(nutr['carbohydrates_serving'] || nutr['carbohydrates_100g'] || nutr['carbohydrates'] || 0);
      const fat = parseFloat(nutr['fat_serving'] || nutr['fat_100g'] || nutr['fat'] || 0);

      currentBarcodeData = {
        barcode: barcode,
        food_name: `${name} (${brand})`,
        calories: cals,
        protein: Math.round(protein * 10) / 10,
        carbs: Math.round(carbs * 10) / 10,
        fat: Math.round(fat * 10) / 10,
        serving_size: serving
      };

      displayScannedBarcodeCard(brand, name, serving, cals, currentBarcodeData.protein, currentBarcodeData.carbs, currentBarcodeData.fat);
      if (statusElem) statusElem.textContent = `Found: ${name}`;
      showToast(`Product identified from Open Food Facts: ${name}!`, 'success');
      return;
    }
  } catch (err) {
    console.warn('Open Food Facts lookup failed or product missing, trying local database...', err);
  }

  // Step 2: Fallback to Local PostgreSQL custom_barcodes table
  try {
    if (statusElem) statusElem.textContent = `Checking local database for ${barcode}...`;
    const localRes = await fetch(`/api/barcodes/${encodeURIComponent(barcode)}`);
    if (localRes.ok) {
      const localData = await localRes.json();
      if (localData.success && localData.product) {
        const prod = localData.product;
        currentBarcodeData = {
          barcode: barcode,
          food_name: `${prod.food_name} (${prod.brand || 'Custom'})`,
          calories: Math.round(prod.calories || 0),
          protein: Math.round((prod.protein || 0) * 10) / 10,
          carbs: Math.round((prod.carbs || 0) * 10) / 10,
          fat: Math.round((prod.fat || 0) * 10) / 10,
          serving_size: prod.serving_size || '100g'
        };

        displayScannedBarcodeCard(prod.brand || 'Custom Item', prod.food_name, prod.serving_size || '100g', currentBarcodeData.calories, currentBarcodeData.protein, currentBarcodeData.carbs, currentBarcodeData.fat);
        if (statusElem) statusElem.textContent = `Found in Custom DB: ${prod.food_name}`;
        showToast(`Product found in custom database: ${prod.food_name}!`, 'success');
        return;
      }
    }
  } catch (err) {
    console.warn('Local database lookup failed', err);
  }

  // Step 3: Missing from both -> Trigger "New Product Detected" Modal with Camera OCR
  if (statusElem) statusElem.textContent = `Barcode ${barcode} not found. Snap nutrition label photo!`;
  showToast(`Barcode ${barcode} not recognized. Snap a photo of the nutrition table to auto-fill!`, 'warning');
  openNewProductModal(barcode);
}

function displayScannedBarcodeCard(brand, name, serving, cals, protein, carbs, fat) {
  setText('scanned-product-brand', brand);
  setText('scanned-product-name', name);
  setText('scanned-product-serving', `Serving: ${serving}`);
  setText('scanned-product-cals', cals);
  setText('scanned-product-protein', `${protein}g`);
  setText('scanned-product-carbs', `${carbs}g`);
  setText('scanned-product-fat', `${fat}g`);

  document.getElementById('barcode-result-card')?.classList.remove('hidden');
}

function openNewProductModal(barcode) {
  const modal = document.getElementById('new-product-modal');
  const label = document.getElementById('new-product-barcode-label');
  const nameInput = document.getElementById('new-barcode-name');
  const brandInput = document.getElementById('new-barcode-brand');
  const servingInput = document.getElementById('new-barcode-serving');
  const calsInput = document.getElementById('new-barcode-cals');
  const proteinInput = document.getElementById('new-barcode-protein');
  const carbsInput = document.getElementById('new-barcode-carbs');
  const fatInput = document.getElementById('new-barcode-fat');

  if (label) label.textContent = `#${barcode}`;
  if (nameInput) nameInput.value = '';
  if (brandInput) brandInput.value = '';
  if (servingInput) servingInput.value = '100g';
  if (calsInput) calsInput.value = '';
  if (proteinInput) proteinInput.value = '';
  if (carbsInput) carbsInput.value = '';
  if (fatInput) fatInput.value = '';

  document.getElementById('barcode-ocr-loading')?.classList.add('hidden');
  modal?.classList.remove('hidden');
}

function resetBarcodeState() {
  currentBarcodeData = null;
  activeScannedBarcode = null;
  const input = document.getElementById('manual-barcode-input');
  if (input) input.value = '';
  document.getElementById('barcode-result-card')?.classList.add('hidden');
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initNutritionTracker();
});
