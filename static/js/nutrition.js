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

document.addEventListener('DOMContentLoaded', initNutritionTracker);
