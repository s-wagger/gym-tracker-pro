"""
Gym Tracker Pro - Data Models & Business Logic
Handles database operations, bcrypt password hashing, session tracking,
automatic PR detection, and analytical aggregations.
"""
import bcrypt
from datetime import datetime, timedelta
from flask_login import UserMixin
from database import get_db
from formulas import calculate_epley_1rm, evaluate_milestones

class User(UserMixin):
    def __init__(self, data: dict):
        self.id = data["id"]
        self.username = data["username"]
        self.email = data["email"]
        self.password_hash = data["password_hash"]
        self.display_name = data.get("display_name") or data["username"]
        self.unit_preference = data.get("unit_preference") or "kg"
        self.daily_calorie_target = data.get("daily_calorie_target") or 2500
        self.daily_protein_target = data.get("daily_protein_target") or 160
        self.daily_carbs_target = data.get("daily_carbs_target") or 250
        self.daily_fat_target = data.get("daily_fat_target") or 70
        self.height = float(data.get("height") or 175.0)
        self.weight = float(data.get("weight") or 75.0)
        self.fitness_goal = data.get("fitness_goal") or "gain_weight"
        self.created_at = data.get("created_at")

    @staticmethod
    def get_by_id(user_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return User(row) if row else None

    @staticmethod
    def get_by_username(username: str):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
            row = cursor.fetchone()
            return User(row) if row else None

    @staticmethod
    def get_by_email(email: str):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
            row = cursor.fetchone()
            return User(row) if row else None

    @staticmethod
    def create(username: str, email: str, password: str, display_name: str = None, unit_preference: str = "kg", height: float = 175.0, weight: float = 75.0, fitness_goal: str = "gain_weight"):
        salt = bcrypt.gensalt()
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        user_id = None
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (username, email, password_hash, display_name, unit_preference, height, weight, fitness_goal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (username.strip(), email.strip().lower(), pw_hash, (display_name or username).strip(), unit_preference, float(height), float(weight), fitness_goal))
            user_id = cursor.lastrowid
        return User.get_by_id(user_id)

    def verify_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def update_password(self, new_password: str):
        salt = bcrypt.gensalt()
        pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), salt).decode("utf-8")
        with get_db() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, self.id))
        self.password_hash = pw_hash

    def update_profile(self, display_name: str, unit_preference: str, calorie_target: int, protein_target: int, carbs_target: int, fat_target: int, height: float = None, weight: float = None, fitness_goal: str = None):
        h = float(height) if height is not None else self.height
        w = float(weight) if weight is not None else self.weight
        g = fitness_goal if fitness_goal is not None else self.fitness_goal
        with get_db() as conn:
            conn.execute("""
            UPDATE users SET display_name = ?, unit_preference = ?, daily_calorie_target = ?, 
            daily_protein_target = ?, daily_carbs_target = ?, daily_fat_target = ?,
            height = ?, weight = ?, fitness_goal = ?
            WHERE id = ?
            """, (display_name.strip(), unit_preference, calorie_target, protein_target, carbs_target, fat_target, h, w, g, self.id))
        self.display_name = display_name
        self.unit_preference = unit_preference
        self.daily_calorie_target = calorie_target
        self.daily_protein_target = protein_target
        self.daily_carbs_target = carbs_target
        self.daily_fat_target = fat_target
        self.height = h
        self.weight = w
        self.fitness_goal = g
        self.daily_protein_target = protein_target
        self.daily_carbs_target = carbs_target
        self.daily_fat_target = fat_target


class WorkoutManager:
    @staticmethod
    def log_workout_session(user_id: int, title: str, date: str, notes: str, sets_data: list) -> dict:
        """
        Creates a workout session with all child sets.
        Automatically analyzes each set for Personal Records (PRs) using Epley 1RM.
        Returns session info and any newly achieved PRs.
        """
        new_prs_detected = []
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. Insert session
            cursor.execute("""
            INSERT INTO workout_sessions (user_id, title, date, notes)
            VALUES (?, ?, ?, ?)
            """, (user_id, title.strip(), date, notes.strip() if notes else ""))
            session_id = cursor.lastrowid

            # 2. Process each set
            for idx, s in enumerate(sets_data):
                muscle_group = s.get("muscle_group", "Full Body").strip()
                exercise_name = s.get("exercise_name", "").strip()
                weight = float(s.get("weight", 0.0))
                reps = int(s.get("reps", 0))
                rpe = float(s.get("rpe", 8.0))
                is_warmup = 1 if s.get("is_warmup") else 0
                set_num = int(s.get("set_number", idx + 1))
                
                # Calculate estimated 1RM
                est_1rm = calculate_epley_1rm(weight, reps)
                
                is_pr = 0
                if not is_warmup and weight > 0 and reps > 0:
                    # Check current PR for this exercise
                    cursor.execute("""
                    SELECT max_weight, reps, estimated_1rm FROM personal_records
                    WHERE user_id = ? AND LOWER(exercise_name) = LOWER(?)
                    """, (user_id, exercise_name))
                    existing_pr = cursor.fetchone()

                    if existing_pr is None:
                        # First time logging this exercise -> New PR!
                        is_pr = 1
                        cursor.execute("""
                        INSERT INTO personal_records (user_id, exercise_name, max_weight, reps, estimated_1rm, date_achieved)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (user_id, exercise_name, weight, reps, est_1rm, date))
                        new_prs_detected.append({
                            "exercise": exercise_name,
                            "weight": weight,
                            "reps": reps,
                            "estimated_1rm": est_1rm,
                            "improvement": "First recorded PR!"
                        })
                    else:
                        # Existing PR: check if weight is higher or 1RM is higher
                        prev_max_weight = existing_pr["max_weight"]
                        prev_1rm = existing_pr["estimated_1rm"]
                        
                        if weight > prev_max_weight or est_1rm > prev_1rm:
                            is_pr = 1
                            diff = round(weight - prev_max_weight, 1)
                            cursor.execute("""
                            UPDATE personal_records
                            SET max_weight = MAX(max_weight, ?),
                                reps = CASE WHEN ? >= max_weight THEN ? ELSE reps END,
                                estimated_1rm = MAX(estimated_1rm, ?),
                                date_achieved = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = ? AND LOWER(exercise_name) = LOWER(?)
                            """, (weight, weight, reps, est_1rm, date, user_id, exercise_name))
                            
                            new_prs_detected.append({
                                "exercise": exercise_name,
                                "weight": weight,
                                "reps": reps,
                                "estimated_1rm": est_1rm,
                                "improvement": f"+{diff} over previous record!" if diff > 0 else "New 1RM milestone!"
                            })

                cursor.execute("""
                INSERT INTO workout_sets 
                (session_id, user_id, muscle_group, exercise_name, set_number, weight, reps, rpe, is_warmup, is_pr, estimated_1rm)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (session_id, user_id, muscle_group, exercise_name, set_num, weight, reps, rpe, is_warmup, is_pr, est_1rm))

            # Consolidate so only the highest peak PR per exercise is returned
            consolidated_prs = {}
            for pr in new_prs_detected:
                ex = pr["exercise"].lower()
                if ex not in consolidated_prs or pr["weight"] >= consolidated_prs[ex]["weight"]:
                    consolidated_prs[ex] = pr

        return {
            "session_id": session_id,
            "title": title,
            "date": date,
            "new_prs": list(consolidated_prs.values())
        }

    @staticmethod
    def get_user_workouts(user_id: int, muscle_group: str = None, exercise_name: str = None, date_str: str = None, limit: int = 50):
        """
        Retrieves workout sessions along with nested sets, optionally filtered.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
            SELECT DISTINCT s.id, s.title, s.date, s.notes, s.created_at
            FROM workout_sessions s
            LEFT JOIN workout_sets w ON s.id = w.session_id
            WHERE s.user_id = ?
            """
            params = [user_id]

            if muscle_group and muscle_group.lower() != "all":
                query += " AND LOWER(w.muscle_group) = LOWER(?)"
                params.append(muscle_group.strip())

            if exercise_name and exercise_name.strip():
                query += " AND LOWER(w.exercise_name) LIKE LOWER(?)"
                params.append(f"%{exercise_name.strip()}%")

            if date_str and date_str.strip():
                query += " AND s.date = ?"
                params.append(date_str.strip())

            query += " ORDER BY s.date DESC, s.id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            sessions = cursor.fetchall()

            # Populate sets for each session
            for sess in sessions:
                cursor.execute("""
                SELECT id, muscle_group, exercise_name, set_number, weight, reps, rpe, is_warmup, is_pr, estimated_1rm
                FROM workout_sets
                WHERE session_id = ?
                ORDER BY exercise_name, set_number ASC
                """, (sess["id"],))
                sess_sets = cursor.fetchall()
                sess["sets"] = sess_sets
                sess["total_volume"] = sum(s["weight"] * s["reps"] for s in sess_sets if not s["is_warmup"])
                sess["total_sets"] = len(sess_sets)
                sess["has_pr"] = any(s["is_pr"] == 1 for s in sess_sets)
                sess["exercises_summary"] = list(dict.fromkeys(s["exercise_name"] for s in sess_sets))

            return sessions

    @staticmethod
    def delete_session(session_id: int, user_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workout_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
            return cursor.rowcount > 0


class NutritionManager:
    @staticmethod
    def log_meal(user_id: int, date: str, meal_type: str, food_name: str, calories: float, protein: float, carbs: float, fat: float) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO nutrition_entries (user_id, date, meal_type, food_name, calories, protein, carbs, fat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, date, meal_type.strip(), food_name.strip(), float(calories), float(protein), float(carbs), float(fat)))
            return cursor.lastrowid

    @staticmethod
    def delete_meal(entry_id: int, user_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM nutrition_entries WHERE id = ? AND user_id = ?", (entry_id, user_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_daily_nutrition(user_id: int, date_str: str) -> dict:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, meal_type, food_name, calories, protein, carbs, fat, created_at
            FROM nutrition_entries
            WHERE user_id = ? AND date = ?
            ORDER BY id ASC
            """, (user_id, date_str))
            entries = cursor.fetchall()

            total_cals = round(sum(e["calories"] for e in entries), 1)
            total_protein = round(sum(e["protein"] for e in entries), 1)
            total_carbs = round(sum(e["carbs"] for e in entries), 1)
            total_fat = round(sum(e["fat"] for e in entries), 1)

            # Group entries by meal_type
            grouped = {
                "Breakfast": [],
                "Lunch": [],
                "Dinner": [],
                "Snack": [],
                "Post-Workout": []
            }
            for e in entries:
                m_type = e["meal_type"]
                if m_type not in grouped:
                    grouped[m_type] = []
                grouped[m_type].append(e)

            return {
                "date": date_str,
                "entries": entries,
                "grouped": grouped,
                "totals": {
                    "calories": total_cals,
                    "protein": total_protein,
                    "carbs": total_carbs,
                    "fat": total_fat
                }
            }


class AnalyticsManager:
    @staticmethod
    def get_personal_records(user_id: int) -> list:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT exercise_name, max_weight, reps, estimated_1rm, date_achieved, updated_at
            FROM personal_records
            WHERE user_id = ?
            ORDER BY max_weight DESC, estimated_1rm DESC
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_key_prs(user_id: int) -> dict:
        prs = AnalyticsManager.get_personal_records(user_id)
        key_lifts = ["Bench Press", "Back Squat", "Deadlift", "Overhead Press"]
        res = {}
        for lift in key_lifts:
            found = next((p for p in prs if p["exercise_name"].lower() == lift.lower()), None)
            if found:
                res[lift] = {
                    "weight": found["max_weight"],
                    "reps": found["reps"],
                    "estimated_1rm": found["estimated_1rm"],
                    "date": found["date_achieved"]
                }
            else:
                res[lift] = {"weight": 0.0, "reps": 0, "estimated_1rm": 0.0, "date": "Not yet logged"}
        return res

    @staticmethod
    def get_progression_data(user_id: int, exercise_name: str, days: int = None) -> list:
        """Returns time-series data points of (date, weight, reps, estimated_1rm) for charting."""
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
            SELECT s.date, w.weight, w.reps, w.estimated_1rm, w.set_number
            FROM workout_sets w
            JOIN workout_sessions s ON w.session_id = s.id
            WHERE w.user_id = ? AND LOWER(w.exercise_name) = LOWER(?) AND w.is_warmup = 0
            """
            params = [user_id, exercise_name.strip()]

            if days:
                cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                query += " AND s.date >= ?"
                params.append(cutoff)

            query += " ORDER BY s.date ASC, w.id ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return rows

    @staticmethod
    def get_distinct_exercises(user_id: int) -> list:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT DISTINCT exercise_name FROM workout_sets
            WHERE user_id = ?
            ORDER BY exercise_name ASC
            """, (user_id,))
            rows = cursor.fetchall()
            return [r["exercise_name"] for r in rows]

    @staticmethod
    def get_dashboard_summary(user: User) -> dict:
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Total workouts
            cursor.execute("SELECT COUNT(*) as count FROM workout_sessions WHERE user_id = ?", (user.id,))
            total_workouts = cursor.fetchone()["count"]

            # Total volume lifted (kg or lbs)
            cursor.execute("SELECT COALESCE(SUM(weight * reps), 0) as total_vol FROM workout_sets WHERE user_id = ? AND is_warmup = 0", (user.id,))
            total_volume = round(cursor.fetchone()["total_vol"], 1)

            # Active PR count
            cursor.execute("SELECT COUNT(*) as pr_count FROM personal_records WHERE user_id = ?", (user.id,))
            pr_count = cursor.fetchone()["pr_count"]

            # Recent 3 workouts
            recent_workouts = WorkoutManager.get_user_workouts(user.id, limit=3)

            # Today's nutrition
            today_nutrition = NutritionManager.get_daily_nutrition(user.id, today_str)

            # Key PRs & Milestones
            key_prs = AnalyticsManager.get_key_prs(user.id)
            milestones = evaluate_milestones({
                "key_prs": key_prs,
                "total_workouts": total_workouts,
                "total_volume": total_volume
            }, unit=user.unit_preference)

            return {
                "total_workouts": total_workouts,
                "total_volume": total_volume,
                "pr_count": pr_count,
                "recent_workouts": recent_workouts,
                "today_nutrition": today_nutrition,
                "key_prs": key_prs,
                "milestones": milestones
            }


class ExportManager:
    @staticmethod
    def get_workouts_csv_data(user_id: int) -> list:
        """Returns flattened workout set records for CSV export."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT s.date, s.title, w.muscle_group, w.exercise_name, w.set_number, 
                   w.weight, w.reps, w.rpe, w.is_warmup, w.is_pr, w.estimated_1rm,
                   (w.weight * w.reps) as volume, s.notes
            FROM workout_sets w
            JOIN workout_sessions s ON w.session_id = s.id
            WHERE w.user_id = ?
            ORDER BY s.date DESC, s.id DESC, w.set_number ASC
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_nutrition_csv_data(user_id: int) -> list:
        """Returns nutrition meal logs for CSV export."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT date, meal_type, food_name, calories, protein, carbs, fat, created_at
            FROM nutrition_entries
            WHERE user_id = ?
            ORDER BY date DESC, id ASC
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_prs_csv_data(user_id: int) -> list:
        """Returns personal record achievements for CSV export."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT exercise_name, max_weight, reps, estimated_1rm, date_achieved, updated_at
            FROM personal_records
            WHERE user_id = ?
            ORDER BY max_weight DESC
            """, (user_id,))
            return cursor.fetchall()
