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
        "category": "Elite Honor",
        "icon": "🏆",
        "target": "1,000 lbs (454 kg) Total",
        "current": f"{round(total_big_three_lbs if unit == 'lbs' else total_big_three_kg, 1)} {unit}",
        "achieved": one_thousand_club_achieved,
        "progress": min(100, int((total_big_three_lbs / 1000.0) * 100)) if total_big_three_lbs else 0
    })

    # 5. Workout Consistency Badges
    total_workouts = stats.get("total_workouts", 0)
    consistency_levels = [
        ("first_rep", "First Rep", "1 Workout Completed", 1, "🌱"),
        ("consistency_10", "10-Session Grinder", "10 Workouts Logged", 10, "🔥"),
        ("iron_devotee_25", "Iron Devotee", "25 Workouts Logged", 25, "⚔️"),
        ("titan_50", "Half-Century Titan", "50 Workouts Logged", 50, "👑"),
        ("centurion_100", "Century Club", "100 Workouts Logged", 100, "💎")
    ]
    for m_id, title, desc, threshold, emoji in consistency_levels:
        achieved = total_workouts >= threshold
        milestones.append({
            "id": m_id,
            "title": title,
            "category": "Consistency",
            "icon": emoji,
            "target": f"{threshold} Workouts",
            "current": f"{total_workouts} Workouts",
            "achieved": achieved,
            "progress": min(100, int((total_workouts / threshold) * 100)) if total_workouts else 0
        })

    return milestones
