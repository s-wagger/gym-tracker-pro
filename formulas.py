"""
Gym Tracker Pro - Mathematical Calculation Engine
Implements standard fitness algorithms:
- Epley 1RM formula: 1RM = W * (1 + R / 30)
- Brzycki and Lombardi formulas for comparison
- Training zones computation (50%, 60%, 70%, 75%, 80%, 85%, 90%, 95%, 100%)
- Automated PR detection and milestone badge evaluations
"""
import math

def calculate_epley_1rm(weight: float, reps: int) -> float:
    """
    Computes 1-Rep Max using the Epley standard formula:
    1RM = W * (1 + R / 30)
    If reps is 1, returns the exact weight lifted.
    """
    if reps <= 0 or weight <= 0:
        return 0.0
    if reps == 1:
        return round(float(weight), 1)
    
    one_rm = float(weight) * (1.0 + (float(reps) / 30.0))
    return round(one_rm, 1)

def calculate_brzycki_1rm(weight: float, reps: int) -> float:
    """
    Computes 1-Rep Max using the Brzycki formula:
    1RM = W * (36 / (37 - R))
    Valid for R < 37.
    """
    if reps <= 0 or weight <= 0:
        return 0.0
    if reps == 1:
        return round(float(weight), 1)
    if reps >= 37:
        return round(float(weight) * 2.0, 1)
    
    one_rm = float(weight) * (36.0 / (37.0 - float(reps)))
    return round(one_rm, 1)

def calculate_lombardi_1rm(weight: float, reps: int) -> float:
    """
    Computes 1-Rep Max using the Lombardi formula:
    1RM = W * (R ^ 0.10)
    """
    if reps <= 0 or weight <= 0:
        return 0.0
    if reps == 1:
        return round(float(weight), 1)
    
    one_rm = float(weight) * math.pow(float(reps), 0.10)
    return round(one_rm, 1)

def get_training_zones(one_rm: float, unit: str = "kg") -> list:
    """
    Generates structured training percentages from 1RM:
    Includes required percentages: 50%, 75%, 85%, 90%, plus full spectrum (60%, 70%, 80%, 95%, 100%).
    """
    if one_rm <= 0:
        return []

    zone_definitions = [
        {
            "percentage": 100,
            "label": "Absolute Max (1RM)",
            "rep_range": "1 Rep",
            "intensity": "Maximum",
            "color": "#FF3366", # Vibrant Coral Red
            "purpose": "True 1RM test / Competition peak"
        },
        {
            "percentage": 95,
            "label": "Near-Max Peak",
            "rep_range": "1 - 2 Reps",
            "intensity": "Very High",
            "color": "#FF5722",
            "purpose": "Neural recruitment & heavy singles"
        },
        {
            "percentage": 90,
            "label": "Heavy Strength",
            "rep_range": "3 - 4 Reps",
            "intensity": "High",
            "color": "#FFD700", # Gold
            "purpose": "Maximum strength development"
        },
        {
            "percentage": 85,
            "label": "Strength Hypertrophy",
            "rep_range": "5 - 6 Reps",
            "intensity": "Sub-Maximal",
            "color": "#CCFF00", # Neon Lime
            "purpose": "Strength building & functional myofibrillar hypertrophy"
        },
        {
            "percentage": 80,
            "label": "Standard Hypertrophy",
            "rep_range": "7 - 8 Reps",
            "intensity": "Moderate-High",
            "color": "#00E5FF", # Cyan
            "purpose": "Optimal muscle mass & size stimulation"
        },
        {
            "percentage": 75,
            "label": "Hypertrophy & Work Capacity",
            "rep_range": "9 - 10 Reps",
            "intensity": "Moderate",
            "color": "#00FF88", # Spring Green
            "purpose": "High volume hypertrophy & technique under fatigue"
        },
        {
            "percentage": 70,
            "label": "Volume / Muscular Endurance",
            "rep_range": "11 - 12 Reps",
            "intensity": "Moderate",
            "color": "#76FF03",
            "purpose": "Metabolic stress and conditioning"
        },
        {
            "percentage": 60,
            "label": "Explosive / Speed Work",
            "rep_range": "12 - 15 Reps",
            "intensity": "Light-Moderate",
            "color": "#64B5F6",
            "purpose": "Dynamic effort and speed development"
        },
        {
            "percentage": 50,
            "label": "Deload / Active Recovery",
            "rep_range": "15 - 20 Reps",
            "intensity": "Light",
            "color": "#B0BEC5",
            "purpose": "Warmup, active recovery, motor pattern drilling"
        }
    ]

    results = []
    for zone in zone_definitions:
        pct = zone["percentage"]
        target_weight = round(one_rm * (pct / 100.0), 1)
        results.append({
            "percentage": pct,
            "weight": target_weight,
            "unit": unit,
            "label": zone["label"],
            "rep_range": zone["rep_range"],
            "intensity": zone["intensity"],
            "color": zone["color"],
            "purpose": zone["purpose"]
        })

    return results

def evaluate_milestones(stats: dict, unit: str = "kg") -> list:
    """
    Evaluates fitness milestones and club achievements based on user metrics.
    unit is 'kg' or 'lbs'.
    """
    milestones = []
    
    # Weight conversion multiplier
    to_kg = 1.0 if unit == "kg" else 0.453592
    to_lbs = 2.20462 if unit == "kg" else 1.0

    key_prs = stats.get("key_prs", {})
    bench_pr = key_prs.get("Bench Press", {}).get("weight", 0) * (to_kg if unit == "lbs" else 1.0)
    squat_pr = key_prs.get("Back Squat", {}).get("weight", 0) * (to_kg if unit == "lbs" else 1.0)
    deadlift_pr = key_prs.get("Deadlift", {}).get("weight", 0) * (to_kg if unit == "lbs" else 1.0)
    
    # 1. 100kg / 225lbs Bench Club
    bench_achieved = bench_pr >= 100.0
    bench_target = "100 kg / 225 lbs"
    milestones.append({
        "id": "bench_club_100",
        "title": "225lb / 100kg Bench Club",
        "category": "Strength Club",
        "icon": "🏋️‍♂️",
        "target": bench_target,
        "current": f"{round(bench_pr if unit == 'kg' else bench_pr * 2.20462, 1)} {unit}",
        "achieved": bench_achieved,
        "progress": min(100, int((bench_pr / 100.0) * 100)) if bench_pr else 0
    })

    # 2. 140kg / 315lbs Squat Club
    squat_achieved = squat_pr >= 140.0
    milestones.append({
        "id": "squat_club_140",
        "title": "315lb / 140kg Squat Club",
        "category": "Strength Club",
        "icon": "🦵",
        "target": "140 kg / 315 lbs",
        "current": f"{round(squat_pr if unit == 'kg' else squat_pr * 2.20462, 1)} {unit}",
        "achieved": squat_achieved,
        "progress": min(100, int((squat_pr / 140.0) * 100)) if squat_pr else 0
    })

    # 3. 180kg / 405lbs Deadlift Club
    deadlift_achieved = deadlift_pr >= 180.0
    milestones.append({
        "id": "deadlift_club_180",
        "title": "405lb / 180kg Deadlift Club",
        "category": "Strength Club",
        "icon": "⚡",
        "target": "180 kg / 405 lbs",
        "current": f"{round(deadlift_pr if unit == 'kg' else deadlift_pr * 2.20462, 1)} {unit}",
        "achieved": deadlift_achieved,
        "progress": min(100, int((deadlift_pr / 180.0) * 100)) if deadlift_pr else 0
    })

    # 4. The 1000lb Club (Squat + Bench + Deadlift combined >= 1000 lbs / 453.6 kg)
    total_big_three_kg = bench_pr + squat_pr + deadlift_pr
    total_big_three_lbs = total_big_three_kg * 2.20462
    one_thousand_club_achieved = total_big_three_lbs >= 1000.0
    milestones.append({
        "id": "thousand_lb_club",
        "title": "The 1000-lb Club",
        "category": "Strength Club",
        "tier": "gold",
        "icon": "🏆",
        "target": "1,000 lbs (454 kg) Total",
        "current": f"{round(total_big_three_lbs if unit == 'lbs' else total_big_three_kg, 1)} {unit}",
        "achieved": one_thousand_club_achieved,
        "progress": min(100, int((total_big_three_lbs / 1000.0) * 100)) if total_big_three_lbs else 0
    })

    # 5. First 100kg Lift (Any exercise >= 100kg / 220lbs)
    max_lift_kg = float(stats.get("max_lift_kg", 0.0))
    first_100_achieved = max_lift_kg >= 100.0
    milestones.append({
        "id": "first_100kg_lift",
        "title": "First 100kg Lift",
        "category": "Strength Club",
        "tier": "silver",
        "icon": "🎖️",
        "target": "100 kg (220 lbs) on any lift",
        "current": f"{round(max_lift_kg if unit == 'kg' else max_lift_kg * 2.20462, 1)} {unit}",
        "achieved": first_100_achieved,
        "progress": min(100, int((max_lift_kg / 100.0) * 100)) if max_lift_kg else 0
    })

    # 6. 50kg Dumbbell Club (Dumbbell total >= 50kg or single >= 25kg)
    max_db_kg = float(stats.get("max_db_kg", 0.0))
    db_50_achieved = max_db_kg >= 50.0
    milestones.append({
        "id": "db_50kg_club",
        "title": "50kg Dumbbell Club",
        "category": "Strength Club",
        "tier": "gold",
        "icon": "💥",
        "target": "50 kg Total (25kg/arm)",
        "current": f"{round(max_db_kg if unit == 'kg' else max_db_kg * 2.20462, 1)} {unit}",
        "achieved": db_50_achieved,
        "progress": min(100, int((max_db_kg / 50.0) * 100)) if max_db_kg else 0
    })

    # 7. PR Mastery Badges
    pr_count = int(stats.get("pr_count", 0))
    pr_pioneer = pr_count >= 1
    milestones.append({
        "id": "pr_pioneer",
        "title": "PR Pioneer",
        "category": "PR Mastery",
        "tier": "bronze",
        "icon": "🌟",
        "target": "1 Active PR Recorded",
        "current": f"{pr_count} PRs",
        "achieved": pr_pioneer,
        "progress": min(100, int((pr_count / 1.0) * 100)) if pr_count else 0
    })

    pr_master = pr_count >= 5
    milestones.append({
        "id": "pr_master_5",
        "title": "New PR Master",
        "category": "PR Mastery",
        "tier": "gold",
        "icon": "🏅",
        "target": "5 Distinct Exercise PRs",
        "current": f"{pr_count} PRs",
        "achieved": pr_master,
        "progress": min(100, int((pr_count / 5.0) * 100)) if pr_count else 0
    })

    # 8. Consistency & Streak Badges
    streak_days = int(stats.get("streak_days", 0))
    streak_achieved = streak_days >= 3
    milestones.append({
        "id": "consistency_streak_3",
        "title": "Consistency Streak",
        "category": "Consistency",
        "tier": "silver",
        "icon": "⚡",
        "target": "3+ Workout Days Streak",
        "current": f"{streak_days} Days Streak",
        "achieved": streak_achieved,
        "progress": min(100, int((streak_days / 3.0) * 100)) if streak_days else 0
    })

    # 9. Volume Titans
    total_vol = float(stats.get("total_volume", 0.0))
    session_max_vol = float(stats.get("session_max_volume", 0.0))
    vol_beast = session_max_vol >= 10000.0
    milestones.append({
        "id": "volume_beast_10k",
        "title": "Volume Beast",
        "category": "Volume",
        "tier": "gold",
        "icon": "🦍",
        "target": "10,000 kg in One Session",
        "current": f"{int(session_max_vol)} {unit}",
        "achieved": vol_beast,
        "progress": min(100, int((session_max_vol / 10000.0) * 100)) if session_max_vol else 0
    })

    heavy_artillery = total_vol >= 50000.0
    milestones.append({
        "id": "heavy_artillery_50k",
        "title": "Heavy Artillery",
        "category": "Volume",
        "tier": "diamond",
        "icon": "🚀",
        "target": "50,000 kg Lifetime Volume",
        "current": f"{int(total_vol)} {unit}",
        "achieved": heavy_artillery,
        "progress": min(100, int((total_vol / 50000.0) * 100)) if total_vol else 0
    })

    # 10. Workout Consistency Total Count Badges
    total_workouts = stats.get("total_workouts", 0)
    consistency_levels = [
        ("first_rep", "First Rep", "1 Workout Completed", 1, "🌱", "bronze"),
        ("consistency_10", "10-Session Grinder", "10 Workouts Logged", 10, "🔥", "silver"),
        ("iron_devotee_25", "Iron Devotee", "25 Workouts Logged", 25, "⚔️", "gold"),
        ("titan_50", "Half-Century Titan", "50 Workouts Logged", 50, "👑", "diamond"),
        ("centurion_100", "Century Club", "100 Workouts Logged", 100, "💎", "diamond")
    ]
    for m_id, title, desc, threshold, emoji, tier in consistency_levels:
        achieved = total_workouts >= threshold
        milestones.append({
            "id": m_id,
            "title": title,
            "category": "Consistency",
            "tier": tier,
            "icon": emoji,
            "target": f"{threshold} Workouts",
            "current": f"{total_workouts} Workouts",
            "achieved": achieved,
            "progress": min(100, int((total_workouts / threshold) * 100)) if total_workouts else 0
        })

    return milestones

def calculate_step_metrics(steps: int, height_cm: float = 175.0, weight_val: float = 75.0, unit: str = "kg", step_goal: int = 10000) -> dict:
    """
    Calculates distance, calories burned, and active walking time from step count.
    - Stride length: approx 0.414 * height_cm (in meters).
    - Distance: (steps * stride_length_m) / 1000 in km (or converted to miles if unit is lbs).
    - Calories: standard MET walking formula approx 0.045 kcal/step adjusted by body weight.
    - Active time: brisk walking averages ~105 steps/min.
    """
    steps = max(0, int(steps or 0))
    height_cm = float(height_cm or 175.0)
    
    # Weight in kg for calorie physics
    weight_kg = float(weight_val or 75.0)
    if unit == "lbs":
        weight_kg = weight_kg / 2.20462

    # Stride length in meters
    stride_m = max(0.5, min(1.0, (height_cm * 0.414) / 100.0))
    distance_km = round((steps * stride_m) / 1000.0, 2)
    distance_miles = round(distance_km * 0.621371, 2)

    # Calorie calculation: walking burns roughly 0.045 kcal/step for a 75kg person
    calorie_multiplier = 0.045 * (weight_kg / 75.0)
    calories_burned = round(steps * calorie_multiplier, 1)

    # Active minutes: 105 steps per minute average walking pace
    active_minutes = int(round(steps / 105.0))

    # Goal percentage
    goal = max(1000, int(step_goal or 10000))
    progress_pct = min(100, int(round((steps / goal) * 100)))

    return {
        "steps": steps,
        "goal": goal,
        "progress_pct": progress_pct,
        "distance_km": distance_km,
        "distance_miles": distance_miles,
        "display_distance": f"{distance_km} km" if unit == "kg" else f"{distance_miles} mi",
        "calories_burned": calories_burned,
        "active_minutes": active_minutes,
        "stride_length_cm": round(stride_m * 100, 1)
    }

def calculate_user_fitness_plan(height_cm: float, weight_val: float, unit: str = "kg", goal: str = "gain_weight") -> dict:
    """
    Computes BMR, TDEE, optimal macro splits, and customized training & dietary plans
    tailored to the user's biometric stats and selected goal:
    - 'gain_weight': Muscle hypertrophy, clean caloric surplus, heavy resistance split
    - 'lose_weight': Fat loss & definition, caloric deficit, high protein muscle sparing split
    - 'maintain_weight': Athletic body recomposition, isocaloric balance, functional fitness
    """
    height_cm = float(height_cm) if height_cm and float(height_cm) > 0 else 175.0
    weight_val = float(weight_val) if weight_val and float(weight_val) > 0 else 75.0
    goal = goal.strip().lower() if goal else "gain_weight"

    # Normalize weight to kg for physiological equations
    weight_kg = weight_val if unit == "kg" else weight_val * 0.453592
    height_m = height_cm / 100.0

    # 1. Biometric calculations
    bmi = round(weight_kg / (height_m * height_m), 1)
    if bmi < 18.5:
        bmi_category = "Lean / Underweight"
    elif bmi < 25.0:
        bmi_category = "Normal / Athletic"
    elif bmi < 30.0:
        bmi_category = "Overweight / Built"
    else:
        bmi_category = "High Mass"

    # Mifflin-St Jeor BMR Equation (assuming active adult reference)
    bmr = round(10.0 * weight_kg + 6.25 * height_cm - 5.0 * 25.0 + 5.0)
    tdee = round(bmr * 1.45) # Active gym trainee expenditure

    # 2. Plan differentiation based on goal
    if goal == "gain_weight":
        target_calories = tdee + 450
        target_protein = round(weight_kg * 2.0)
        target_fat = round(weight_kg * 0.9)
        target_carbs = max(50, round((target_calories - (target_protein * 4 + target_fat * 9)) / 4.0))

        title = "Muscle Hypertrophy & Clean Mass"
        badge = "🥩 Gain Weight"
        color = "#CCFF00"
        workout_split_name = "4-Day Upper / Lower Strength-Hypertrophy Split"
        workout_days = [
            {"day": "Day 1 (Mon)", "focus": "Upper Body Heavy Power", "routine": "Bench Press (4x5), Barbell Rows (4x6), Overhead Press (3x6), Pull-ups (3x8)"},
            {"day": "Day 2 (Tue)", "focus": "Lower Body Quad & Posterior", "routine": "Back Squat (4x6), Romanian Deadlifts (4x8), Leg Press (3x10), Standing Calves (4x12)"},
            {"day": "Day 3 (Wed)", "focus": "Active Recovery & Mobility", "routine": "Light 20-min mobility flow, foam rolling, dynamic hip openers"},
            {"day": "Day 4 (Thu)", "focus": "Upper Body Hypertrophy", "routine": "Incline Dumbbell Press (4x8-10), Lat Pulldown (4x10), Cable Flyes (3x12), Bicep/Tricep superset (3x12)"},
            {"day": "Day 5 (Fri)", "focus": "Lower Body Volume & Core", "routine": "Bulgarian Split Squats (3x10/leg), Leg Curls (4x12), Leg Extensions (3x15), Hanging Leg Raises (4x15)"},
            {"day": "Weekend", "focus": "Rest & Nutritional Replenishment", "routine": "Full rest, prioritize high carbohydrate and protein refueling"}
        ]
        nutrition_rules = [
            "Eat at a deliberate +400-500 kcal surplus to stimulate myofibrillar protein synthesis.",
            "Target 2.0g of protein per kg of bodyweight spaced across 4-5 balanced meals.",
            "Consume 60% of your daily carbs pre-workout and post-workout to maximize glycogen replenishment.",
            "Aim for 8 hours of sleep nightly: 90% of growth hormone is secreted during deep REM stages."
        ]

    elif goal == "lose_weight":
        target_calories = max(1400, tdee - 500)
        target_protein = round(weight_kg * 2.2) # High protein prevents muscle wasting during caloric deficit
        target_fat = round(weight_kg * 0.8)
        target_carbs = max(40, round((target_calories - (target_protein * 4 + target_fat * 9)) / 4.0))

        title = "Accelerated Fat Loss & Lean Definition"
        badge = "🔥 Lose Weight"
        color = "#FF3366"
        workout_split_name = "Push / Pull / Legs + Low-Impact Cardio Conditioning"
        workout_days = [
            {"day": "Day 1 (Mon)", "focus": "Heavy Push (Muscle Retention)", "routine": "Barbell Bench Press (4x6), Incline Dumbbells (3x8), Lateral Raises (4x12), Tricep Rope (3x12)"},
            {"day": "Day 2 (Tue)", "focus": "Heavy Pull + Core", "routine": "Deadlifts (4x5), Chest-Supported Rows (4x8), Pull-ups (3xMax), Ab Wheel Rollout (3x12)"},
            {"day": "Day 3 (Wed)", "focus": "Legs & Posterior Chain", "routine": "Back Squats (4x6), Walking Dumbbell Lunges (3x12), Hamstring Curls (4x12), Calf Raises (4x15)"},
            {"day": "Day 4 (Thu)", "focus": "Zone 2 Low-Impact Cardio", "routine": "35-45 min Incline Treadmill Walk (Heart Rate ~120-135 BPM) to burn fatty acids without muscle loss"},
            {"day": "Day 5 (Fri)", "focus": "Full Body Metabolic Density", "routine": "Dumbbell Thrusters, Kettlebell Swings, Cable Woodchoppers, Plank Holds (4 rounds for time)"},
            {"day": "Weekend", "focus": "Active Recovery & Step Target", "routine": "Walk outside, maintain 10,000 steps daily to keep NEAT (Non-Exercise Activity) high"}
        ]
        nutrition_rules = [
            "Maintain a steady 400-500 kcal deficit (expected fat loss: ~0.5kg to 0.7kg per week).",
            "Keep protein elevated at 2.2g/kg: this signals your body to burn fat while sparing lean muscle.",
            "Prioritize leafy greens, cruciferous vegetables, and lean white proteins for high satiety per calorie.",
            "Drink at least 3.5 liters of cold water daily to promote metabolic turnover."
        ]

    else: # maintain_weight
        target_calories = tdee
        target_protein = round(weight_kg * 1.8)
        target_fat = round(weight_kg * 0.9)
        target_carbs = max(50, round((target_calories - (target_protein * 4 + target_fat * 9)) / 4.0))

        title = "Body Recomposition & Peak Athletic Health"
        badge = "⚖️ Maintain Weight"
        color = "#00E5FF"
        workout_split_name = "3-4 Day Compound Athletic Conditioning"
        workout_days = [
            {"day": "Day 1 (Mon)", "focus": "Full Body Strength Foundation", "routine": "Barbell Squats (3x5), Bench Press (3x6), Pull-ups (3x8), Planks (3x60s)"},
            {"day": "Day 2 (Tue)", "focus": "Cardio & Movement Quality", "routine": "25-30 min interval cardio, rowing machine or outdoor jog, mobility drills"},
            {"day": "Day 3 (Wed)", "focus": "Upper Body Hypertrophy & Posture", "routine": "Overhead Press (4x6), Barbell Rows (4x8), Face Pulls (4x15), Dips (3x10)"},
            {"day": "Day 4 (Thu)", "focus": "Rest or Light Mobility", "routine": "Rest day, stretching, hydration, dynamic yoga or gentle walking"},
            {"day": "Day 5 (Fri)", "focus": "Lower Posterior Chain & Power", "routine": "Deadlifts (3x5), Bulgarian Splits (3x8/leg), Romanian Deadlifts (3x10), Core circuits"},
            {"day": "Weekend", "focus": "Outdoor Sports / Recreation", "routine": "Sports, hiking, swimming, or general active lifestyle with family and friends"}
        ]
        nutrition_rules = [
            "Eat at true maintenance calories to support intense training and hormonal equilibrium.",
            "Balance macros across 40% clean carbs, 30% lean protein, and 30% healthy anti-inflammatory fats.",
            "Focus on nutrient density: nuts, avocados, berries, wild fish, and diverse prebiotic fiber.",
            "Stay consistent with weigh-ins once a week to verify weight stability within ±1 kg."
        ]

    return {
        "goal_key": goal,
        "title": title,
        "badge": badge,
        "color": color,
        "bmi": bmi,
        "bmi_category": bmi_category,
        "bmr": bmr,
        "tdee": tdee,
        "targets": {
            "calories": target_calories,
            "protein": target_protein,
            "carbs": target_carbs,
            "fat": target_fat
        },
        "workout_split_name": workout_split_name,
        "workout_days": workout_days,
        "nutrition_rules": nutrition_rules
    }

def calculate_onboarding_targets(
    gender: str = "male",
    dob: str = None,
    age: int = None,
    height_cm: float = 175.0,
    weight: float = 75.0,
    goal_weight: float = None,
    core_goal: str = "gain_weight",
    fitness_objective: str = "tone",
    activity_level: str = "moderate",
    unit: str = "kg"
) -> dict:
    """
    MyFitnessPal-grade algorithmic engine for user onboarding.
    Calculates Mifflin-St Jeor BMR, TDEE, net caloric targets, optimal macronutrient splits,
    and daily hydration requirements based on user demographics and objectives.
    """
    from datetime import date, datetime

    # 1. Normalize units and biometrics
    unit = unit.lower() if unit in ["kg", "lbs"] else "kg"
    weight_val = float(weight) if weight and float(weight) > 0 else 75.0
    weight_kg = weight_val if unit == "kg" else weight_val * 0.453592

    goal_wt_val = float(goal_weight) if goal_weight and float(goal_weight) > 0 else None
    goal_weight_kg = (goal_wt_val if unit == "kg" else goal_wt_val * 0.453592) if goal_wt_val else None

    height_val = float(height_cm) if height_cm and float(height_cm) > 0 else 175.0
    # Sanity guard: if height entered in meters e.g. 1.75
    if height_val < 3.0:
        height_val = height_val * 100.0

    # 2. Determine age
    user_age = 25
    if age and int(age) > 0:
        user_age = int(age)
    elif dob:
        try:
            born = datetime.strptime(str(dob).strip(), "%Y-%m-%d").date()
            today = date.today()
            user_age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        except Exception:
            user_age = 25
    user_age = max(14, min(100, user_age))

    # 3. Mifflin-St Jeor Basal Metabolic Rate (BMR)
    # Men: BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) + 5
    # Women: BMR = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years) - 161
    is_female = str(gender).strip().lower() in ["female", "f", "woman"]
    if is_female:
        bmr = (10.0 * weight_kg) + (6.25 * height_val) - (5.0 * user_age) - 161.0
    else:
        bmr = (10.0 * weight_kg) + (6.25 * height_val) - (5.0 * user_age) + 5.0
    bmr = round(max(900.0, bmr))

    # 4. Activity Multiplier (TDEE)
    activity_map = {
        "sedentary": 1.20,      # Desk job, little or no exercise
        "light": 1.375,         # Light exercise / sports 1-3 days/week
        "moderate": 1.55,       # Moderate exercise / sports 3-5 days/week
        "very_active": 1.725    # Hard exercise / sports 6-7 days/week
    }
    act_mult = activity_map.get(str(activity_level).lower(), 1.55)
    tdee = round(bmr * act_mult)

    # 5. Core Goal Net Caloric Target Adjustment
    core_goal_clean = str(core_goal).lower().strip()
    if core_goal_clean in ["lose", "lose_weight", "fat_loss", "cut"]:
        core_goal_norm = "lose_weight"
        deficit = 500
        min_cals = 1200 if is_female else 1450
        daily_cals = max(min_cals, tdee - deficit)
    elif core_goal_clean in ["gain", "gain_weight", "bulk", "muscle_gain", "gain_muscle"]:
        core_goal_norm = "gain_weight"
        surplus = 450 if fitness_objective == "bulk" else 300
        daily_cals = tdee + surplus
    else:
        core_goal_norm = "maintain_weight"
        daily_cals = tdee

    # 6. Objective-Specific Macronutrient Optimization
    obj_clean = str(fitness_objective).lower().strip()
    if obj_clean in ["tone", "tone_up", "lean"]:
        obj_norm = "tone"
        # High protein for muscle tone & definition: 2.2 g/kg
        protein_g = round(weight_kg * 2.2)
        fat_g = round(weight_kg * 0.85)
    elif obj_clean in ["bulk", "bulk_up", "mass"]:
        obj_norm = "bulk"
        protein_g = round(weight_kg * 2.0)
        fat_g = round(weight_kg * 0.95)
    else: # strength / athletic
        obj_norm = "strength"
        protein_g = round(weight_kg * 2.0)
        fat_g = round(weight_kg * 0.90)

    # Bounds check on protein and fat
    protein_g = max(90, min(320, protein_g))
    fat_g = max(40, min(140, fat_g))

    # Carbohydrates supply the remainder of the daily calorie budget
    cals_from_pro_fat = (protein_g * 4) + (fat_g * 9)
    if cals_from_pro_fat >= daily_cals:
        daily_cals = cals_from_pro_fat + 200 # Ensure at least 50g carbs
    carbs_g = round(max(50, (daily_cals - cals_from_pro_fat) / 4.0))

    # Recalculate true calorie sum from rounded macros
    calculated_calories = (protein_g * 4) + (carbs_g * 4) + (fat_g * 9)

    # Macro Energy Percentages
    pct_protein = round((protein_g * 4 / calculated_calories) * 100)
    pct_carbs = round((carbs_g * 4 / calculated_calories) * 100)
    pct_fat = max(0, 100 - pct_protein - pct_carbs)

    # 7. Daily Hydration Target (ml)
    # Standard athletic guideline: ~35 ml per kg of bodyweight (+ activity adjustment)
    water_ml = round(max(2000, min(5000, weight_kg * 38)))
    water_cups = round(water_ml / 250.0, 1)

    # 8. BMI calculation
    height_m = height_val / 100.0
    bmi = round(weight_kg / (height_m * height_m), 1)

    return {
        "bmr": bmr,
        "tdee": tdee,
        "age": user_age,
        "bmi": bmi,
        "gender": "female" if is_female else "male",
        "core_goal": core_goal_norm,
        "fitness_objective": obj_norm,
        "activity_level": str(activity_level).lower(),
        "daily_calorie_target": calculated_calories,
        "daily_protein_target": protein_g,
        "daily_carbs_target": carbs_g,
        "daily_fat_target": fat_g,
        "water_goal_ml": water_ml,
        "water_goal_cups": water_cups,
        "macro_percentages": {
            "protein": pct_protein,
            "carbs": pct_carbs,
            "fat": pct_fat
        }
    }
