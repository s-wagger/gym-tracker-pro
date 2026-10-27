"""
Gym Tracker Pro - Demo Data Seeder
Populates a comprehensive demo athlete account with workouts,
meals, and personal records for immediate testing and presentation.
"""
from datetime import datetime, timedelta
from database import init_db
from models import User, WorkoutManager, NutritionManager

def seed():
    init_db()
    
    # Check if demo athlete exists
    user = User.get_by_username("demo_athlete")
    if not user:
        user = User.create(
            username="demo_athlete",
            email="demo@gymtracker.com",
            password="password123",
            display_name="Marcus Vance",
            unit_preference="kg"
        )
        user.update_profile("Marcus Vance", "kg", 2700, 185, 275, 75)
        print("Created demo user: demo_athlete (password: password123)")
    else:
        print("Demo user demo_athlete already exists.")

    today = datetime.now()

    # 1. Seed past 4 weeks of workouts
    sample_workouts = [
        {
            "days_ago": 18,
            "title": "Push Day Strength",
            "muscle": "Chest",
            "notes": "Felt explosive on bench press.",
            "sets": [
                {"set_number": 1, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 60, "reps": 10, "is_warmup": True},
                {"set_number": 2, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 85, "reps": 8, "is_warmup": False},
                {"set_number": 3, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 95, "reps": 5, "is_warmup": False},
                {"set_number": 4, "muscle_group": "Chest", "exercise_name": "Incline Dumbbell Press", "weight": 32, "reps": 8, "is_warmup": False},
                {"set_number": 5, "muscle_group": "Shoulders", "exercise_name": "Overhead Press", "weight": 55, "reps": 6, "is_warmup": False}
            ]
        },
        {
            "days_ago": 15,
            "title": "Pull Day Volume",
            "muscle": "Back",
            "notes": "Focused on back contraction and controlled eccentric.",
            "sets": [
                {"set_number": 1, "muscle_group": "Back", "exercise_name": "Deadlift", "weight": 100, "reps": 8, "is_warmup": True},
                {"set_number": 2, "muscle_group": "Back", "exercise_name": "Deadlift", "weight": 140, "reps": 5, "is_warmup": False},
                {"set_number": 3, "muscle_group": "Back", "exercise_name": "Deadlift", "weight": 160, "reps": 3, "is_warmup": False},
                {"set_number": 4, "muscle_group": "Back", "exercise_name": "Barbell Row", "weight": 80, "reps": 8, "is_warmup": False},
                {"set_number": 5, "muscle_group": "Back", "exercise_name": "Pull-ups", "weight": 0, "reps": 12, "is_warmup": False}
            ]
        },
        {
            "days_ago": 12,
            "title": "Leg Day Hypertrophy",
            "muscle": "Legs",
            "notes": "Heavy back squats into high volume leg press.",
            "sets": [
                {"set_number": 1, "muscle_group": "Legs", "exercise_name": "Back Squat", "weight": 70, "reps": 10, "is_warmup": True},
                {"set_number": 2, "muscle_group": "Legs", "exercise_name": "Back Squat", "weight": 110, "reps": 6, "is_warmup": False},
                {"set_number": 3, "muscle_group": "Legs", "exercise_name": "Back Squat", "weight": 130, "reps": 5, "is_warmup": False},
                {"set_number": 4, "muscle_group": "Legs", "exercise_name": "Leg Press", "weight": 220, "reps": 12, "is_warmup": False},
                {"set_number": 5, "muscle_group": "Legs", "exercise_name": "Romanian Deadlift", "weight": 100, "reps": 8, "is_warmup": False}
            ]
        },
        {
            "days_ago": 5,
            "title": "Push Day Heavy Singles & 1RM Test",
            "muscle": "Chest",
            "notes": "Hit new Bench PR! 105kg x 3 reps.",
            "sets": [
                {"set_number": 1, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 70, "reps": 8, "is_warmup": True},
                {"set_number": 2, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 95, "reps": 5, "is_warmup": False},
                {"set_number": 3, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 105, "reps": 3, "is_warmup": False},
                {"set_number": 4, "muscle_group": "Shoulders", "exercise_name": "Overhead Press", "weight": 62.5, "reps": 5, "is_warmup": False}
            ]
        },
        {
            "days_ago": 2,
            "title": "Deadlift & Pull Peak",
            "muscle": "Back",
            "notes": "Deadlift 180kg x 1 completed cleanly! 405 club entered.",
            "sets": [
                {"set_number": 1, "muscle_group": "Back", "exercise_name": "Deadlift", "weight": 110, "reps": 6, "is_warmup": True},
                {"set_number": 2, "muscle_group": "Back", "exercise_name": "Deadlift", "weight": 150, "reps": 3, "is_warmup": False},
                {"set_number": 3, "muscle_group": "Back", "exercise_name": "Deadlift", "weight": 180, "reps": 1, "is_warmup": False},
                {"set_number": 4, "muscle_group": "Back", "exercise_name": "Lat Pulldown", "weight": 75, "reps": 10, "is_warmup": False}
            ]
        },
        {
            "days_ago": 0, # Today
            "title": "Quad Domination & Squats",
            "muscle": "Legs",
            "notes": "Hit 140kg squat for 2 clean reps!",
            "sets": [
                {"set_number": 1, "muscle_group": "Legs", "exercise_name": "Back Squat", "weight": 80, "reps": 8, "is_warmup": True},
                {"set_number": 2, "muscle_group": "Legs", "exercise_name": "Back Squat", "weight": 120, "reps": 5, "is_warmup": False},
                {"set_number": 3, "muscle_group": "Legs", "exercise_name": "Back Squat", "weight": 140, "reps": 2, "is_warmup": False},
                {"set_number": 4, "muscle_group": "Legs", "exercise_name": "Bulgarian Split Squat", "weight": 24, "reps": 10, "is_warmup": False}
            ]
        }
    ]

    for w in sample_workouts:
        date_str = (today - timedelta(days=w["days_ago"])).strftime("%Y-%m-%d")
        WorkoutManager.log_workout_session(user.id, w["title"], date_str, w["notes"], w["sets"])

    # 2. Seed today's nutrition
    today_str = today.strftime("%Y-%m-%d")
    NutritionManager.log_meal(user.id, today_str, "Breakfast", "4 Scrambled Eggs + 2 Slices Sourdough", 520, 36, 44, 22)
    NutritionManager.log_meal(user.id, today_str, "Lunch", "250g Grilled Chicken Breast, Jasmine Rice & Broccoli", 680, 62, 75, 12)
    NutritionManager.log_meal(user.id, today_str, "Snack", "Whey Protein Isolate with Almond Milk & Banana", 310, 32, 35, 4)
    NutritionManager.log_meal(user.id, today_str, "Dinner", "200g Lean Sirloin Steak & Roasted Baby Potatoes", 650, 48, 45, 24)

    print("Demo data seeded successfully for 'demo_athlete'!")

if __name__ == "__main__":
    seed()
