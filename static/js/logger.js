/**
 * Gym Tracker Pro - Unified Daily Workout Logger & Progressive Overload Engine
 * 
 * Features:
 * 1. Single Daily Session Flow: One consolidated session title per day (e.g., "Chest and Back").
 * 2. Multi-Exercise appending: Add multiple movements back-to-back under one session.
 * 3. Flexible Equipment Weight Selector & Manual Override Toggle.
 * 4. Progressive Overload "Last Time" Ghost Targets:
 *    - Displays previous session's performance for each movement (e.g. "Last Time: 30 kg x 10 reps").
 *    - Live visual feedback when beating previous session stats (Overload Indicator).
 * 5. Reusable Workout Routines & Custom Split Templates:
 *    - 1-click loading of splits (Push Day, Pull Day, Legs, Upper Body Power, Custom).
 *    - Save current active session as a reusable routine template.
 * 6. Celebratory PR & Badges Gamification Modal with Confetti:
 *    - Triggers celebratory modal and canvas confetti particle burst when new PRs or badges are achieved!
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

// Global active session state
let currentExercises = [];
let nextExerciseId = 1;
let nextSetId = 1;

// Ghost targets cache: exercise_name -> { weight, reps, estimated_1rm, date }
let ghostTargetsCache = {};

// Saved and starter routines
let loadedTemplates = [];

// Confetti animation handle
let confettiAnimationId = null;

/**
 * Initialize workout logger on DOM ready
 */
async function initWorkoutLogger() {
  const workoutForm = document.getElementById('workout-log-form');
  const addExerciseBtn = document.getElementById('btn-add-exercise');

  if (!workoutForm) return;

  // 1. Preload ghost targets cache from historical logs
  await preloadGhostTargets();

  // 2. Preload and render split templates
  await loadTemplates();

  // 3. Populate initial default exercises if none exist
  if (currentExercises.length === 0) {
    addExerciseToSession("Chest", "Bench Press", [
      { equipType: "plates", singleWeight: 20, plateWeight: 20, platesCount: 3, isOverride: false, overrideWeight: 60, totalWeight: 60, reps: 10, rpe: 8, isWarmup: false },
      { equipType: "plates", singleWeight: 20, plateWeight: 20, platesCount: 3, isOverride: false, overrideWeight: 60, totalWeight: 60, reps: 10, rpe: 8.5, isWarmup: false },
      { equipType: "plates", singleWeight: 20, plateWeight: 20, platesCount: 3, isOverride: false, overrideWeight: 60, totalWeight: 60, reps: 8, rpe: 9, isWarmup: false }
    ]);
  }

  // 4. Bind Add Next Exercise button
  if (addExerciseBtn) {
    addExerciseBtn.addEventListener('click', () => {
      const lastEx = currentExercises[currentExercises.length - 1];
      let nextMuscle = "Back";
      if (lastEx && lastEx.muscleGroup === "Chest") nextMuscle = "Back";
      else if (lastEx && lastEx.muscleGroup === "Back") nextMuscle = "Arms";
      else if (lastEx) nextMuscle = lastEx.muscleGroup;

      const exercisesList = EXERCISE_DATABASE[nextMuscle] || EXERCISE_DATABASE["Chest"];
      const defaultExName = exercisesList[0] || "Exercise";

      addExerciseToSession(nextMuscle, defaultExName, [
        { equipType: "direct", singleWeight: 40, plateWeight: 10, platesCount: 4, isOverride: false, overrideWeight: 40, totalWeight: 40, reps: 10, rpe: 8, isWarmup: false },
        { equipType: "direct", singleWeight: 40, plateWeight: 10, platesCount: 4, isOverride: false, overrideWeight: 40, totalWeight: 40, reps: 10, rpe: 8, isWarmup: false },
        { equipType: "direct", singleWeight: 40, plateWeight: 10, platesCount: 4, isOverride: false, overrideWeight: 40, totalWeight: 40, reps: 8, rpe: 8.5, isWarmup: false }
      ]);

      setTimeout(() => {
        const allCards = document.querySelectorAll('.exercise-card');
        if (allCards.length > 0) {
          allCards[allCards.length - 1].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    });
  }

  // 5. Bind Form Submission
  workoutForm.addEventListener('submit', handleWorkoutSubmit);

  // 6. Bind History Filters
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

/**
 * Preload all historical top performances to serve as Progressive Overload Ghost Targets
 */
async function preloadGhostTargets() {
  try {
    const res = await fetch('/api/workouts/last-performances');
    const data = await res.json();
    if (res.ok && data.performances) {
      ghostTargetsCache = data.performances;
    }
  } catch (err) {
    console.error('Error preloading ghost targets:', err);
  }
}

/**
 * Get ghost target for an exercise, fetching from API if not yet in cache
 */
async function fetchGhostTargetForExercise(exerciseName) {
  if (!exerciseName) return null;
  const cleanName = exerciseName.trim();
  const lowerName = cleanName.toLowerCase();

  // Search case-insensitively in cache
  for (let key in ghostTargetsCache) {
    if (key.toLowerCase() === lowerName) {
      return ghostTargetsCache[key];
    }
  }

  try {
    const res = await fetch(`/api/workouts/last-performance?exercise=${encodeURIComponent(cleanName)}`);
    const data = await res.json();
    if (res.ok && data.last_performance) {
      ghostTargetsCache[cleanName] = data.last_performance;
      return data.last_performance;
    }
  } catch (err) {
    console.error('Error fetching ghost target:', err);
  }
  return null;
}

/**
 * Load and render Reusable Workout Split Templates
 */
async function loadTemplates() {
  const container = document.getElementById('template-chips-container');
  if (!container) return;

  try {
    const res = await fetch('/api/templates');
    const data = await res.json();
    if (res.ok && data.templates) {
      loadedTemplates = data.templates;
      renderTemplateChips(loadedTemplates);
    }
  } catch (err) {
    console.error('Error loading routines:', err);
  }
}

function renderTemplateChips(templates) {
  const container = document.getElementById('template-chips-container');
  if (!container) return;

  if (templates.length === 0) {
    container.innerHTML = '<span class="text-xs text-slate-500 italic">No templates available.</span>';
    return;
  }

  container.innerHTML = templates.map((tmpl) => `
    <div class="inline-flex items-center gap-1.5 shrink-0 p-1 pl-3 pr-2 rounded-xl text-xs font-bold bg-[#101C3D] hover:bg-[#1E3A8A]/50 border border-blue-900/60 hover:border-[#E6D5B8]/50 transition group shadow-sm">
      <button type="button" onclick="applyTemplate('${tmpl.id}')" class="flex items-center gap-1.5 text-white hover:text-[#E6D5B8]">
        <span class="text-blue-400">🚀</span>
        <span>${tmpl.name}</span>
        <span class="text-[10px] text-slate-400 font-normal lowercase">(${tmpl.exercises.length} ex)</span>
      </button>

      ${tmpl.is_custom ? `
        <button type="button" onclick="deleteCustomTemplate(${tmpl.id}, event)" title="Delete template" class="text-slate-500 hover:text-red-400 ml-1 p-0.5 rounded transition">
          ✕
        </button>
      ` : ''}
    </div>
  `).join('');
}

/**
 * 1-Click Launch: Load routine template into the active session
 */
async function applyTemplate(templateId) {
  const tmpl = loadedTemplates.find(t => String(t.id) === String(templateId));
  if (!tmpl) return;

  const titleInput = document.getElementById('log-workout-title');
  if (titleInput) {
    titleInput.value = tmpl.name;
  }

  currentExercises = [];
  nextExerciseId = 1;
  nextSetId = 1;

  for (let i = 0; i < tmpl.exercises.length; i++) {
    const exConfig = tmpl.exercises[i];
    const targetSets = exConfig.targetSets || 3;
    const defWeight = exConfig.defaultWeight || 40;
    const defReps = exConfig.defaultReps || 10;
    const equipType = exConfig.equipType || "plates";

    const sets = [];
    for (let s = 1; s <= targetSets; s++) {
      sets.push({
        equipType: equipType,
        singleWeight: equipType === "dumbbell" ? defWeight : defWeight / 2,
        plateWeight: 10,
        platesCount: Math.max(1, Math.round(defWeight / 10)),
        isOverride: false,
        overrideWeight: defWeight,
        totalWeight: defWeight,
        reps: defReps,
        rpe: 8.0,
        isWarmup: false
      });
    }

    addExerciseToSession(exConfig.muscleGroup || "Chest", exConfig.exerciseName || "Exercise", sets);
  }

  showToast(`⚡ Loaded routine: ${tmpl.name}!`, 'success');

  // Scroll to active session
  const formSection = document.getElementById('section-workout-form');
  if (formSection) {
    formSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/**
 * Open Modal to Save Current Session as a Template
 */
function openSaveTemplateModal() {
  if (currentExercises.length === 0) {
    showToast('Add at least one exercise before saving as a routine template.', 'error');
    return;
  }

  const modal = document.getElementById('modal-save-template');
  const nameInput = document.getElementById('template-input-name');
  const currentTitle = document.getElementById('log-workout-title')?.value.trim();

  if (nameInput) {
    nameInput.value = currentTitle || "Custom Routine";
  }

  if (modal) modal.classList.remove('hidden');
}

function closeSaveTemplateModal() {
  const modal = document.getElementById('modal-save-template');
  if (modal) modal.classList.add('hidden');
}

/**
 * Confirm and save active session as a reusable split template
 */
async function confirmSaveTemplate() {
  const name = document.getElementById('template-input-name')?.value.trim();
  const category = document.getElementById('template-input-category')?.value || 'Custom';
  const desc = document.getElementById('template-input-desc')?.value.trim() || '';

  if (!name) {
    showToast('Please enter a routine name.', 'error');
    return;
  }

  const exercisesPayload = currentExercises.map(ex => {
    const exName = ex.exerciseName === "CUSTOM" ? (ex.customName || "Custom Exercise") : ex.exerciseName;
    const firstSet = ex.sets[0] || {};
    return {
      muscleGroup: ex.muscleGroup,
      exerciseName: exName,
      equipType: firstSet.equipType || "direct",
      defaultWeight: firstSet.totalWeight || 40,
      defaultReps: firstSet.reps || 10,
      targetSets: ex.sets.length || 3
    };
  });

  try {
    const res = await fetch('/api/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        description: desc,
        split_category: category,
        exercises: exercisesPayload
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Routine "${name}" saved to your templates!`, 'success');
      closeSaveTemplateModal();
      await loadTemplates();
    } else {
      showToast(data.error || 'Failed to save template.', 'error');
    }
  } catch (err) {
    console.error('Error saving template:', err);
    showToast('Network error while saving template.', 'error');
  }
}

/**
 * Delete a custom template
 */
async function deleteCustomTemplate(templateId, e) {
  if (e) e.stopPropagation();
  if (!confirm('Are you sure you want to remove this custom template?')) return;

  try {
    const res = await fetch(`/api/templates/${templateId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.success) {
      showToast('Template deleted.', 'success');
      await loadTemplates();
    } else {
      showToast(data.error || 'Could not delete template.', 'error');
    }
  } catch (err) {
    console.error('Error deleting template:', err);
  }
}

/**
 * Add an exercise block to the active session
 */
function addExerciseToSession(muscleGroup = "Chest", exerciseName = "Bench Press", initialSets = null) {
  const exId = nextExerciseId++;

  const sets = initialSets && initialSets.length > 0 ? initialSets.map((s, idx) => ({
    id: nextSetId++,
    setNumber: idx + 1,
    equipType: s.equipType || "direct",
    singleWeight: s.singleWeight !== undefined ? s.singleWeight : 20,
    plateWeight: s.plateWeight !== undefined ? s.plateWeight : 20,
    platesCount: s.platesCount !== undefined ? s.platesCount : 2,
    isOverride: Boolean(s.isOverride),
    overrideWeight: s.overrideWeight !== undefined ? s.overrideWeight : 40,
    totalWeight: s.totalWeight !== undefined ? s.totalWeight : 40,
    reps: s.reps !== undefined ? s.reps : 10,
    rpe: s.rpe !== undefined ? s.rpe : 8.0,
    isWarmup: Boolean(s.isWarmup)
  })) : [
    createNewDefaultSet(1, 40, 10)
  ];

  currentExercises.push({
    id: exId,
    muscleGroup: muscleGroup,
    exerciseName: exerciseName,
    customName: "",
    sets: sets
  });

  renderExercises();
}

function createNewDefaultSet(setNumber = 1, defaultWeight = 40, defaultReps = 10, equipType = "direct") {
  return {
    id: nextSetId++,
    setNumber: setNumber,
    equipType: equipType,
    singleWeight: equipType === "dumbbell" ? defaultWeight / 2 : defaultWeight,
    plateWeight: 10,
    platesCount: Math.max(1, Math.round(defaultWeight / 10)),
    isOverride: false,
    overrideWeight: defaultWeight,
    totalWeight: defaultWeight,
    reps: defaultReps,
    rpe: 8.0,
    isWarmup: false
  };
}

function computeSetWeights(set) {
  if (set.isOverride) {
    set.totalWeight = parseFloat(set.overrideWeight || 0);
  } else {
    switch (set.equipType) {
      case "dumbbell":
        set.totalWeight = parseFloat(set.singleWeight || 0) * 2;
        break;
      case "machine":
      case "plates":
        set.totalWeight = parseFloat(set.plateWeight || 0) * parseInt(set.platesCount || 0);
        break;
      case "direct":
      default:
        set.totalWeight = parseFloat(set.overrideWeight || set.singleWeight || 0);
        break;
    }
  }
}

function getEquipmentDetailsString(set) {
  if (set.equipType === "dumbbell") {
    if (set.isOverride) {
      return `Dumbbell (Manual Total: ${set.totalWeight}kg, single: ${set.singleWeight}kg)`;
    }
    return `2x ${set.singleWeight}kg (Total ${set.totalWeight}kg)`;
  } else if (set.equipType === "machine") {
    if (set.isOverride) {
      return `Machine Stack (Manual Total: ${set.totalWeight}kg, ${set.platesCount}x${set.plateWeight}kg)`;
    }
    return `${set.platesCount} plates @ ${set.plateWeight}kg`;
  } else if (set.equipType === "plates") {
    if (set.isOverride) {
      return `Plates (Manual Total: ${set.totalWeight}kg, ${set.platesCount}x${set.plateWeight}kg)`;
    }
    return `${set.platesCount} plates @ ${set.plateWeight}kg`;
  }
  return "Direct Total Load";
}

/**
 * Render all exercises in the container with Progressive Overload Ghost Targets
 */
async function renderExercises() {
  const container = document.getElementById('exercises-container');
  if (!container) return;

  container.innerHTML = '';

  for (let exIndex = 0; exIndex < currentExercises.length; exIndex++) {
    const exercise = currentExercises[exIndex];
    const card = document.createElement('div');
    card.className = 'exercise-card gt-card p-4 sm:p-6 bg-[#0A1128] border border-blue-900/60 rounded-2xl shadow-lg space-y-4';
    card.dataset.exerciseId = exercise.id;

    // Muscle options
    const muscleGroups = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Full Body"];
    const muscleOptionsHtml = muscleGroups.map(m => 
      `<option value="${m}" ${m === exercise.muscleGroup ? 'selected' : ''}>${m}</option>`
    ).join('');

    // Exercise options
    const exercisesList = EXERCISE_DATABASE[exercise.muscleGroup] || EXERCISE_DATABASE["Chest"];
    let exOptionsHtml = exercisesList.map(name => 
      `<option value="${name}" ${name === exercise.exerciseName ? 'selected' : ''}>${name}</option>`
    ).join('');
    exOptionsHtml += `<option value="CUSTOM" ${exercise.exerciseName === 'CUSTOM' ? 'selected' : ''}>✏️ Custom Exercise...</option>`;

    // Active movement name
    const activeMovementName = exercise.exerciseName === 'CUSTOM' ? (exercise.customName || 'Custom Exercise') : exercise.exerciseName;

    // Look up Ghost Target for this exercise
    const ghost = await fetchGhostTargetForExercise(activeMovementName);

    let ghostBadgeHtml = '';
    if (ghost) {
      ghostBadgeHtml = `
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[11px] font-black bg-[#2563EB]/20 text-[#E6D5B8] border border-[#2563EB]/40 shadow-sm" title="Your top set performance from your previous session">
          <span>🎯 Ghost Target:</span>
          <strong>Last Time: ${ghost.weight} kg × ${ghost.reps} reps</strong>
          <span class="text-[10px] text-slate-400 font-normal">(${ghost.date})</span>
        </span>
      `;
    } else {
      ghostBadgeHtml = `
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[10px] font-bold bg-[#101C3D] text-slate-400 border border-blue-900/40">
          <span>🎯 First time logging this movement!</span>
        </span>
      `;
    }

    card.innerHTML = `
      <!-- Exercise Header Row -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-800">
        <div class="flex flex-wrap items-center gap-2">
          <span class="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400 font-black text-xs flex items-center justify-center">
            #${exIndex + 1}
          </span>
          <span class="text-sm font-bold text-white tracking-wide">
            Exercise ${exIndex + 1}: <strong class="text-[#E6D5B8]">${activeMovementName}</strong>
          </span>
          <!-- Progressive Overload Ghost Target Badge -->
          ${ghostBadgeHtml}
        </div>

        <div class="flex items-center gap-2">
          ${currentExercises.length > 1 ? `
            <button type="button" class="btn-remove-exercise text-xs text-red-400 hover:text-red-300 px-2.5 py-1 rounded-lg bg-red-950/40 border border-red-800/40 hover:bg-red-900/60 transition" onclick="removeExercise(${exercise.id})">
              ✕ Remove Exercise
            </button>
          ` : ''}
        </div>
      </div>

      <!-- Muscle & Exercise Selector Row -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Target Muscle Group</label>
          <select class="gt-input w-full text-xs font-semibold select-muscle" onchange="onMuscleChange(${exercise.id}, this.value)">
            ${muscleOptionsHtml}
          </select>
        </div>

        <div>
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Select Exercise</label>
          <select class="gt-input w-full text-xs font-semibold select-exercise" onchange="onExerciseChange(${exercise.id}, this.value)">
            ${exOptionsHtml}
          </select>
        </div>

        <div class="col-span-1 sm:col-span-2 ${exercise.exerciseName === 'CUSTOM' ? '' : 'hidden'} custom-ex-wrapper">
          <label class="block text-[10px] uppercase font-bold text-[#E6D5B8] mb-1">Custom Exercise Name</label>
          <input type="text" class="gt-input w-full text-xs font-bold input-custom-ex" placeholder="e.g. Incline Smith Press" value="${exercise.customName || ''}" oninput="onCustomNameInput(${exercise.id}, this.value)">
        </div>
      </div>

      <!-- Sets Container for this Exercise -->
      <div class="space-y-2 pt-1">
        <div class="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1">
          <span>Sets & Equipment Weight Calculator</span>
          <span class="text-[10px] text-slate-500 lowercase">warmups excluded from volume</span>
        </div>

        <div class="exercise-sets-list space-y-2" id="sets-list-${exercise.id}">
          <!-- Set rows rendered below -->
        </div>

        <!-- Add Set to this Exercise Button -->
        <button type="button" class="w-full py-2 px-3 rounded-xl border border-dashed border-gray-700 hover:border-[#E6D5B8] text-gray-300 hover:text-[#E6D5B8] bg-[#101C3D]/60 hover:bg-[#101C3D] text-xs font-bold transition flex items-center justify-center gap-1.5 mt-2" onclick="addSetToExercise(${exercise.id})">
          <span>＋</span> Add Set to Exercise #${exIndex + 1}
        </button>
      </div>
    `;

    container.appendChild(card);
    renderSetsForExercise(exercise, ghost);
  }

  calculateLiveVolume();
}

/**
 * Render sets for a specific exercise and compare with Ghost Target for progressive overload
 */
function renderSetsForExercise(exercise, ghostTarget = null) {
  const setsContainer = document.getElementById(`sets-list-${exercise.id}`);
  if (!setsContainer) return;

  setsContainer.innerHTML = '';

  exercise.sets.forEach((set, sIdx) => {
    set.setNumber = sIdx + 1;
    computeSetWeights(set);

    const row = document.createElement('div');
    row.className = 'set-row p-3 rounded-xl bg-[#101C3D] border border-gray-800/80 hover:border-blue-900/60 transition flex flex-col gap-2.5';
    row.dataset.setId = set.id;

    // Equipment selection options
    const equipOptions = [
      { val: "direct", label: "Direct Total Wt" },
      { val: "dumbbell", label: "Dumbbell (Per Arm)" },
      { val: "machine", label: "Machine Stack / Plates" },
      { val: "plates", label: "Barbell / Smith Plates" }
    ];

    const equipSelectHtml = equipOptions.map(opt => 
      `<option value="${opt.val}" ${opt.val === set.equipType ? 'selected' : ''}>${opt.label}</option>`
    ).join('');

    // Progressive Overload Check
    let overloadIndicatorHtml = '';
    if (ghostTarget && set.totalWeight > 0 && set.reps > 0) {
      if (set.totalWeight > ghostTarget.weight) {
        const diff = (set.totalWeight - ghostTarget.weight).toFixed(1);
        overloadIndicatorHtml = `<span class="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">⚡ +${diff}kg OVERLOAD!</span>`;
      } else if (set.totalWeight === ghostTarget.weight && set.reps > ghostTarget.reps) {
        overloadIndicatorHtml = `<span class="text-[9px] font-black px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40">⚡ +${set.reps - ghostTarget.reps} REPS OVERLOAD!</span>`;
      }
    }

    // Dynamic weight input UI based on equipment and override status
    let weightInputControlsHtml = '';

    if (set.isOverride) {
      weightInputControlsHtml = `
        <div class="flex-1 min-w-[130px]">
          <div class="flex items-center justify-between mb-1">
            <label class="text-[10px] uppercase font-bold text-[#E6D5B8]">⚡ Manual Total Wt</label>
            <span class="text-[9px] text-[#E6D5B8]/80 font-bold bg-[#E6D5B8]/15 px-1 rounded">OVERRIDE ON</span>
          </div>
          <input type="number" step="0.5" min="0" value="${set.overrideWeight}" class="gt-input w-full py-1.5 px-2 text-xs font-bold text-[#E6D5B8] bg-blue-950/60 border-[#E6D5B8]/50" oninput="onOverrideWeightChange(${exercise.id}, ${set.id}, this.value)">
          <div class="flex items-center justify-between mt-0.5">
            <span class="text-[10px] text-slate-400">Total load: <strong>${set.totalWeight} kg</strong></span>
            ${overloadIndicatorHtml}
          </div>
        </div>
      `;
    } else if (set.equipType === "dumbbell") {
      weightInputControlsHtml = `
        <div class="flex-1 min-w-[130px]">
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Single DB Wt (One Arm)</label>
          <div class="flex items-center gap-1.5">
            <input type="number" step="0.5" min="0" value="${set.singleWeight}" class="gt-input w-full py-1.5 px-2 text-xs font-bold text-white text-center" oninput="onSingleWeightChange(${exercise.id}, ${set.id}, this.value)">
            <span class="text-[11px] font-bold text-slate-400">ea</span>
          </div>
          <div class="flex items-center justify-between mt-0.5">
            <span class="text-[10px] text-[#E6D5B8] font-bold">Total: <strong>${set.totalWeight} kg</strong></span>
            ${overloadIndicatorHtml}
          </div>
        </div>
      `;
    } else if (set.equipType === "machine" || set.equipType === "plates") {
      weightInputControlsHtml = `
        <div class="flex-1 min-w-[150px] flex items-center gap-2">
          <div class="flex-1">
            <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Plate Wt</label>
            <input type="number" step="0.5" min="0" value="${set.plateWeight}" class="gt-input w-full py-1.5 px-2 text-xs font-bold text-white text-center" oninput="onPlateWeightChange(${exercise.id}, ${set.id}, this.value)">
          </div>
          <div class="w-16">
            <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Plates</label>
            <input type="number" step="1" min="1" value="${set.platesCount}" class="gt-input w-full py-1.5 px-2 text-xs font-bold text-white text-center" oninput="onPlatesCountChange(${exercise.id}, ${set.id}, this.value)">
          </div>
        </div>
        <div class="hidden sm:block text-[10px] text-[#E6D5B8] font-bold shrink-0 self-end pb-2">
          Total: <strong>${set.totalWeight} kg</strong> ${overloadIndicatorHtml}
        </div>
      `;
    } else {
      weightInputControlsHtml = `
        <div class="flex-1 min-w-[120px]">
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Direct Total Weight</label>
          <input type="number" step="0.5" min="0" value="${set.totalWeight}" class="gt-input w-full py-1.5 px-2 text-xs font-bold text-[#E6D5B8] text-center" oninput="onDirectWeightChange(${exercise.id}, ${set.id}, this.value)">
          <div class="flex items-center justify-between mt-0.5">
            <span class="text-[10px] text-slate-400">Total: <strong>${set.totalWeight} kg</strong></span>
            ${overloadIndicatorHtml}
          </div>
        </div>
      `;
    }

    row.innerHTML = `
      <div class="flex flex-wrap items-center gap-2.5">
        <!-- Set Number Badge -->
        <div class="w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center font-black text-xs text-blue-400 shrink-0">
          #${set.setNumber}
        </div>

        <!-- Equipment Selector -->
        <div class="w-36 sm:w-44 shrink-0">
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Equipment</label>
          <select class="gt-input w-full py-1.5 px-2 text-xs font-semibold bg-[#0A1128]" onchange="onEquipTypeChange(${exercise.id}, ${set.id}, this.value)">
            ${equipSelectHtml}
          </select>
        </div>

        <!-- Weight Controls (Dynamic) -->
        ${weightInputControlsHtml}

        <!-- Manual Override Toggle Button -->
        <div class="shrink-0 pt-3 sm:pt-4">
          <button type="button" 
            title="Toggle Direct Manual Weight Override (bypass plate math)"
            class="px-2 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition flex items-center gap-1 border ${set.isOverride ? 'bg-[#E6D5B8] text-[#0A1128] border-[#E6D5B8] shadow-sm' : 'bg-[#0A1128] text-slate-400 hover:text-white border-gray-700'}"
            onclick="toggleManualOverride(${exercise.id}, ${set.id})">
            <span>⚡</span> <span>${set.isOverride ? 'Direct Total (On)' : 'Manual Override'}</span>
          </button>
        </div>

        <!-- Reps Input -->
        <div class="w-16 shrink-0">
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">Reps</label>
          <input type="number" step="1" min="1" value="${set.reps}" class="gt-input w-full py-1.5 px-2 text-xs font-bold text-white text-center" oninput="onRepsChange(${exercise.id}, ${set.id}, this.value)">
        </div>

        <!-- RPE Input -->
        <div class="w-16 hidden sm:block shrink-0">
          <label class="block text-[10px] uppercase font-bold text-slate-400 mb-1">RPE</label>
          <input type="number" step="0.5" min="5" max="10" value="${set.rpe}" class="gt-input w-full py-1.5 px-2 text-xs font-semibold text-center" oninput="onRpeChange(${exercise.id}, ${set.id}, this.value)">
        </div>

        <!-- Warmup Checkbox -->
        <div class="flex flex-col items-center justify-center shrink-0 px-1 pt-1">
          <label class="text-[9px] uppercase font-bold text-slate-400 mb-1">Warmup</label>
          <input type="checkbox" class="w-4 h-4 accent-[#2563EB]" ${set.isWarmup ? 'checked' : ''} onchange="onWarmupChange(${exercise.id}, ${set.id}, this.checked)">
        </div>

        <!-- Delete Set Button -->
        <div class="shrink-0 pt-3 sm:pt-4">
          <button type="button" class="w-7 h-7 rounded-lg bg-red-950/40 border border-red-800/40 text-red-400 hover:bg-red-900/60 flex items-center justify-center text-xs transition" onclick="removeSetFromExercise(${exercise.id}, ${set.id})">
            ✕
          </button>
        </div>
      </div>
    `;

    setsContainer.appendChild(row);
  });
}

/**
 * Event Handlers for Exercise & Set Mutations
 */
function onMuscleChange(exerciseId, muscle) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  ex.muscleGroup = muscle;
  const exercisesList = EXERCISE_DATABASE[muscle] || EXERCISE_DATABASE["Chest"];
  ex.exerciseName = exercisesList[0] || "Custom";
  renderExercises();
}

function onExerciseChange(exerciseId, exerciseName) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  ex.exerciseName = exerciseName;
  renderExercises();
}

function onCustomNameInput(exerciseId, value) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (ex) ex.customName = value;
}

function removeExercise(exerciseId) {
  if (currentExercises.length <= 1) {
    showToast('A workout session must contain at least one exercise.', 'error');
    return;
  }
  currentExercises = currentExercises.filter(e => e.id !== exerciseId);
  renderExercises();
}

function addSetToExercise(exerciseId) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;

  const count = ex.sets.length;
  let defWeight = 50;
  let defReps = 10;
  let defEquip = "direct";

  if (count > 0) {
    const lastSet = ex.sets[count - 1];
    defWeight = lastSet.totalWeight || 50;
    defReps = lastSet.reps || 10;
    defEquip = lastSet.equipType || "direct";
  }

  const newSet = createNewDefaultSet(count + 1, defWeight, defReps, defEquip);
  if (count > 0) {
    const lastSet = ex.sets[count - 1];
    newSet.singleWeight = lastSet.singleWeight;
    newSet.plateWeight = lastSet.plateWeight;
    newSet.platesCount = lastSet.platesCount;
    newSet.overrideWeight = lastSet.overrideWeight;
    newSet.isOverride = lastSet.isOverride;
  }

  ex.sets.push(newSet);
  renderExercises();
}

function removeSetFromExercise(exerciseId, setId) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  if (ex.sets.length <= 1) {
    showToast('Each exercise must have at least one set.', 'error');
    return;
  }
  ex.sets = ex.sets.filter(s => s.id !== setId);
  renderExercises();
}

function onEquipTypeChange(exerciseId, setId, equipType) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.equipType = equipType;
  if (equipType === "dumbbell") {
    set.singleWeight = set.totalWeight > 0 ? (set.totalWeight / 2) : 20;
  } else if (equipType === "machine" || equipType === "plates") {
    set.plateWeight = 10;
    set.platesCount = Math.max(1, Math.round((set.totalWeight || 40) / 10));
  }
  computeSetWeights(set);
  renderExercises();
}

function toggleManualOverride(exerciseId, setId) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.isOverride = !set.isOverride;
  if (set.isOverride) {
    set.overrideWeight = set.totalWeight;
  }
  computeSetWeights(set);
  renderExercises();
}

function onOverrideWeightChange(exerciseId, setId, val) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.overrideWeight = parseFloat(val) || 0;
  computeSetWeights(set);
  calculateLiveVolume();
}

function onSingleWeightChange(exerciseId, setId, val) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.singleWeight = parseFloat(val) || 0;
  computeSetWeights(set);
  renderSetsForExercise(ex);
  calculateLiveVolume();
}

function onPlateWeightChange(exerciseId, setId, val) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.plateWeight = parseFloat(val) || 0;
  computeSetWeights(set);
  renderSetsForExercise(ex);
  calculateLiveVolume();
}

function onPlatesCountChange(exerciseId, setId, val) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.platesCount = parseInt(val) || 0;
  computeSetWeights(set);
  renderSetsForExercise(ex);
  calculateLiveVolume();
}

function onDirectWeightChange(exerciseId, setId, val) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.overrideWeight = parseFloat(val) || 0;
  set.totalWeight = parseFloat(val) || 0;
  calculateLiveVolume();
}

function onRepsChange(exerciseId, setId, val) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;

  set.reps = parseInt(val) || 0;
  calculateLiveVolume();
}

function onRpeChange(exerciseId, setId, val) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;
  set.rpe = parseFloat(val) || 8.0;
}

function onWarmupChange(exerciseId, setId, checked) {
  const ex = currentExercises.find(e => e.id === exerciseId);
  if (!ex) return;
  const set = ex.sets.find(s => s.id === setId);
  if (!set) return;
  set.isWarmup = checked;
  calculateLiveVolume();
}

function calculateLiveVolume() {
  const statsElem = document.getElementById('live-session-stats');
  if (!statsElem) return;

  let totalVol = 0;
  let totalSets = 0;
  const totalExercises = currentExercises.length;

  currentExercises.forEach(ex => {
    ex.sets.forEach(set => {
      totalSets++;
      if (!set.isWarmup) {
        computeSetWeights(set);
        const w = parseFloat(set.totalWeight || 0);
        const r = parseInt(set.reps || 0);
        if (w > 0 && r > 0) {
          totalVol += (w * r);
        }
      }
    });
  });

  statsElem.textContent = `${totalExercises} ${totalExercises === 1 ? 'exercise' : 'exercises'} • ${totalSets} sets • ${totalVol.toLocaleString()} vol`;
}

function switchWorkoutView(mode) {
  const formSection = document.getElementById('section-workout-form');
  const historySection = document.getElementById('section-workout-history');
  const btnHistory = document.getElementById('tab-btn-history');
  const btnNew = document.getElementById('tab-btn-new');

  if (mode === 'new') {
    if (formSection) formSection.classList.remove('hidden');
    if (historySection) historySection.classList.add('hidden');
    if (btnNew) {
      btnNew.className = 'flex-1 py-2.5 px-4 rounded-xl text-xs font-black uppercase tracking-wider transition flex items-center justify-center gap-2 bg-[#E6D5B8] text-[#0A1128] shadow-sm';
    }
    if (btnHistory) {
      btnHistory.className = 'flex-1 py-2.5 px-4 rounded-xl text-xs font-black uppercase tracking-wider transition flex items-center justify-center gap-2 text-slate-400 hover:text-white';
    }
  } else {
    if (formSection) formSection.classList.add('hidden');
    if (historySection) historySection.classList.remove('hidden');
    if (btnHistory) {
      btnHistory.className = 'flex-1 py-2.5 px-4 rounded-xl text-xs font-black uppercase tracking-wider transition flex items-center justify-center gap-2 bg-[#E6D5B8] text-[#0A1128] shadow-sm';
    }
    if (btnNew) {
      btnNew.className = 'flex-1 py-2.5 px-4 rounded-xl text-xs font-black uppercase tracking-wider transition flex items-center justify-center gap-2 text-slate-400 hover:text-white';
    }
  }
}

/**
 * Handle form submission: collects all sets, posts to backend, and handles PR / Badges celebration
 */
async function handleWorkoutSubmit(e) {
  e.preventDefault();

  const titleInput = document.getElementById('log-workout-title');
  const dateInput = document.getElementById('log-workout-date');
  const notesInput = document.getElementById('log-workout-notes');

  const title = (titleInput ? titleInput.value : "").trim() || "Daily Workout Session";
  const date = (dateInput ? dateInput.value : "") || new Date().toISOString().split('T')[0];
  const notes = (notesInput ? notesInput.value : "").trim();

  // Validate exercises
  const allSetsData = [];

  for (let i = 0; i < currentExercises.length; i++) {
    const ex = currentExercises[i];
    let exName = ex.exerciseName;
    if (exName === "CUSTOM") {
      exName = (ex.customName || "").trim();
    }
    if (!exName) {
      showToast(`Please specify a name for Exercise #${i + 1}.`, 'error');
      return;
    }

    if (!ex.sets || ex.sets.length === 0) {
      showToast(`Please add at least one set for ${exName}.`, 'error');
      return;
    }

    ex.sets.forEach((set, sIdx) => {
      computeSetWeights(set);
      allSetsData.push({
        set_number: sIdx + 1,
        muscle_group: ex.muscleGroup,
        exercise_name: exName,
        weight: set.totalWeight,
        reps: set.reps,
        rpe: set.rpe,
        is_warmup: set.isWarmup,
        equipment_type: set.equipType,
        equipment_details: getEquipmentDetailsString(set)
      });
    });
  }

  if (allSetsData.length === 0) {
    showToast('Please add at least one exercise set.', 'error');
    return;
  }

  try {
    const response = await fetch('/api/workouts/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        date: date,
        notes: notes,
        sets: allSetsData
      })
    });

    const data = await response.json();
    if (response.ok && data.success) {
      // Check for PRs or unlocked badges to trigger celebratory modal
      const hasPRs = data.new_prs && data.new_prs.length > 0;
      const hasBadges = data.new_badges && data.new_badges.length > 0;

      if (hasPRs || hasBadges) {
        showPrCelebrationModal(data.new_prs || [], data.new_badges || []);
      } else {
        showToast(`Successfully saved ${title} with ${currentExercises.length} exercises!`, 'success');
      }

      // Preload updated ghost targets
      await preloadGhostTargets();

      // Automatically switch to history tab and refresh logs
      switchWorkoutView('history');
      applyWorkoutFilters();
    } else {
      showToast(data.error || 'Failed to save workout session.', 'error');
    }
  } catch (err) {
    console.error('Error submitting workout:', err);
    showToast('Network error while saving workout.', 'error');
  }
}

/**
 * Celebratory PR & Badges Modal with Confetti
 */
function showPrCelebrationModal(newPrs, newBadges) {
  const modal = document.getElementById('modal-pr-celebration');
  const list = document.getElementById('pr-celebration-list');
  if (!modal || !list) return;

  list.innerHTML = '';

  // Render PRs
  newPrs.forEach(pr => {
    const item = document.createElement('div');
    item.className = 'p-3 rounded-xl bg-[#0A1128] border border-[#E6D5B8]/40 flex items-center justify-between gap-3 shadow-md';
    item.innerHTML = `
      <div class="flex items-center gap-2.5">
        <span class="text-2xl">🏆</span>
        <div>
          <h4 class="text-xs font-black text-white">${pr.exercise}</h4>
          <span class="text-[11px] text-[#E6D5B8] font-bold">${pr.weight} kg × ${pr.reps} reps (1RM: ${pr.estimated_1rm})</span>
        </div>
      </div>
      <span class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
        ${pr.improvement || 'NEW PR'}
      </span>
    `;
    list.appendChild(item);
  });

  // Render newly unlocked badges
  newBadges.forEach(b => {
    const item = document.createElement('div');
    item.className = 'p-3 rounded-xl bg-gradient-to-r from-[#101C3D] to-blue-900/40 border border-blue-500/60 flex items-center justify-between gap-3 shadow-md';
    item.innerHTML = `
      <div class="flex items-center gap-2.5">
        <span class="text-2xl">${b.icon || '🎖️'}</span>
        <div>
          <h4 class="text-xs font-black text-[#E6D5B8]">${b.title}</h4>
          <span class="text-[10px] text-slate-300">${b.target}</span>
        </div>
      </div>
      <span class="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider bg-[#2563EB] text-white">
        UNLOCKED
      </span>
    `;
    list.appendChild(item);
  });

  modal.classList.remove('hidden');

  // Trigger Haptic Vibration on Mobile
  if (navigator.vibrate) {
    try { navigator.vibrate([100, 50, 150, 50, 250]); } catch (e) {}
  }

  // Start celebratory canvas confetti
  startConfettiBurst();
}

function closePrModal() {
  const modal = document.getElementById('modal-pr-celebration');
  if (modal) modal.classList.add('hidden');
  stopConfettiBurst();
}

/**
 * Pure JavaScript Confetti Burst (Works 100% offline in PWA with zero dependencies)
 */
function startConfettiBurst() {
  const canvas = document.getElementById('confetti-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const colors = ['#2563EB', '#E6D5B8', '#F59E0B', '#10B981', '#38BDF8', '#FFFFFF'];
  const particles = [];
  const particleCount = 140;

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: canvas.width / 2,
      y: canvas.height * 0.45,
      r: Math.random() * 6 + 3,
      d: Math.random() * particleCount,
      color: colors[Math.floor(Math.random() * colors.length)],
      tilt: Math.floor(Math.random() * 10) - 10,
      tiltAngleIncremental: (Math.random() * 0.07) + 0.05,
      tiltAngle: 0,
      vx: (Math.random() - 0.5) * 16,
      vy: (Math.random() - 0.7) * 18,
      gravity: 0.35,
      alpha: 1,
      decay: Math.random() * 0.01 + 0.005
    });
  }

  const startTime = Date.now();

  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(p => {
      p.tiltAngle += p.tiltAngleIncremental;
      p.vy += p.gravity;
      p.x += p.vx;
      p.y += p.vy;
      p.alpha -= p.decay;

      if (p.alpha > 0) {
        ctx.save();
        ctx.globalAlpha = Math.max(0, p.alpha);
        ctx.beginPath();
        ctx.lineWidth = p.r / 2;
        ctx.strokeStyle = p.color;
        ctx.moveTo(p.x + p.tilt + (p.r / 4), p.y);
        ctx.lineTo(p.x + p.tilt, p.y + p.tilt + (p.r / 4));
        ctx.stroke();
        ctx.restore();
      }
    });

    if (Date.now() - startTime < 3800) {
      confettiAnimationId = requestAnimationFrame(render);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  if (confettiAnimationId) cancelAnimationFrame(confettiAnimationId);
  confettiAnimationId = requestAnimationFrame(render);
}

function stopConfettiBurst() {
  if (confettiAnimationId) {
    cancelAnimationFrame(confettiAnimationId);
    confettiAnimationId = null;
  }
  const canvas = document.getElementById('confetti-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

/**
 * Filter history workouts
 */
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

/**
 * Render history workout cards
 */
function renderWorkoutHistory(sessions) {
  const container = document.getElementById('workout-history-list');
  if (!container) return;

  if (sessions.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12 bg-[#101C3D] border border-gray-800 rounded-2xl p-8">
        <div class="text-4xl mb-3">🏋️‍♂️</div>
        <h3 class="text-lg font-bold text-white mb-1">No Workouts Found</h3>
        <p class="text-slate-400 text-sm">Try adjusting your filters or record a new session above.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = sessions.map((s) => `
    <div class="gt-card p-5 mb-4 border border-gray-800 hover:border-[#2563EB]/40 transition" id="workout-card-${s.id}">
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4 border-b border-gray-800/80 pb-3">
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-bold text-white">${s.title}</h3>
            ${s.has_pr ? `<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-[#E6D5B8]/20 text-[#E6D5B8] border border-[#E6D5B8]/40 flex items-center gap-1">🏆 PR</span>` : ''}
          </div>
          <div class="text-xs text-slate-400 mt-0.5">📅 ${s.date} • ${s.exercises_summary.join(', ')}</div>
        </div>
        <div class="flex items-center gap-4">
          <div class="text-right">
            <div class="text-sm font-black text-[#E6D5B8]">${s.total_volume.toLocaleString()}</div>
            <div class="text-[10px] uppercase font-bold text-slate-500">Total Volume</div>
          </div>
          <button onclick="deleteWorkoutSession(${s.id})" class="text-gray-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-gray-800 transition" title="Delete workout">
            🗑️
          </button>
        </div>
      </div>

      <!-- Sets Table -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs text-gray-300">
          <thead class="text-[10px] uppercase tracking-wider text-slate-400 bg-[#0A1128] rounded-lg">
            <tr>
              <th class="py-2 px-3">Set</th>
              <th class="py-2 px-3">Exercise</th>
              <th class="py-2 px-3">Equipment</th>
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
                <td class="py-2.5 px-3 font-bold text-slate-400">#${set.set_number}</td>
                <td class="py-2.5 px-3 font-semibold text-white">${set.exercise_name}</td>
                <td class="py-2.5 px-3">
                  ${set.equipment_type && set.equipment_type !== 'direct' ? `
                    <span class="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-500/15 text-blue-300 border border-blue-500/30">
                      ${set.equipment_type}
                    </span>
                    ${set.equipment_details ? `<div class="text-[10px] text-slate-400 font-medium mt-0.5">${set.equipment_details}</div>` : ''}
                  ` : `
                    <span class="text-[10px] text-slate-500 font-semibold uppercase">Total Load</span>
                  `}
                </td>
                <td class="py-2.5 px-3 font-bold text-[#E6D5B8]">${set.weight}</td>
                <td class="py-2.5 px-3 font-bold text-white">${set.reps}</td>
                <td class="py-2.5 px-3 text-slate-400">${(set.weight * set.reps).toLocaleString()}</td>
                <td class="py-2.5 px-3 text-[#E6D5B8] font-semibold">${set.estimated_1rm || '-'}</td>
                <td class="py-2.5 px-3 text-right">
                  ${set.is_pr ? `<span class="text-[#E6D5B8] font-bold">🏆 PR</span>` : set.is_warmup ? `<span class="text-slate-500">Warmup</span>` : `<span class="text-slate-400">Done</span>`}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      ${s.notes ? `<div class="mt-3 pt-3 border-t border-gray-800/60 text-xs text-slate-400 italic">📝 ${s.notes}</div>` : ''}
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
