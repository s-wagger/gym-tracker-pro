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
from models import User, WorkoutManager, NutritionManager, AnalyticsManager, ExportManager, StepManager, SubscriptionManager
from formulas import (
    calculate_epley_1rm, calculate_brzycki_1rm,
    calculate_lombardi_1rm, get_training_zones, evaluate_milestones,
    calculate_user_fitness_plan, calculate_step_metrics
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
        self.assertEqual(data["background_color"], "#0A1128")
        self.assertEqual(data["theme_color"], "#0A1128")
        self.assertGreaterEqual(len(data["icons"]), 2)

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
    # 9. Subscription, 30-Day Free Trial & Paywall Subsystem Tests
    # ---------------------------------------------------------
    def test_30_day_free_trial_and_paywall(self):
        """
        Verify:
        - New user starts with 30-day free trial and full Pro feature access.
        - When trial expires, pro features (AI Camera, 1RM, CSV Exports) are gated.
        - Core features (Workout logging, pedometer, manual nutrition, PRs) remain 100% accessible.
        - Direct Bank Transfer (UBL IBAN) payment submission & owner approval activates Pro.
        - Owner has permanent lifetime VIP access.
        """
        # 1. New user registration check
        user = User.create("subscriber", "sub@test.com", "pass1234")
        self.assertEqual(user.subscription_status, "trial")
        self.assertGreaterEqual(user.trial_days_left, 29)
        self.assertTrue(user.has_pro_access)

        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # During free trial: /1rm and /export are accessible
        res_1rm = self.client.get("/1rm")
        self.assertEqual(res_1rm.status_code, 200)

        res_export = self.client.get("/export")
        self.assertEqual(res_export.status_code, 200)

        # 2. Simulate 30-day Free Trial Expiration
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

        # 4. Bank Transfer Payment Verification Request (UBL IBAN)
        res_sub_submit = self.client.post("/api/subscription/submit", json={
            "sender_name": "Hamza Ali",
            "transaction_ref": "UBL-TXN-984210",
            "plan_name": "Pro Monthly",
            "amount_paid": 1500,
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

if __name__ == "__main__":
    unittest.main()
