/**
 * Gym Tracker Pro - Calorie & Macro Tracker
 * Manages itemized meal logging, dynamic progress indicators, macro splits,
 * and date-based dietary analysis.
 */

let activeNutritionDate = new Date().toISOString().split('T')[0];

function initNutritionTracker() {
  const mealForm = document.getElementById('nutrition-log-form');
  const dateInput = document.getElementById('nutrition-active-date');
  const prevDayBtn = document.getElementById('btn-prev-day');
  const nextDayBtn = document.getElementById('btn-next-day');
  const todayBtn = document.getElementById('btn-today');

  if (dateInput) {
    activeNutritionDate = dateInput.value || activeNutritionDate;
    dateInput.addEventListener('change', () => {
      activeNutritionDate = dateInput.value;
      fetchNutritionForDate(activeNutritionDate);
    });
  }

  if (prevDayBtn) {
    prevDayBtn.addEventListener('click', () => changeNutritionDay(-1));
  }
  if (nextDayBtn) {
    nextDayBtn.addEventListener('click', () => changeNutritionDay(1));
  }
  if (todayBtn) {
    todayBtn.addEventListener('click', () => {
      const today = new Date().toISOString().split('T')[0];
      if (dateInput) dateInput.value = today;
      activeNutritionDate = today;
      fetchNutritionForDate(today);
    });
  }

  if (mealForm) {
    mealForm.addEventListener('submit', handleMealSubmit);
  }
}

function changeNutritionDay(delta) {
  const dateInput = document.getElementById('nutrition-active-date');
  const current = new Date(activeNutritionDate);
  current.setDate(current.getDate() + delta);
  const formatted = current.toISOString().split('T')[0];
  activeNutritionDate = formatted;
  if (dateInput) dateInput.value = formatted;
  fetchNutritionForDate(formatted);
}

async function handleMealSubmit(e) {
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

      fetchNutritionForDate(activeNutritionDate);
    } else {
      showToast(data.error || 'Failed to log meal.', 'error');
    }
  } catch (err) {
    console.error('Error logging meal:', err);
    showToast('Network error while logging meal.', 'error');
  }
}

async function fetchNutritionForDate(dateStr) {
  try {
    const res = await fetch(`/api/nutrition?date=${dateStr}`);
    const data = await res.json();
    if (res.ok) {
      updateNutritionUI(data);
    }
  } catch (err) {
    console.error('Error fetching nutrition:', err);
  }
}

function updateNutritionUI(data) {
  const totals = data.totals;
  const targets = data.targets; // User configured daily targets

  // 1. Calories Bar
  const calConsumedElem = document.getElementById('cal-consumed');
  const calTargetElem = document.getElementById('cal-target');
  const calRemainingElem = document.getElementById('cal-remaining');
  const calBarElem = document.getElementById('cal-progress-bar');

  if (calConsumedElem) calConsumedElem.textContent = totals.calories.toLocaleString();
  if (calTargetElem) calTargetElem.textContent = targets.calories.toLocaleString();
  
  const remainingCals = Math.max(0, targets.calories - totals.calories);
  if (calRemainingElem) {
    calRemainingElem.textContent = `${remainingCals.toLocaleString()} kcal left`;
  }

  if (calBarElem) {
    const calPct = Math.min(100, Math.round((totals.calories / targets.calories) * 100));
    calBarElem.style.width = `${calPct}%`;
    calBarElem.className = `h-3 rounded-full transition-all duration-700 ${calPct > 100 ? 'bg-red-500' : 'bg-[#CCFF00]'}`;
  }

  // 2. Protein Bar
  const proteinValElem = document.getElementById('protein-val');
  const proteinBarElem = document.getElementById('protein-progress-bar');
  if (proteinValElem) proteinValElem.textContent = `${totals.protein} / ${targets.protein}g`;
  if (proteinBarElem) {
    const pPct = Math.min(100, Math.round((totals.protein / targets.protein) * 100));
    proteinBarElem.style.width = `${pPct}%`;
  }

  // 3. Carbs Bar
  const carbsValElem = document.getElementById('carbs-val');
  const carbsBarElem = document.getElementById('carbs-progress-bar');
  if (carbsValElem) carbsValElem.textContent = `${totals.carbs} / ${targets.carbs}g`;
  if (carbsBarElem) {
    const cPct = Math.min(100, Math.round((totals.carbs / targets.carbs) * 100));
    carbsBarElem.style.width = `${cPct}%`;
  }

  // 4. Fat Bar
  const fatValElem = document.getElementById('fat-val');
  const fatBarElem = document.getElementById('fat-progress-bar');
  if (fatValElem) fatValElem.textContent = `${totals.fat} / ${targets.fat}g`;
  if (fatBarElem) {
    const fPct = Math.min(100, Math.round((totals.fat / targets.fat) * 100));
    fatBarElem.style.width = `${fPct}%`;
  }

  // 5. Render Itemized Meal Groups
  renderMealItems(data.grouped);
}

function renderMealItems(grouped) {
  const container = document.getElementById('meal-items-container');
  if (!container) return;

  const categories = ["Breakfast", "Lunch", "Dinner", "Snack", "Post-Workout"];
  let totalEntries = 0;

  let html = '';
  categories.forEach((cat) => {
    const items = grouped[cat] || [];
    totalEntries += items.length;

    const catCals = items.reduce((acc, i) => acc + i.calories, 0);

    html += `
      <div class="gt-card p-4 mb-4 border border-gray-800">
        <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-800/80">
          <div class="flex items-center gap-2">
            <span class="text-base">${getMealCategoryIcon(cat)}</span>
            <h4 class="font-bold text-white text-sm">${cat}</h4>
            <span class="text-xs text-gray-400">(${items.length} items)</span>
          </div>
          <div class="text-xs font-bold text-[#CCFF00]">${catCals.toLocaleString()} kcal</div>
        </div>

        ${items.length === 0 ? `
          <div class="text-xs text-gray-500 italic py-2 text-center">No foods logged for ${cat}.</div>
        ` : `
          <div class="divide-y divide-gray-800/40">
            ${items.map((item) => `
              <div class="flex items-center justify-between py-2 text-xs">
                <div>
                  <div class="font-semibold text-gray-200">${item.food_name}</div>
                  <div class="text-[11px] text-gray-400 mt-0.5">
                    P: <span class="text-blue-400 font-medium">${item.protein}g</span> • 
                    C: <span class="text-amber-400 font-medium">${item.carbs}g</span> • 
                    F: <span class="text-red-400 font-medium">${item.fat}g</span>
                  </div>
                </div>
                <div class="flex items-center gap-3">
                  <span class="font-bold text-white">${item.calories} kcal</span>
                  <button onclick="deleteMealItem(${item.id})" class="text-gray-500 hover:text-red-400 p-1 transition" title="Delete entry">
                    ✕
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        `}
      </div>
    `;
  });

  if (totalEntries === 0) {
    container.innerHTML = `
      <div class="text-center py-10 bg-[#1E1E1E] border border-gray-800 rounded-2xl p-6">
        <div class="text-4xl mb-2">🥗</div>
        <h4 class="font-bold text-white text-base mb-1">No Meals Logged Today</h4>
        <p class="text-gray-400 text-xs">Use the quick logging form to track your calories and macros.</p>
      </div>
    `;
  } else {
    container.innerHTML = html;
  }
}

function getMealCategoryIcon(cat) {
  switch (cat) {
    case "Breakfast": return "🍳";
    case "Lunch": return "🥗";
    case "Dinner": return "🥩";
    case "Snack": return "🍎";
    case "Post-Workout": return "🥤";
    default: return "🍽️";
  }
}

async function deleteMealItem(entryId) {
  try {
    const res = await fetch(`/api/nutrition/${entryId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast('Food entry removed.', 'success');
      fetchNutritionForDate(activeNutritionDate);
    } else {
      showToast(data.error || 'Failed to remove food item.', 'error');
    }
  } catch (err) {
    showToast('Error deleting meal item.', 'error');
  }
}

// -------------------------------------------------------------
// AI Food Camera & Nutrition Vision Scanner
// -------------------------------------------------------------
let currentScannedData = null;

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
  
  // API key & error elements
  const keyToggleBtn = document.getElementById('btn-toggle-key-settings');
  const apiKeyBox = document.getElementById('camera-api-key-box');
  const apiKeyInput = document.getElementById('camera-gemini-key-input');
  const saveKeyBtn = document.getElementById('btn-save-camera-key');
  const errorBanner = document.getElementById('camera-error-banner');
  const errorMessage = document.getElementById('camera-error-message');
  const retakeErrorBtn = document.getElementById('btn-camera-retake-error');

  if (!openBtn || !modal) return;

  keyToggleBtn?.addEventListener('click', () => {
    apiKeyBox?.classList.toggle('hidden');
  });

  saveKeyBtn?.addEventListener('click', async () => {
    const keyVal = apiKeyInput?.value?.trim();
    if (!keyVal) {
      showToast('Please paste a valid Gemini API key.', 'error');
      return;
    }
    try {
      const res = await fetch('/api/user/save-gemini-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: keyVal })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Gemini API key saved! You can now scan real meals.', 'success');
        apiKeyBox?.classList.add('hidden');
      } else {
        showToast(data.error || 'Failed to save key.', 'error');
      }
    } catch (err) {
      showToast('Error saving API key.', 'error');
    }
  });

  openBtn.addEventListener('click', () => {
    modal.classList.remove('hidden');
    resetCameraState();
  });

  closeBtn.addEventListener('click', () => {
    modal.classList.add('hidden');
    resetCameraState();
  });

  uploadZone.addEventListener('click', () => {
    fileInput.click();
  });

  retakeBtn?.addEventListener('click', () => {
    resetCameraState();
    fileInput.click();
  });

  retakeErrorBtn?.addEventListener('click', () => {
    resetCameraState();
    fileInput.click();
  });

  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = async (evt) => {
      imagePreview.src = evt.target.result;
      uploadZone.classList.add('hidden');
      previewZone.classList.remove('hidden');
      scanningIndicator.classList.remove('hidden');
      resultsZone.classList.add('hidden');
      errorBanner?.classList.add('hidden');

      // Upload and analyze
      const formData = new FormData();
      formData.append('meal_image', file);

      try {
        const res = await fetch('/api/nutrition/scan-meal', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        scanningIndicator.classList.add('hidden');

        if (res.ok && data.success && data.analysis) {
          currentScannedData = data.analysis;
          renderScanResults(data.analysis);
          resultsZone.classList.remove('hidden');
          errorBanner?.classList.add('hidden');
        } else if (data.needs_api_key) {
          apiKeyBox?.classList.remove('hidden');
          apiKeyInput?.focus();
          showToast('Google Gemini API Key required. Paste your free key above to scan.', 'warning');
        } else if (data.is_food === false || !res.ok) {
          if (errorBanner && errorMessage) {
            errorMessage.textContent = data.error || 'No food detected in this photo. Please aim your camera at an actual meal.';
            errorBanner.classList.remove('hidden');
          } else {
            showToast(data.error || 'No food detected.', 'error');
          }
        }
      } catch (err) {
        scanningIndicator.classList.add('hidden');
        showToast('Network error while processing image.', 'error');
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
        showToast(`Logged "${currentScannedData.food_name}" (${currentScannedData.calories} kcal) via AI Scanner!`, 'success');
        modal.classList.add('hidden');
        resetCameraState();
        fetchNutritionForDate(activeNutritionDate);
      } else {
        showToast(data.error || 'Failed to save scanned meal.', 'error');
      }
    } catch (err) {
      showToast('Error saving meal.', 'error');
    }
  });

  function resetCameraState() {
    fileInput.value = '';
    currentScannedData = null;
    uploadZone.classList.remove('hidden');
    previewZone.classList.add('hidden');
    resultsZone.classList.add('hidden');
    scanningIndicator.classList.add('hidden');
    errorBanner?.classList.add('hidden');
  }

  function renderScanResults(analysis) {
    document.getElementById('detected-food-name').textContent = analysis.food_name;
    document.getElementById('detected-food-desc').textContent = `${analysis.description} (${analysis.portion_size})`;
    document.getElementById('detected-cals').textContent = Math.round(analysis.calories);
    document.getElementById('detected-protein').textContent = `${Math.round(analysis.protein)}g`;
    document.getElementById('detected-carbs').textContent = `${Math.round(analysis.carbs)}g`;
    document.getElementById('detected-fat').textContent = `${Math.round(analysis.fat)}g`;

    const breakdownContainer = document.getElementById('detected-breakdown-list');
    if (breakdownContainer && analysis.breakdown) {
      breakdownContainer.innerHTML = analysis.breakdown.map((item) => `
        <div class="flex items-center justify-between p-1.5 rounded-lg bg-[#181818] border border-gray-800">
          <span>${item.item} (${item.portion})</span>
          <span class="font-bold text-white">${Math.round(item.calories)} kcal • P: ${Math.round(item.protein)}g</span>
        </div>
      `).join('');
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initNutritionTracker();
  initAiCameraScanner();
});
