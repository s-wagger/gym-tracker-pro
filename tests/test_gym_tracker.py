"""
Gym Tracker Pro - Comprehensive Automated Test Suite
Tests mathematical formulas, database integrity, bcrypt security,
workout multi-set logging, auto-PR detection, macro calculations,
CSV export engines, and PWA endpoints.
"""
import unittest
import os
import io
import json
import zipfile
import sqlite3

# Set test database before importing application modules
os.environ["SECRET_KEY"] = "test-secret-key-12345"
from app import app
from database import init_db, get_db
from models import (
    User, WorkoutManager, NutritionManager, AnalyticsManager,
    ExportManager, StepManager, SubscriptionManager, TemplateManager,
    WaterManager, BarcodeManager
)
from formulas import (
    calculate_epley_1rm, calculate_brzycki_1rm,
    calculate_lombardi_1rm, get_training_zones, evaluate_milestones,
    calculate_user_fitness_plan, calculate_step_metrics,
    calculate_onboarding_targets, calculate_barbell_plates
)

class GymTrackerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Clean database before each test
        with get_db() as conn:
            conn.execute("DELETE FROM custom_barcodes")
            conn.execute("DELETE FROM onboarding_profiles")
            conn.execute("DELETE FROM daily_water")
            conn.execute("DELETE FROM workout_templates")
            conn.execute("DELETE FROM subscription_requests")
            conn.execute("DELETE FROM daily_steps")
            conn.execute("DELETE FROM workout_sets")
            conn.execute("DELETE FROM workout_sessions")
            conn.execute("DELETE FROM nutrition_entries")
            conn.execute("DELETE FROM personal_records")
            conn.execute("DELETE FROM users")

    # ---------------------------------------------------------
    # 1. Mathematical 1RM & Formulas Unit Tests
    # ---------------------------------------------------------
    def test_epley_1rm_single_rep(self):
        """When reps == 1, 1RM should equal the weight lifted exactly."""
        self.assertEqual(calculate_epley_1rm(100.0, 1), 100.0)
        self.assertEqual(calculate_epley_1rm(140.0, 1), 140.0)

    def test_epley_1rm_standard_formula(self):
        """1RM = W * (1 + R / 30)"""
        # 100kg for 5 reps: 100 * (1 + 5/30) = 100 * 1.1666... = 116.7
        res = calculate_epley_1rm(100.0, 5)
        self.assertAlmostEqual(res, 116.7, places=1)

        # 80kg for 10 reps: 80 * (1 + 10/30) = 80 * 1.333... = 106.7
        res = calculate_epley_1rm(80.0, 10)
        self.assertAlmostEqual(res, 106.7, places=1)

    def test_alternative_formulas(self):
        """Brzycki and Lombardi formulas should compute expected positive numbers."""
        brz = calculate_brzycki_1rm(100.0, 5)
        lomb = calculate_lombardi_1rm(100.0, 5)
        self.assertGreater(brz, 100.0)
        self.assertGreater(lomb, 100.0)

    def test_training_zones_breakdown(self):
        """Verify standard training zones: 50%, 75%, 85%, 90% as required by brief."""
        zones = get_training_zones(100.0, unit="kg")
        self.assertEqual(len(zones), 9)

        percentages = [z["percentage"] for z in zones]
        self.assertIn(50, percentages)
        self.assertIn(75, percentages)
        self.assertIn(85, percentages)
        self.assertIn(90, percentages)
        self.assertIn(100, percentages)

        # 90% zone on 100kg 1RM should be exactly 90.0 kg
        z90 = next(z for z in zones if z["percentage"] == 90)
        self.assertEqual(z90["weight"], 90.0)

        # 85% zone on 100kg 1RM should be 85.0 kg
        z85 = next(z for z in zones if z["percentage"] == 85)
        self.assertEqual(z85["weight"], 85.0)

    def test_milestone_evaluations(self):
        """Verify milestone club achievements (100kg Bench, 140kg Squat, 1000lb club)."""
        stats_achieved = {
            "key_prs": {
                "Bench Press": {"weight": 110.0},
                "Back Squat": {"weight": 160.0},
                "Deadlift": {"weight": 200.0}
            },
            "total_workouts": 30
        }
        milestones = evaluate_milestones(stats_achieved, unit="kg")
        bench_club = next(m for m in milestones if m["id"] == "bench_club_100")
        squat_club = next(m for m in milestones if m["id"] == "squat_club_140")
        deadlift_club = next(m for m in milestones if m["id"] == "deadlift_club_180")
        thousand_club = next(m for m in milestones if m["id"] == "thousand_lb_club")
        consistency_25 = next(m for m in milestones if m["id"] == "iron_devotee_25")

        self.assertTrue(bench_club["achieved"])
        self.assertTrue(squat_club["achieved"])
        self.assertTrue(deadlift_club["achieved"])
        self.assertTrue(thousand_club["achieved"])
        self.assertTrue(consistency_25["achieved"])

    # ---------------------------------------------------------
    # 2. User Authentication & Security Tests (M1)
    # ---------------------------------------------------------
    def test_user_creation_and_bcrypt_hashing(self):
        user = User.create("powerlifter", "lifter@test.com", "strongpassword123", "Power Lifter", "kg")
        self.assertIsNotNone(user.id)
        self.assertTrue(user.verify_password("strongpassword123"))
        self.assertFalse(user.verify_password("wrongpassword"))

        # Check that password in DB is not plain text
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user.id,))
            pw_hash = cursor.fetchone()["password_hash"]
            self.assertNotEqual(pw_hash, "strongpassword123")
            self.assertTrue(pw_hash.startswith("$2b$") or pw_hash.startswith("$2a$"))

    def test_user_profile_and_password_update(self):
        user = User.create("athlete1", "athlete1@test.com", "pass1234")
        user.update_profile("Champion Athlete", "lbs", 2800, 180, 300, 80)
        
        updated = User.get_by_id(user.id)
        self.assertEqual(updated.display_name, "Champion Athlete")
        self.assertEqual(updated.unit_preference, "lbs")
        self.assertEqual(updated.daily_calorie_target, 2800)
        self.assertEqual(updated.daily_protein_target, 180)

        # Update password
        user.update_password("newsecretpass567")
        self.assertTrue(user.verify_password("newsecretpass567"))
        self.assertFalse(user.verify_password("pass1234"))

    # ---------------------------------------------------------
    # 3. Workout Logging & Automatic PR Detection Tests (M4 & M7)
    # ---------------------------------------------------------
    def test_workout_logging_and_auto_pr_detection(self):
        user = User.create("bench_king", "bench@test.com", "pass1234")
        
        # 1. Log first session (Bench Press 100kg x 5)
        sets1 = [
            {"set_number": 1, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 60, "reps": 10, "is_warmup": True},
            {"set_number": 2, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 90, "reps": 8, "is_warmup": False},
            {"set_number": 3, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 100, "reps": 5, "is_warmup": False}
        ]
        res1 = WorkoutManager.log_workout_session(user.id, "Heavy Chest Day", "2026-10-20", "Felt strong", sets1)
        self.assertIsNotNone(res1["session_id"])
        self.assertEqual(len(res1["new_prs"]), 1)
        self.assertEqual(res1["new_prs"][0]["exercise"], "Bench Press")
        self.assertEqual(res1["new_prs"][0]["weight"], 100.0)

        # Check personal records table
        prs = AnalyticsManager.get_personal_records(user.id)
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["max_weight"], 100.0)
        self.assertEqual(prs[0]["estimated_1rm"], 116.7)

        # 2. Log second session with higher weight (Bench Press 105kg x 5) -> Should detect new PR!
        sets2 = [
            {"set_number": 1, "muscle_group": "Chest", "exercise_name": "Bench Press", "weight": 105, "reps": 5, "is_warmup": False}
        ]
        res2 = WorkoutManager.log_workout_session(user.id, "Chest PR Day", "2026-10-25", "Hit new peak", sets2)
        self.assertEqual(len(res2["new_prs"]), 1)
        self.assertEqual(res2["new_prs"][0]["weight"], 105.0)

        # PR table should be updated to 105kg
        prs_updated = AnalyticsManager.get_personal_records(user.id)
        self.assertEqual(prs_updated[0]["max_weight"], 105.0)

        # 3. Retrieve workouts with filter
        history = WorkoutManager.get_user_workouts(user.id, muscle_group="Chest")
        self.assertEqual(len(history), 2)
        self.assertTrue(history[0]["has_pr"])

    # ---------------------------------------------------------
    # 4. Nutrition Logging & Macro Targets Tests (M5)
    # ---------------------------------------------------------
    def test_nutrition_logging_and_totals(self):
        user = User.create("diet_pro", "diet@test.com", "pass1234")
        today = "2026-10-26"

        # Log Breakfast
        NutritionManager.log_meal(user.id, today, "Breakfast", "Oatmeal with Whey", 450, 35, 60, 8)
        # Log Lunch
        NutritionManager.log_meal(user.id, today, "Lunch", "Chicken Breast & Sweet Potato", 600, 55, 65, 10)
        # Log Dinner
        entry_id = NutritionManager.log_meal(user.id, today, "Dinner", "Salmon Fillet & Rice", 700, 45, 50, 25)

        summary = NutritionManager.get_daily_nutrition(user.id, today)
        self.assertEqual(summary["totals"]["calories"], 1750.0)
        self.assertEqual(summary["totals"]["protein"], 135.0)
        self.assertEqual(summary["totals"]["carbs"], 175.0)
        self.assertEqual(summary["totals"]["fat"], 43.0)

        # Test delete meal item
        NutritionManager.delete_meal(entry_id, user.id)
        summary_after_del = NutritionManager.get_daily_nutrition(user.id, today)
        self.assertEqual(summary_after_del["totals"]["calories"], 1050.0)

    # ---------------------------------------------------------
    # 5. Data Export Subsystem Tests (M8)
    # ---------------------------------------------------------
    def test_csv_export_generation(self):
        user = User.create("exporter", "export@test.com", "pass1234")
        
        # Add workout and nutrition
        WorkoutManager.log_workout_session(user.id, "Back Workout", "2026-10-26", "", [
            {"set_number": 1, "muscle_group": "Back", "exercise_name": "Deadlift", "weight": 140, "reps": 5, "is_warmup": False}
        ])
        NutritionManager.log_meal(user.id, "2026-10-26", "Lunch", "Steak", 500, 45, 0, 30)

        # Verify export data structures
        workouts_data = ExportManager.get_workouts_csv_data(user.id)
        self.assertEqual(len(workouts_data), 1)
        self.assertEqual(workouts_data[0]["exercise_name"], "Deadlift")
        self.assertEqual(workouts_data[0]["weight"], 140.0)

        nutrition_data = ExportManager.get_nutrition_csv_data(user.id)
        self.assertEqual(len(nutrition_data), 1)
        self.assertEqual(nutrition_data[0]["food_name"], "Steak")

        prs_data = ExportManager.get_prs_csv_data(user.id)
        self.assertEqual(len(prs_data), 1)
        self.assertEqual(prs_data[0]["exercise_name"], "Deadlift")

    # ---------------------------------------------------------
    # 6. PWA & Web App Manifest Endpoints Tests
    # ---------------------------------------------------------
    def test_pwa_manifest_json(self):
        res = self.client.get("/manifest.json")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data["name"], "Gym Tracker Pro")
        self.assertEqual(data["short_name"], "GymTracker")
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["background_color"], "#F8FAFC")
        self.assertEqual(data["theme_color"], "#0066FF")
        self.assertGreaterEqual(len(data["icons"]), 2)
        self.assertIn("shortcuts", data)
        shortcut_names = [s["name"] for s in data["shortcuts"]]
        self.assertIn("Log Workout", shortcut_names)
        self.assertIn("Log Meal", shortcut_names)
        self.assertIn("Step Counter", shortcut_names)

    def test_pwa_service_worker(self):
        res = self.client.get("/sw.js")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"gymtracker", res.data)
        self.assertEqual(res.headers.get("Service-Worker-Allowed"), "/")

    def test_pwa_offline_page(self):
        res = self.client.get("/offline.html")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"You're Offline", res.data)

    # ---------------------------------------------------------
    # 7. Personalized Fitness Plans & AI Camera Tests
    # ---------------------------------------------------------
    def test_personalized_fitness_plans(self):
        # 1. Gain Weight test
        plan_gain = calculate_user_fitness_plan(height_cm=180, weight_val=75, unit="kg", goal="gain_weight")
        self.assertEqual(plan_gain["bmi"], 23.1)
        self.assertGreater(plan_gain["targets"]["calories"], plan_gain["tdee"])
        self.assertEqual(plan_gain["targets"]["protein"], 150) # 75kg * 2.0

        # 2. Lose Weight test
        plan_loss = calculate_user_fitness_plan(height_cm=180, weight_val=85, unit="kg", goal="lose_weight")
        self.assertLess(plan_loss["targets"]["calories"], plan_loss["tdee"])
        self.assertEqual(plan_loss["targets"]["protein"], 187) # 85kg * 2.2

        # 3. Maintain Weight test
        plan_maint = calculate_user_fitness_plan(height_cm=175, weight_val=70, unit="kg", goal="maintain_weight")
        self.assertEqual(plan_maint["targets"]["calories"], plan_maint["tdee"])
        self.assertEqual(plan_maint["targets"]["protein"], 126) # 70kg * 1.8

    def test_ai_food_camera_scanner(self):
        user = User.create("cameratester", "camera@test.com", "pass1234")
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # Test scan with base64 dummy image
        dummy_b64 = "data:image/jpeg;base64," + "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" * 5
        res = self.client.post("/api/nutrition/scan-meal", json={"image_data": dummy_b64})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("calories", data["analysis"])
        self.assertIn("protein", data["analysis"])
        self.assertGreater(data["analysis"]["calories"], 0)

    # ---------------------------------------------------------
    # 8. Pedometer & Step Counter Subsystem Tests
    # ---------------------------------------------------------
    def test_step_metrics_formula(self):
        """Verify biomechanical calculation of stride, distance, MET calories, and active minutes."""
        metrics = calculate_step_metrics(
            steps=10000,
            height_cm=175.0,
            weight_val=75.0,
            unit="kg",
            step_goal=10000
        )
        self.assertEqual(metrics["steps"], 10000)
        self.assertGreater(metrics["distance_km"], 6.5)
        self.assertLess(metrics["distance_km"], 8.5)
        self.assertGreater(metrics["calories_burned"], 300)
        self.assertGreater(metrics["active_minutes"], 70)
        self.assertEqual(metrics["progress_pct"], 100)

    def test_step_manager_and_endpoints(self):
        """Verify logging steps, updating daily totals, retrieving history, and CSV export."""
        user = User.create("stepper", "step@test.com", "pass1234")
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 1. Access /steps page
        res_page = self.client.get("/steps")
        self.assertEqual(res_page.status_code, 200)
        self.assertIn(b"Smart Pedometer", res_page.data)

        # 2. Sync steps via POST /api/steps/sync
        res_sync = self.client.post("/api/steps/sync", json={
            "steps": 4500,
            "date": today_str
        })
        self.assertEqual(res_sync.status_code, 200)
        sync_data = json.loads(res_sync.data)
        self.assertTrue(sync_data["success"])
        self.assertEqual(sync_data["data"]["steps"], 4500)
        self.assertGreater(sync_data["data"]["distance_km"], 2.0)

        # 3. Add incremental steps via POST /api/steps/add
        res_add = self.client.post("/api/steps/add", json={
            "delta": 1000,
            "date": today_str
        })
        self.assertEqual(res_add.status_code, 200)
        add_data = json.loads(res_add.data)
        self.assertTrue(add_data["success"])
        self.assertEqual(add_data["data"]["steps"], 5500)

        # 4. Fetch today's steps via GET /api/steps/today
        res_today = self.client.get("/api/steps/today")
        self.assertEqual(res_today.status_code, 200)
        today_data = json.loads(res_today.data)
        self.assertEqual(today_data["data"]["steps"], 5500)

        # 5. Update daily step goal via POST /api/steps/goal
        res_goal = self.client.post("/api/steps/goal", json={"goal": 12000})
        self.assertEqual(res_goal.status_code, 200)
        goal_data = json.loads(res_goal.data)
        self.assertTrue(goal_data["success"])
        self.assertEqual(goal_data["goal"], 12000)

        # 6. Verify 7-day history via GET /api/steps/history
        res_hist = self.client.get("/api/steps/history")
        self.assertEqual(res_hist.status_code, 200)
        hist_data = json.loads(res_hist.data)
        self.assertEqual(len(hist_data["history"]), 7)

        # 7. Verify Steps CSV export
        res_csv = self.client.get("/export/steps/csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn(b"Steps,Distance (km)", res_csv.data)
        self.assertIn(b"5500", res_csv.data)

        # 8. Verify Steps in ExportManager
        steps_csv_data = ExportManager.get_steps_csv_data(user.id)
        self.assertEqual(len(steps_csv_data), 1)
        self.assertEqual(steps_csv_data[0]["steps"], 5500)

    # ---------------------------------------------------------
    # 9. Subscription, 7-Day Free Trial & Paywall Subsystem Tests
    # ---------------------------------------------------------
    def test_7_day_free_trial_and_paywall(self):
        """
        Verify:
        - New user starts with 7-day free trial (1 week) and full Pro feature access.
        - When trial expires, pro features (AI Camera, 1RM, CSV Exports) are gated.
        - Core features (Workout logging, pedometer, manual nutrition, PRs) remain 100% accessible.
        - Direct Bank Transfer (UBL IBAN) payment submission (Rs. 500/mo) & owner approval activates Pro.
        - Owner has permanent lifetime VIP access.
        """
        # 1. New user registration check
        user = User.create("subscriber", "sub@test.com", "pass1234")
        self.assertEqual(user.subscription_status, "trial")
        self.assertGreaterEqual(user.trial_days_left, 6)
        self.assertLessEqual(user.trial_days_left, 7)
        self.assertTrue(user.has_pro_access)

        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # During free trial: /1rm and /export are accessible
        res_1rm = self.client.get("/1rm")
        self.assertEqual(res_1rm.status_code, 200)

        res_export = self.client.get("/export")
        self.assertEqual(res_export.status_code, 200)

        # 2. Simulate 7-day Free Trial Expiration
        user.set_subscription("trial", days=-1) # Expired
        self.assertEqual(user.trial_days_left, 0)
        self.assertFalse(user.has_pro_access)

        # Pro feature 1: AI Camera Scanner -> Expect 403 Forbidden
        dummy_b64 = "data:image/jpeg;base64," + "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" * 5
        res_scan = self.client.post("/api/nutrition/scan-meal", json={"image_data": dummy_b64})
        self.assertEqual(res_scan.status_code, 403)
        scan_data = json.loads(res_scan.data)
        self.assertTrue(scan_data["is_pro_required"])

        # Pro feature 2: 1RM Engine -> Redirects to /subscription
        res_1rm_locked = self.client.get("/1rm")
        self.assertEqual(res_1rm_locked.status_code, 302)
        self.assertIn("/subscription", res_1rm_locked.headers["Location"])

        # Pro feature 3: CSV Export -> Redirects to /subscription
        res_export_locked = self.client.get("/export")
        self.assertEqual(res_export_locked.status_code, 302)
        self.assertIn("/subscription", res_export_locked.headers["Location"])

        # 3. VERIFY CORE FREE FEATURES REMAIN 100% ACCESSIBLE AFTER TRIAL EXPIRES
        # Core 1: Workout Logging
        res_workout = self.client.post("/api/workouts/log", json={
            "title": "Leg Day",
            "date": "2026-11-05",
            "notes": "Good squats",
            "sets": [{"muscle_group": "Legs", "exercise_name": "Back Squat", "weight": 120, "reps": 8, "rpe": 8, "is_warmup": False}]
        })
        self.assertEqual(res_workout.status_code, 200)

        # Core 2: Pedometer & Steps
        res_step = self.client.post("/api/steps/sync", json={"steps": 3000, "date": "2026-11-05"})
        self.assertEqual(res_step.status_code, 200)

        # Core 3: Manual Nutrition Logging
        res_diet = self.client.post("/api/nutrition/log", json={
            "date": "2026-11-05",
            "meal_type": "Lunch",
            "food_name": "Chicken and Rice",
            "calories": 500,
            "protein": 40,
            "carbs": 60,
            "fat": 10
        })
        self.assertEqual(res_diet.status_code, 200)

        # Core 4: PRs & Analytics
        res_analytics = self.client.get("/analytics")
        self.assertEqual(res_analytics.status_code, 200)

        # 4. Bank Transfer Payment Verification Request (UBL IBAN) - Rs. 500/month
        res_sub_submit = self.client.post("/api/subscription/submit", json={
            "sender_name": "Hamza Ali",
            "transaction_ref": "UBL-TXN-984210",
            "plan_name": "Pro Monthly - Rs. 500",
            "amount_paid": 500,
            "notes": "Paid via UBL Netbanking to PK58UNIL0109000321329705"
        })
        self.assertEqual(res_sub_submit.status_code, 200)
        sub_resp = json.loads(res_sub_submit.data)
        self.assertTrue(sub_resp["success"])
        req_id = sub_resp["request_id"]

        # 5. Owner Approval Process
        # Non-owner cannot approve
        res_unauth_approve = self.client.post("/api/admin/subscription/approve", json={"request_id": req_id})
        self.assertEqual(res_unauth_approve.status_code, 403)

        # Create Owner and claim VIP status
        owner = User.create("app_owner", "owner@gymtracker.com", "ownerpass")
        owner.grant_owner()
        self.assertTrue(owner.is_owner_user)
        self.assertTrue(owner.has_pro_access)

        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(owner.id)

        # Owner approves the subscriber's payment request
        res_approve = self.client.post("/api/admin/subscription/approve", json={"request_id": req_id})
        self.assertEqual(res_approve.status_code, 200)

        # Verify subscriber is now Pro and features are unlocked
        refreshed_user = User.get_by_id(user.id)
        self.assertEqual(refreshed_user.subscription_status, "pro")
        self.assertTrue(refreshed_user.has_pro_access)

    # ---------------------------------------------------------
    # 10. Single Daily Session & Flexible Equipment Weight Tests
    # ---------------------------------------------------------
    def test_single_daily_session_multi_exercise_grouping(self):
        """
        Verify that multiple exercises logged on the same date (e.g., Row -> Incline Bench -> Lat Pulldown)
        are consolidated under a single workout_sessions record with aggregated volume and summary.
        """
        user = User.create("lifter_session", "lifter@test.com", "pass1234")
        date_str = "2026-11-06"

        # 1. Log First Exercise (Row) under session "Chest and Back"
        res1 = WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Chest and Back",
            date=date_str,
            notes="Morning session",
            sets_data=[
                {"muscle_group": "Back", "exercise_name": "Barbell Row", "set_number": 1, "weight": 70, "reps": 10, "rpe": 8, "is_warmup": False, "equipment_type": "plates", "equipment_details": "2 plates @ 25kg + 20kg bar"},
                {"muscle_group": "Back", "exercise_name": "Barbell Row", "set_number": 2, "weight": 80, "reps": 8, "rpe": 8.5, "is_warmup": False, "equipment_type": "plates", "equipment_details": "2 plates @ 30kg + 20kg bar"}
            ]
        )
        session_id_1 = res1["session_id"]

        # 2. Add Next Exercise (Incline Bench) under the same daily session
        res2 = WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Chest and Back",
            date=date_str,
            notes="Added chest incline",
            sets_data=[
                {"muscle_group": "Chest", "exercise_name": "Incline Dumbbell Press", "set_number": 1, "weight": 60, "reps": 10, "rpe": 8, "is_warmup": False, "equipment_type": "dumbbell", "equipment_details": "2x 30kg (Total 60kg)"},
                {"muscle_group": "Chest", "exercise_name": "Incline Dumbbell Press", "set_number": 2, "weight": 60, "reps": 8, "rpe": 9, "is_warmup": False, "equipment_type": "dumbbell", "equipment_details": "2x 30kg (Total 60kg)"}
            ]
        )
        session_id_2 = res2["session_id"]

        # Sessions must be grouped into the exact same database session row
        self.assertEqual(session_id_1, session_id_2)

        # Retrieve user workouts and verify consolidated session
        workouts = WorkoutManager.get_user_workouts(user.id, date_str=date_str)
        self.assertEqual(len(workouts), 1)

        sess = workouts[0]
        self.assertEqual(sess["title"], "Chest and Back")
        self.assertEqual(len(sess["sets"]), 4) # 2 rows + 2 incline presses
        self.assertIn("Barbell Row", sess["exercises_summary"])
        self.assertIn("Incline Dumbbell Press", sess["exercises_summary"])
        # Total volume: (70*10) + (80*8) + (60*10) + (60*8) = 700 + 640 + 600 + 480 = 2420
        self.assertEqual(sess["total_volume"], 2420)

    def test_equipment_weight_and_manual_override(self):
        """
        Verify flexible equipment weight calculator and manual override persistence:
        - Dumbbell: stores single weight details and effective total
        - Machine Stack: stores plate math details and effective total
        - Direct / Manual Override: stores override total weight and detail tag
        """
        user = User.create("equip_user", "equip@test.com", "pass1234")
        date_str = "2026-11-07"

        res = WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Full Body Power",
            date=date_str,
            notes="Testing equipment types",
            sets_data=[
                # Dumbbell: single DB = 22.5kg per arm -> total = 45kg
                {"muscle_group": "Arms", "exercise_name": "Hammer Curl", "set_number": 1, "weight": 45.0, "reps": 10, "rpe": 8, "is_warmup": False, "equipment_type": "dumbbell", "equipment_details": "2x 22.5kg (Total 45kg)"},
                # Machine Stack: 6 plates @ 10kg ea -> total = 60kg
                {"muscle_group": "Back", "exercise_name": "Lat Pulldown", "set_number": 1, "weight": 60.0, "reps": 12, "rpe": 8, "is_warmup": False, "equipment_type": "machine", "equipment_details": "6 plates @ 10kg"},
                # Manual Override on Barbell: user typed 85kg directly
                {"muscle_group": "Chest", "exercise_name": "Bench Press", "set_number": 1, "weight": 85.0, "reps": 6, "rpe": 9, "is_warmup": False, "equipment_type": "plates", "equipment_details": "Plates (Manual Total: 85kg, 2x30kg + bar)"}
            ]
        )
        self.assertTrue(res["session_id"] > 0)

        workouts = WorkoutManager.get_user_workouts(user.id, date_str=date_str)
        self.assertEqual(len(workouts), 1)
        sets = workouts[0]["sets"]
        self.assertEqual(len(sets), 3)

        # Check DB columns persisted
        set_db = next(s for s in sets if s["exercise_name"] == "Hammer Curl")
        self.assertEqual(set_db["equipment_type"], "dumbbell")
        self.assertEqual(set_db["equipment_details"], "2x 22.5kg (Total 45kg)")
        self.assertEqual(set_db["weight"], 45.0)

        set_mach = next(s for s in sets if s["exercise_name"] == "Lat Pulldown")
        self.assertEqual(set_mach["equipment_type"], "machine")
        self.assertEqual(set_mach["equipment_details"], "6 plates @ 10kg")
        self.assertEqual(set_mach["weight"], 60.0)

        set_override = next(s for s in sets if s["exercise_name"] == "Bench Press")
        self.assertEqual(set_override["equipment_type"], "plates")
        self.assertIn("Manual Total: 85kg", set_override["equipment_details"])
        self.assertEqual(set_override["weight"], 85.0)

    # ---------------------------------------------------------
    # 11. Dynamic All-Exercise PR Tracking & Universal Progression
    # ---------------------------------------------------------
    def test_dynamic_all_exercise_pr_tracking_and_progression_curves(self):
        """
        Verify that PR tracking is not limited to 4 hardcoded lifts, but tracks peak weight,
        set volume, and 1RM for any exercise (e.g. Incline Dumbbell Press, Cable Crossover),
        and feeds universal progression time-series.
        """
        user = User.create("pr_lifter", "prlifter@test.com", "pass1234")

        # Day 1: Log Incline Dumbbell Press (30kg, 10 reps) & Cable Crossover (20kg, 12 reps)
        res1 = WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Chest Hypertrophy",
            date="2026-11-01",
            notes="Session 1",
            sets_data=[
                {"muscle_group": "Chest", "exercise_name": "Incline Dumbbell Press", "set_number": 1, "weight": 30.0, "reps": 10, "is_warmup": False, "equipment_type": "dumbbell"},
                {"muscle_group": "Chest", "exercise_name": "Cable Crossover", "set_number": 1, "weight": 20.0, "reps": 12, "is_warmup": False, "equipment_type": "machine"}
            ]
        )
        self.assertEqual(len(res1["new_prs"]), 2)

        # Day 2: Beat Incline Dumbbell Press (34kg, 8 reps) -> Higher weight & 1RM
        res2 = WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Chest Hypertrophy 2",
            date="2026-11-05",
            notes="Session 2",
            sets_data=[
                {"muscle_group": "Chest", "exercise_name": "Incline Dumbbell Press", "set_number": 1, "weight": 34.0, "reps": 8, "is_warmup": False, "equipment_type": "dumbbell"}
            ]
        )
        self.assertEqual(len(res2["new_prs"]), 1)
        self.assertEqual(res2["new_prs"][0]["exercise"], "Incline Dumbbell Press")
        self.assertEqual(res2["new_prs"][0]["weight"], 34.0)

        # Verify all PRs in database
        prs = AnalyticsManager.get_personal_records(user.id)
        pr_exercises = [p["exercise_name"] for p in prs]
        self.assertIn("Incline Dumbbell Press", pr_exercises)
        self.assertIn("Cable Crossover", pr_exercises)

        incline_pr = next(p for p in prs if p["exercise_name"] == "Incline Dumbbell Press")
        self.assertEqual(incline_pr["max_weight"], 34.0)
        self.assertGreater(incline_pr["max_volume"], 0.0)

        # Distinct exercises list must include all logged movements
        distinct = AnalyticsManager.get_distinct_exercises(user.id)
        self.assertIn("Incline Dumbbell Press", distinct)
        self.assertIn("Cable Crossover", distinct)

        # Universal progression curve query for Incline Dumbbell Press
        prog_points = AnalyticsManager.get_progression_data(user.id, "Incline Dumbbell Press")
        self.assertEqual(len(prog_points), 2)
        self.assertEqual(prog_points[0]["date"], "2026-11-01")
        self.assertEqual(prog_points[1]["date"], "2026-11-05")
        self.assertEqual(prog_points[1]["weight"], 34.0)

    # ---------------------------------------------------------
    # 12. Progressive Overload "Last Time" Ghost Targets
    # ---------------------------------------------------------
    def test_progressive_overload_ghost_targets(self):
        """
        Verify that the ghost target engine accurately retrieves the user's latest performance
        for that specific exercise, enabling progressive overload guidance.
        """
        user = User.create("ghost_user", "ghost@test.com", "pass1234")

        # Initial workout
        WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Back Power",
            date="2026-11-02",
            notes="Session A",
            sets_data=[
                {"muscle_group": "Back", "exercise_name": "Lat Pulldown", "set_number": 1, "weight": 55.0, "reps": 10, "is_warmup": False, "equipment_type": "machine"}
            ]
        )

        # Second workout with higher weight
        WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Back Power 2",
            date="2026-11-06",
            notes="Session B",
            sets_data=[
                {"muscle_group": "Back", "exercise_name": "Lat Pulldown", "set_number": 1, "weight": 60.0, "reps": 10, "is_warmup": False, "equipment_type": "machine"}
            ]
        )

        # Retrieve ghost target
        target = WorkoutManager.get_last_performance(user.id, "Lat Pulldown")
        self.assertIsNotNone(target)
        self.assertEqual(target["date"], "2026-11-06")
        self.assertEqual(target["weight"], 60.0)
        self.assertEqual(target["reps"], 10)

        # Test API endpoint
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        res = self.client.get("/api/workouts/last-performance?exercise=Lat+Pulldown")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["last_performance"]["weight"], 60.0)

    # ---------------------------------------------------------
    # 13. Workout Routines & Custom Split Templates
    # ---------------------------------------------------------
    def test_workout_routines_and_split_templates(self):
        """
        Verify starter split templates and user-created custom reusable templates.
        """
        user = User.create("routine_user", "routine@test.com", "pass1234")

        # Get initial templates (should contain default starters)
        templates = TemplateManager.get_user_templates(user.id)
        self.assertGreaterEqual(len(templates), 4)
        tmpl_names = [t["name"] for t in templates]
        self.assertTrue(any("Push Day" in name for name in tmpl_names))
        self.assertTrue(any("Pull Day" in name for name in tmpl_names))

        # Create custom split template
        custom_exercises = [
            {"muscleGroup": "Chest", "exerciseName": "Incline Dumbbell Press", "equipType": "dumbbell", "defaultWeight": 28, "defaultReps": 10, "targetSets": 3},
            {"muscleGroup": "Back", "exerciseName": "Chest Supported Row", "equipType": "machine", "defaultWeight": 45, "defaultReps": 10, "targetSets": 3}
        ]
        tid = TemplateManager.create_template(
            user_id=user.id,
            name="My Upper Hypertrophy Split",
            description="Upper day with dumbbell incline focus",
            split_category="Upper / Lower",
            exercises=custom_exercises
        )
        self.assertGreater(tid, 0)

        # Verify custom template appears first in list
        updated_templates = TemplateManager.get_user_templates(user.id)
        custom_tmpl = next(t for t in updated_templates if t["id"] == tid)
        self.assertEqual(custom_tmpl["name"], "My Upper Hypertrophy Split")
        self.assertTrue(custom_tmpl["is_custom"])
        self.assertEqual(len(custom_tmpl["exercises"]), 2)

        # Delete template
        deleted = TemplateManager.delete_template(tid, user.id)
        self.assertTrue(deleted)
        post_del = TemplateManager.get_user_templates(user.id)
        self.assertFalse(any(t["id"] == tid for t in post_del))

    # ---------------------------------------------------------
    # 14. Gamification Rewards & Badging System
    # ---------------------------------------------------------
    def test_gamification_rewards_and_badges_system(self):
        """
        Verify achievement badges (First 100kg lift, 50kg dumbbell club, consistency, PR master)
        and celebratory triggers when logging qualifying sets.
        """
        user = User.create("badge_champ", "champ@test.com", "pass1234")

        # Log a 100kg lift and 50kg dumbbell lift
        res = WorkoutManager.log_workout_session(
            user_id=user.id,
            title="Heavy Test Day",
            date="2026-11-07",
            notes="Badge unlock attempt",
            sets_data=[
                {"muscle_group": "Chest", "exercise_name": "Bench Press", "set_number": 1, "weight": 100.0, "reps": 5, "is_warmup": False, "equipment_type": "plates"},
                {"muscle_group": "Arms", "exercise_name": "Dumbbell Press", "set_number": 1, "weight": 50.0, "reps": 8, "is_warmup": False, "equipment_type": "dumbbell"}
            ]
        )
        self.assertIn("new_badges", res)
        self.assertGreater(len(res["new_badges"]), 0)

        summary = AnalyticsManager.get_dashboard_summary(user)
        milestones = summary["milestones"]
        m_map = {m["id"]: m for m in milestones}

        # Assert badges unlocked
        self.assertTrue(m_map["first_100kg_lift"]["achieved"])
        self.assertTrue(m_map["db_50kg_club"]["achieved"])

    # ---------------------------------------------------------
    # 15. MyFitnessPal Aesthetic, Date Bar & Calorie Formula
    # ---------------------------------------------------------
    def test_myfitnesspal_daily_date_bar_and_calorie_formula(self):
        """
        Verify Top Daily Date Bar query parameter on Hub and Nutrition,
        and MyFitnessPal calorie formula data (Goal - Food + Exercise = Remaining).
        """
        user = User.create("mfp_user", "mfp@test.com", "pass1234")
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # 1. Log steps for exercise burned calories
        test_date = "2026-11-08"
        StepManager.log_or_update_steps(user.id, test_date, 6500, user)

        # 2. Log food for that date
        NutritionManager.log_meal(
            user_id=user.id,
            date=test_date,
            meal_type="Lunch",
            food_name="Chicken & Rice Bowl",
            calories=550.0,
            protein=45.0,
            carbs=50.0,
            fat=12.0
        )

        # 3. GET /dashboard with ?date=
        dash_res = self.client.get(f"/dashboard?date={test_date}")
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(test_date.encode(), dash_res.data)

        # 4. GET /nutrition with ?date=
        nutr_res = self.client.get(f"/nutrition?date={test_date}")
        self.assertEqual(nutr_res.status_code, 200)
        self.assertIn(test_date.encode(), nutr_res.data)
        self.assertIn(b"Calories Remaining", nutr_res.data)
        self.assertIn(b"html5-qrcode", nutr_res.data)

        # 5. GET /api/nutrition returns steps with exercise calories burned
        api_res = self.client.get(f"/api/nutrition?date={test_date}")
        self.assertEqual(api_res.status_code, 200)
        api_data = json.loads(api_res.data)
        self.assertTrue(api_data["success"])
        self.assertEqual(api_data["totals"]["calories"], 550.0)
        self.assertIn("steps", api_data)
        self.assertEqual(api_data["steps"]["steps"], 6500)
        self.assertGreater(api_data["steps"]["calories_burned"], 0)

    # ---------------------------------------------------------
    # 16. Step-by-Step Onboarding Wizard & Calculations
    # ---------------------------------------------------------
    def test_onboarding_calculation_engine(self):
        """
        Verify Mifflin-St Jeor BMR, TDEE, net calorie adjustments, macro splits,
        and hydration requirements calculated across different goals and objectives.
        """
        # Test 1: Male, 75kg, 178cm, age 25, gain muscle, bulk objective, moderate activity
        bulk_plan = calculate_onboarding_targets(
            gender="male",
            age=25,
            height_cm=178.0,
            weight=75.0,
            core_goal="gain_weight",
            fitness_objective="bulk",
            activity_level="moderate",
            unit="kg"
        )
        self.assertGreater(bulk_plan["bmr"], 1600)
        self.assertGreater(bulk_plan["tdee"], bulk_plan["bmr"])
        self.assertGreater(bulk_plan["daily_calorie_target"], bulk_plan["tdee"]) # Surplus
        self.assertGreaterEqual(bulk_plan["daily_protein_target"], 150) # >= 2.0g/kg
        self.assertGreater(bulk_plan["water_goal_ml"], 2500)
        self.assertEqual(bulk_plan["core_goal"], "gain_weight")

        # Test 2: Female, 65kg, 165cm, age 28, lose weight, tone objective, sedentary
        cut_plan = calculate_onboarding_targets(
            gender="female",
            age=28,
            height_cm=165.0,
            weight=65.0,
            core_goal="lose_weight",
            fitness_objective="tone",
            activity_level="sedentary",
            unit="kg"
        )
        self.assertEqual(cut_plan["gender"], "female")
        self.assertLess(cut_plan["daily_calorie_target"], cut_plan["tdee"]) # Deficit
        self.assertGreaterEqual(cut_plan["daily_protein_target"], 130) # ~2.2g/kg for tone

    def test_onboarding_flow_and_api(self):
        """
        Verify GET /onboarding, POST /api/onboarding/calculate,
        and POST /onboarding completing onboarding and saving profile targets.
        """
        user = User.create("onboard_user", "onboard@test.com", "pass1234")
        self.assertFalse(user.onboarding_completed)

        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # 1. GET /onboarding
        get_res = self.client.get("/onboarding")
        self.assertEqual(get_res.status_code, 200)
        self.assertIn(b"Personalized Onboarding Wizard", get_res.data)

        # 2. POST /api/onboarding/calculate
        calc_res = self.client.post("/api/onboarding/calculate", json={
            "gender": "male",
            "dob": "1997-06-15",
            "height": 180,
            "weight": 80,
            "core_goal": "gain_weight",
            "fitness_objective": "tone",
            "activity_level": "moderate"
        })
        self.assertEqual(calc_res.status_code, 200)
        calc_data = json.loads(calc_res.data)
        self.assertTrue(calc_data["success"])
        self.assertIn("daily_calorie_target", calc_data["plan"])

        # 3. POST /onboarding form submission
        post_res = self.client.post("/onboarding", data={
            "first_name": "Marcus",
            "core_goal": "gain_weight",
            "fitness_objective": "bulk",
            "activity_level": "moderate",
            "gender": "male",
            "dob": "1997-06-15",
            "height": 180,
            "weight": 80,
            "goal_weight": 85,
            "unit_preference": "kg"
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)

        # Reload user from DB
        updated_user = User.get_by_id(user.id)
        self.assertTrue(updated_user.onboarding_completed)
        self.assertEqual(updated_user.display_name, "Marcus")
        self.assertEqual(updated_user.fitness_goal, "gain_weight")
        self.assertEqual(updated_user.fitness_objective, "bulk")
        self.assertGreater(updated_user.daily_calorie_target, 2000)

    # ---------------------------------------------------------
    # 17. Water Consumption Hydration Tracker
    # ---------------------------------------------------------
    def test_water_consumption_tracker(self):
        """
        Verify WaterManager calculations, quick-add, undo, reset,
        and integration with /api/nutrition/water and /api/nutrition.
        """
        user = User.create("water_user", "water@test.com", "pass1234")
        test_date = "2026-11-08"

        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # 1. Initial water is 0
        w0 = WaterManager.get_daily_water(user.id, test_date)
        self.assertEqual(w0["amount_ml"], 0)
        self.assertEqual(w0["cups"], 0.0)

        # 2. Add 250ml (+1 cup)
        w1 = WaterManager.log_or_update_water(user.id, test_date, delta_ml=250)
        self.assertEqual(w1["amount_ml"], 250)
        self.assertEqual(w1["cups"], 1.0)

        # 3. Add 500ml via API endpoint POST /api/nutrition/water
        res_post = self.client.post("/api/nutrition/water", json={
            "date": test_date,
            "delta_ml": 500
        })
        self.assertEqual(res_post.status_code, 200)
        data_post = json.loads(res_post.data)
        self.assertTrue(data_post["success"])
        self.assertEqual(data_post["water"]["amount_ml"], 750)
        self.assertEqual(data_post["water"]["cups"], 3.0)

        # 4. GET /api/nutrition/water
        res_get = self.client.get(f"/api/nutrition/water?date={test_date}")
        self.assertEqual(res_get.status_code, 200)
        data_get = json.loads(res_get.data)
        self.assertEqual(data_get["water"]["amount_ml"], 750)

        # 5. GET /api/nutrition includes water data
        res_nutr = self.client.get(f"/api/nutrition?date={test_date}")
        self.assertEqual(res_nutr.status_code, 200)
        nutr_data = json.loads(res_nutr.data)
        self.assertIn("water", nutr_data)
        self.assertEqual(nutr_data["water"]["amount_ml"], 750)

    # ---------------------------------------------------------
    # 18. Freemium 'Go Premium' Feature Locking System
    # ---------------------------------------------------------
    def test_freemium_feature_locking_system(self):
        """
        Verify 7-day free trial gives full Pro access, expired trial locks features
        and renders 'Go Premium' upgrade prompt, and owner account retains lifetime access.
        """
        # 1. New user has active 7-day trial -> Pro access granted
        trial_user = User.create("trial_hero", "trial@test.com", "pass1234")
        self.assertTrue(trial_user.has_pro_access)
        self.assertEqual(trial_user.subscription_badge["type"], "trial")
        self.assertGreater(trial_user.trial_days_left, 0)

        # 2. Expired trial user -> Pro access revoked
        expired_user = User.create("expired_guy", "expired@test.com", "pass1234")
        with get_db() as conn:
            conn.execute("UPDATE users SET subscription_status = 'expired', trial_ends_at = datetime('now', '-2 days') WHERE id = ?", (expired_user.id,))
        expired_reloaded = User.get_by_id(expired_user.id)
        self.assertFalse(expired_reloaded.has_pro_access)
        self.assertEqual(expired_reloaded.subscription_badge["type"], "expired")

        # 3. Expired user blocked from Pro CSV export
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(expired_user.id)
            sess["_fresh"] = True

        exp_res = self.client.get("/export/workouts.csv", follow_redirects=False)
        self.assertEqual(exp_res.status_code, 302)
        self.assertIn("/subscription", exp_res.headers.get("Location", ""))

        # 4. Nutrition page renders 'Go Premium' locking overlay for expired user
        nutr_res = self.client.get("/nutrition")
        self.assertEqual(nutr_res.status_code, 200)
        self.assertIn(b"Go Premium", nutr_res.data)
        self.assertIn(b"PKR 500 / mo", nutr_res.data)

        # 5. Master Owner Swagger has permanent lifetime VIP
        owner_user = User.get_by_username("swagger")
        if not owner_user:
            owner_user = User.create("swagger", "ghost.5abdullah@gmail.com", "pass1234")
        self.assertTrue(owner_user.is_owner_user)
        self.assertTrue(owner_user.has_pro_access)
        self.assertEqual(owner_user.subscription_badge["type"], "owner")

    # ---------------------------------------------------------
    # 11. Barcode Database & Vision OCR Tests
    # ---------------------------------------------------------
    def test_barcode_database_save_and_retrieve(self):
        """Verify BarcodeManager saves custom barcodes and handles retrieval."""
        saved = BarcodeManager.save_barcode(
            barcode="7613035987654",
            food_name="Pure Whey Isolate",
            brand="Optimum Sport",
            serving_size="30g",
            calories=120.0,
            protein=25.0,
            carbs=2.0,
            fat=1.0,
            source="custom"
        )
        self.assertIsNotNone(saved)
        self.assertEqual(saved["barcode"], "7613035987654")
        self.assertEqual(saved["food_name"], "Pure Whey Isolate")
        self.assertEqual(saved["protein"], 25.0)

        # Retrieve
        fetched = BarcodeManager.get_by_barcode("7613035987654")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["calories"], 120.0)

        # Missing barcode returns None
        missing = BarcodeManager.get_by_barcode("9999999999999")
        self.assertIsNone(missing)

    def test_barcode_api_endpoints(self):
        """Test GET and POST endpoints for custom barcodes."""
        user = User.create("barcode_user", "bar@test.com", "pass1234")
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # POST /api/barcodes
        save_res = self.client.post("/api/barcodes", json={
            "barcode": "8901234567890",
            "food_name": "Greek Yogurt Cups",
            "brand": "Chobani",
            "serving_size": "150g",
            "calories": 130,
            "protein": 14,
            "carbs": 12,
            "fat": 0
        })
        self.assertEqual(save_res.status_code, 200)
        save_data = save_res.get_json()
        self.assertTrue(save_data["success"])
        self.assertEqual(save_data["product"]["brand"], "Chobani")

        # GET /api/barcodes/<barcode>
        get_res = self.client.get("/api/barcodes/8901234567890")
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.get_json()
        self.assertTrue(get_data["success"])
        self.assertEqual(get_data["product"]["food_name"], "Greek Yogurt Cups")

        # GET missing barcode
        missing_res = self.client.get("/api/barcodes/0000000000000")
        self.assertEqual(missing_res.status_code, 404)

    def test_barcode_ocr_endpoint_in_test_mode(self):
        """Test POST /api/barcodes/ocr with test image payload."""
        user = User.create("ocr_user", "ocr@test.com", "pass1234")
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        dummy_image = (io.BytesIO(b"RIFF....WAVEfmt test image data byte content over 120 bytes minimum threshold required by OCR check...................."), "label.jpg")
        ocr_res = self.client.post(
            "/api/barcodes/ocr",
            data={
                "barcode": "5060123456789",
                "image": dummy_image
            },
            content_type="multipart/form-data"
        )
        self.assertEqual(ocr_res.status_code, 200)
        ocr_data = ocr_res.get_json()
        self.assertTrue(ocr_data["success"])
        self.assertIn("product", ocr_data)
        self.assertEqual(ocr_data["product"]["barcode"], "5060123456789")

    # ---------------------------------------------------------
    # 12. Visual Barbell Plate Loader Tests
    # ---------------------------------------------------------
    def test_calculate_barbell_plates_kg(self):
        """Test greedy Olympic plate math in kg."""
        # Target 100 kg with 20 kg bar -> 80 kg needed -> 40 kg per side: 25kg + 15kg
        breakdown = calculate_barbell_plates(100.0, bar_weight=20.0, unit="kg")
        self.assertEqual(breakdown["target_weight"], 100.0)
        self.assertEqual(breakdown["bar_weight"], 20.0)
        self.assertEqual(breakdown["side_weight"], 40.0)
        self.assertEqual(breakdown["total_loaded"], 100.0)
        self.assertEqual(breakdown["unit"], "kg")
        # 40 kg per side: 1 x 25kg, 1 x 15kg
        self.assertEqual(breakdown["plate_counts"], {"25.0": 1, "15.0": 1})

        # Target 140 kg with 20 kg bar -> 120 kg needed -> 60 kg per side: 2 x 25kg + 1 x 10kg
        breakdown_140 = calculate_barbell_plates(140.0, bar_weight=20.0, unit="kg")
        self.assertEqual(breakdown_140["plate_counts"], {"25.0": 2, "10.0": 1})

        # Target <= bar weight
        breakdown_empty = calculate_barbell_plates(20.0, bar_weight=20.0, unit="kg")
        self.assertEqual(breakdown_empty["side_weight"], 0.0)
        self.assertEqual(len(breakdown_empty["plates_per_side"]), 0)

    def test_calculate_barbell_plates_lbs(self):
        """Test greedy Olympic plate math in lbs."""
        # 225 lbs with 45 lb bar -> 180 lbs needed -> 90 lbs per side: 2 x 45lb
        breakdown_lbs = calculate_barbell_plates(225.0, bar_weight=45.0, unit="lbs")
        self.assertEqual(breakdown_lbs["side_weight"], 90.0)
        self.assertEqual(breakdown_lbs["total_loaded"], 225.0)
        self.assertEqual(breakdown_lbs["plate_counts"], {"45.0": 2})

    def test_plate_calculator_api_endpoint(self):
        """Test /api/plates/calculate endpoint."""
        res = self.client.post("/api/plates/calculate", json={
            "target_weight": 110.0,
            "bar_weight": 20.0,
            "unit": "kg"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["breakdown"]["side_weight"], 45.0)
        self.assertEqual(data["breakdown"]["plate_counts"], {"25.0": 1, "20.0": 1})

    # ---------------------------------------------------------
    # 13. Supabase & Onboarding Profiles Schema Tests
    # ---------------------------------------------------------
    def test_onboarding_profiles_table_persistence(self):
        """Verify User.complete_onboarding writes to the onboarding_profiles table."""
        user = User.create("profile_user", "prof@test.com", "pass1234")
        targets = calculate_onboarding_targets(
            gender="male",
            age=25,
            height_cm=180.0,
            weight=85.0,
            goal_weight=78.0,
            core_goal="lose_weight",
            fitness_objective="tone",
            activity_level="active"
        )
        user.complete_onboarding({
            "first_name": "ProfileTester",
            "core_goal": "lose_weight",
            "fitness_objective": "tone",
            "activity_level": "active",
            "gender": "male",
            "height": 180.0,
            "weight": 85.0,
            "goal_weight": 78.0,
            "daily_calorie_target": targets["daily_calorie_target"],
            "daily_protein_target": targets["daily_protein_target"],
            "daily_carbs_target": targets["daily_carbs_target"],
            "daily_fat_target": targets["daily_fat_target"],
            "water_goal_ml": targets["water_goal_ml"]
        })

        # Check onboarding_profiles table directly
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id, core_goal, calculated_calories, calculated_protein FROM onboarding_profiles WHERE user_id = ?", (user.id,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["user_id"], user.id)
            self.assertEqual(row["core_goal"], "lose_weight")
            self.assertEqual(row["calculated_calories"], targets["daily_calorie_target"])

if __name__ == "__main__":
    unittest.main()
