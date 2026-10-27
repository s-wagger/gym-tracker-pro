/**
 * Gym Tracker Pro - Workout Logger & Exercise Manager
 * Handles dynamic multi-set entries, muscle group presets, live volume tallying,
 * AJAX submission, PR notifications, and history filtering.
 */

const EXERCISE_DATABASE = {
  "Chest": [
    "Bench Press",
    "Incline Dumbbell Press",
    "Incline Barbell Press",
    "Cable Crossover",
    "Chest Dips",
    "Dumbbell Flyes",
    "Push-ups"
  ],
  "Back": [
    "Deadlift",
    "Barbell Row",
    "Pull-ups",
    "Lat Pulldown",
    "Seated Cable Row",
    "Romanian Deadlift",
    "T-Bar Row",
    "Single-Arm Dumbbell Row"
  ],
  "Legs": [
    "Back Squat",
    "Front Squat",
    "Leg Press",
    "Bulgarian Split Squat",
    "Romanian Deadlift",
    "Leg Curl",
    "Leg Extension",
    "Standing Calf Raise"
  ],
  "Shoulders": [
    "Overhead Press",
    "Dumbbell Lateral Raise",
    "Arnold Press",
    "Face Pull",
    "Rear Delt Flyes",
    "Cable Lateral Raise"
  ],
  "Arms": [
    "Barbell Bicep Curl",
    "Incline Dumbbell Curl",
    "Hammer Curl",
    "Tricep Rope Pushdown",
    "Skull Crushers",
    "Close-Grip Bench Press"
  ],
  "Core": [
    "Hanging Leg Raise",
    "Cable Woodchoppers",
    "Ab Wheel Rollout",
    "Plank",
    "Decline Crunch"
  ],
  "Full Body": [
    "Clean and Jerk",
    "Snatch",
    "Kettlebell Swings",
    "Thrusters",
    "Farmer's Walk"
  ]
};

let currentSets = [];

function initWorkoutLogger() {
  const muscleSelect = document.getElementById('log-muscle-group');
  const exerciseSelect = document.getElementById('log-exercise-select');
  const addSetBtn = document.getElementById('btn-add-set');
  const workoutForm = document.getElementById('workout-log-form');

  if (!muscleSelect || !workoutForm) return;

  // 1. Populate exercises on muscle group change
  muscleSelect.addEventListener('change', () => {
    populateExercisesForMuscle(muscleSelect.value);
  });

  // Preload initial exercises
  populateExercisesForMuscle(muscleSelect.value);

  // 2. Add Set Button
  if (addSetBtn) {
    addSetBtn.addEventListener('click', () => {
      addNewSetRow();
    });
  }

  // Add initial 3 sets by default
  addNewSetRow(60, 10);
  addNewSetRow(60, 10);
  addNewSetRow(60, 8);

  // 3. Form Submission
  workoutForm.addEventListener('submit', handleWorkoutSubmit);

  // 4. History Filters
  const filterMuscle = document.getElementById('filter-muscle');
  const filterExercise = document.getElementById('filter-exercise');
  const filterDate = document.getElementById('filter-date');
  const filterBtn = document.getElementById('btn-apply-filters');
  const resetBtn = document.getElementById('btn-reset-filters');

  if (filterBtn) {
    filterBtn.addEventListener('click', applyWorkoutFilters);
  }
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (filterMuscle) filterMuscle.value = 'All';
      if (filterExercise) filterExercise.value = '';
      if (filterDate) filterDate.value = '';
      applyWorkoutFilters();
    });
  }
}

function populateExercisesForMuscle(muscle) {
  const select = document.getElementById('log-exercise-select');
  if (!select) return;

  select.innerHTML = '';
  const exercises = EXERCISE_DATABASE[muscle] || EXERCISE_DATABASE["Chest"];

  exercises.forEach((ex) => {
    const opt = document.createElement('option');
    opt.value = ex;
    opt.textContent = ex;
    select.appendChild(opt);
  });

  const customOpt = document.createElement('option');
  customOpt.value = "CUSTOM";
  customOpt.textContent = "✏️ Custom Exercise...";
  select.appendChild(customOpt);

  select.addEventListener('change', () => {
    const customInputContainer = document.getElementById('custom-exercise-container');
    if (customInputContainer) {
      if (select.value === "CUSTOM") {
        customInputContainer.classList.remove('hidden');
        document.getElementById('log-custom-exercise').focus();
      } else {
        customInputContainer.classList.add('hidden');
      }
    }
  });
}

function addNewSetRow(defaultWeight = null, defaultReps = null) {
  const container = document.getElementById('sets-container');
  if (!container) return;

  const currentCount = container.children.length;
  const setNumber = currentCount + 1;

  // Infer weight and reps from previous set if not provided
  let weight = defaultWeight;
  let reps = defaultReps;
  if (weight === null && currentCount > 0) {
    const lastRow = container.children[currentCount - 1];
    const prevWeightInput = lastRow.querySelector('.input-set-weight');
    const prevRepsInput = lastRow.querySelector('.input-set-reps');
    if (prevWeightInput) weight = prevWeightInput.value;
    if (prevRepsInput) reps = prevRepsInput.value;
  }
  if (weight === null) weight = 50;
  if (reps === null) reps = 10;

  const row = document.createElement('div');
  row.className = 'set-row flex items-center gap-3 p-3 bg-[#171717] rounded-xl border border-gray-800/80 mb-2 transition';
  row.dataset.setIndex = setNumber;

  row.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center font-bold text-xs text-[#CCFF00] shrink-0 set-badge">
      ${setNumber}
    </div>
    <div class="flex-1 min-w-[70px]">
      <label class="block text-[10px] uppercase font-bold text-gray-500 mb-1">Weight</label>
      <input type="number" step="0.5" min="0" value="${weight}" class="gt-input w-full py-1.5 px-2 text-sm text-center font-bold input-set-weight" oninput="calculateLiveVolume()">
    </div>
    <div class="flex-1 min-w-[60px]">
      <label class="block text-[10px] uppercase font-bold text-gray-500 mb-1">Reps</label>
      <input type="number" step="1" min="1" value="${reps}" class="gt-input w-full py-1.5 px-2 text-sm text-center font-bold input-set-reps" oninput="calculateLiveVolume()">
    </div>
    <div class="w-16 hidden sm:block">
      <label class="block text-[10px] uppercase font-bold text-gray-500 mb-1">RPE</label>
      <input type="number" step="0.5" min="5" max="10" value="8" class="gt-input w-full py-1.5 px-2 text-sm text-center font-semibold input-set-rpe">
    </div>
    <div class="flex flex-col items-center justify-center shrink-0 px-1">
      <label class="text-[10px] uppercase font-bold text-gray-500 mb-1">Warmup</label>
      <input type="checkbox" class="w-4 h-4 accent-[#CCFF00] input-set-warmup" onchange="calculateLiveVolume()">
    </div>
    <div class="flex items-end pb-0.5 shrink-0">
      <button type="button" class="w-8 h-8 rounded-lg bg-red-950/40 border border-red-800/40 text-red-400 hover:bg-red-900/60 flex items-center justify-center transition" onclick="removeSetRow(this)">
        ✕
      </button>
    </div>
  `;

  container.appendChild(row);
  calculateLiveVolume();
}

function removeSetRow(btn) {
  const container = document.getElementById('sets-container');
  if (!container) return;

  const row = btn.closest('.set-row');
  if (row) {
    row.remove();
    // Renumber remaining sets
    Array.from(container.children).forEach((child, index) => {
      const badge = child.querySelector('.set-badge');
      if (badge) badge.textContent = index + 1;
      child.dataset.setIndex = index + 1;
    });
    calculateLiveVolume();
  }
}

function calculateLiveVolume() {
  const container = document.getElementById('sets-container');
  const volumeElem = document.getElementById('live-session-volume');
  if (!container || !volumeElem) return;

  let totalVol = 0;
  const rows = container.querySelectorAll('.set-row');
  rows.forEach((row) => {
    const isWarmup = row.querySelector('.input-set-warmup')?.checked;
    if (!isWarmup) {
      const weight = parseFloat(row.querySelector('.input-set-weight')?.value || 0);
      const reps = parseInt(row.querySelector('.input-set-reps')?.value || 0);
      if (weight > 0 && reps > 0) {
        totalVol += (weight * reps);
      }
    }
  });

  volumeElem.textContent = `${totalVol.toLocaleString()} total volume`;
}

async function handleWorkoutSubmit(e) {
  e.preventDefault();
  const title = document.getElementById('log-workout-title').value.trim();
  const date = document.getElementById('log-workout-date').value;
  const muscleGroup = document.getElementById('log-muscle-group').value;
  let exerciseName = document.getElementById('log-exercise-select').value;
  
  if (exerciseName === "CUSTOM") {
    exerciseName = document.getElementById('log-custom-exercise').value.trim();
  }

  if (!exerciseName) {
    showToast('Please select or specify an exercise name.', 'error');
    return;
  }

  const container = document.getElementById('sets-container');
  const rows = container.querySelectorAll('.set-row');
  if (rows.length === 0) {
    showToast('Please add at least one set.', 'error');
    return;
  }

  const setsData = [];
  rows.forEach((row, idx) => {
    setsData.push({
      set_number: idx + 1,
      muscle_group: muscleGroup,
      exercise_name: exerciseName,
      weight: parseFloat(row.querySelector('.input-set-weight').value || 0),
      reps: parseInt(row.querySelector('.input-set-reps').value || 0),
      rpe: parseFloat(row.querySelector('.input-set-rpe')?.value || 8.0),
      is_warmup: row.querySelector('.input-set-warmup')?.checked || false
    });
  });

  const notes = document.getElementById('log-workout-notes')?.value || "";

  try {
    const response = await fetch('/api/workouts/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title || `${muscleGroup} Session`,
        date: date,
        notes: notes,
        sets: setsData
      })
    });

    const data = await response.json();
    if (response.ok && data.success) {
      if (data.new_prs && data.new_prs.length > 0) {
        data.new_prs.forEach((pr) => {
          showToast(`🏆 NEW PERSONAL RECORD! ${pr.exercise}: ${pr.weight} × ${pr.reps} reps (Est 1RM: ${pr.estimated_1rm})`, 'pr', 'PR UNLOCKED!');
        });
      } else {
        showToast('Workout successfully logged!', 'success');
      }

      // Reload page or refresh list
      setTimeout(() => {
        window.location.reload();
      }, 1200);
    } else {
      showToast(data.error || 'Failed to save workout session.', 'error');
    }
  } catch (err) {
    console.error('Error submitting workout:', err);
    showToast('Network error while saving workout.', 'error');
  }
}

async function applyWorkoutFilters() {
  const muscle = document.getElementById('filter-muscle')?.value || 'All';
  const exercise = document.getElementById('filter-exercise')?.value || '';
  const date = document.getElementById('filter-date')?.value || '';

  const params = new URLSearchParams({
    muscle: muscle,
    exercise: exercise,
    date: date
  });

  try {
    const res = await fetch(`/api/workouts?${params.toString()}`);
    const data = await res.json();
    if (res.ok && data.sessions) {
      renderWorkoutHistory(data.sessions);
    }
  } catch (err) {
    console.error('Filter fetch error:', err);
  }
}

function renderWorkoutHistory(sessions) {
  const container = document.getElementById('workout-history-list');
  if (!container) return;

  if (sessions.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12 bg-[#1E1E1E] border border-gray-800 rounded-2xl p-8">
        <div class="text-4xl mb-3">🏋️‍♂️</div>
        <h3 class="text-lg font-bold text-white mb-1">No Workouts Found</h3>
        <p class="text-gray-400 text-sm">Try adjusting your filters or record a new session above.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = sessions.map((s) => `
    <div class="gt-card p-5 mb-4 border border-gray-800 hover:border-gray-700 transition" id="workout-card-${s.id}">
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4 border-b border-gray-800/80 pb-3">
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-bold text-white">${s.title}</h3>
            ${s.has_pr ? `<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/40 flex items-center gap-1">🏆 PR</span>` : ''}
          </div>
          <div class="text-xs text-gray-400 mt-0.5">📅 ${s.date} • ${s.exercises_summary.join(', ')}</div>
        </div>
        <div class="flex items-center gap-4">
          <div class="text-right">
            <div class="text-sm font-black text-[#CCFF00]">${s.total_volume.toLocaleString()}</div>
            <div class="text-[10px] uppercase font-bold text-gray-500">Total Volume</div>
          </div>
          <button onclick="deleteWorkoutSession(${s.id})" class="text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-gray-800 transition" title="Delete workout">
            🗑️
          </button>
        </div>
      </div>

      <!-- Sets Table -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs text-gray-300">
          <thead class="text-[10px] uppercase tracking-wider text-gray-500 bg-[#171717] rounded-lg">
            <tr>
              <th class="py-2 px-3">Set</th>
              <th class="py-2 px-3">Exercise</th>
              <th class="py-2 px-3">Weight</th>
              <th class="py-2 px-3">Reps</th>
              <th class="py-2 px-3">Volume</th>
              <th class="py-2 px-3">Est 1RM</th>
              <th class="py-2 px-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-800/60">
            ${s.sets.map((set) => `
              <tr class="hover:bg-white/[0.02]">
                <td class="py-2.5 px-3 font-bold text-gray-400">#${set.set_number}</td>
                <td class="py-2.5 px-3 font-semibold text-white">${set.exercise_name}</td>
                <td class="py-2.5 px-3 font-bold text-[#CCFF00]">${set.weight}</td>
                <td class="py-2.5 px-3 font-bold text-white">${set.reps}</td>
                <td class="py-2.5 px-3 text-gray-400">${(set.weight * set.reps).toLocaleString()}</td>
                <td class="py-2.5 px-3 text-[#FFD700] font-semibold">${set.estimated_1rm || '-'}</td>
                <td class="py-2.5 px-3 text-right">
                  ${set.is_pr ? `<span class="text-[#FFD700] font-bold">🏆 PR</span>` : set.is_warmup ? `<span class="text-gray-500">Warmup</span>` : `<span class="text-gray-400">Done</span>`}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      ${s.notes ? `<div class="mt-3 pt-3 border-t border-gray-800/60 text-xs text-gray-400 italic">📝 ${s.notes}</div>` : ''}
    </div>
  `).join('');
}

async function deleteWorkoutSession(sessionId) {
  if (!confirm('Are you sure you want to delete this workout session?')) return;

  try {
    const res = await fetch(`/api/workouts/${sessionId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast('Workout session removed.', 'success');
      const elem = document.getElementById(`workout-card-${sessionId}`);
      if (elem) elem.remove();
    } else {
      showToast(data.error || 'Could not delete session.', 'error');
    }
  } catch (err) {
    showToast('Error deleting workout session.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', initWorkoutLogger);
