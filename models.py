"""
Gym Tracker Pro - Data Models & Business Logic
Handles database operations, bcrypt password hashing, session tracking,
automatic PR detection, and analytical aggregations.
"""
import bcrypt
import json
from datetime import datetime, timedelta
from flask_login import UserMixin
from database import get_db
from formulas import calculate_epley_1rm, evaluate_milestones, calculate_step_metrics

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
        self.daily_step_goal = int(data.get("daily_step_goal") or 10000)
        self.subscription_status = data.get("subscription_status") or "trial"
        self.trial_ends_at = data.get("trial_ends_at")
        self.is_owner = bool(data.get("is_owner") or 0)
        self.gemini_api_key = data.get("gemini_api_key")
        self.created_at = data.get("created_at")

    @property
    def is_owner_user(self) -> bool:
        """Determines if this account is the permanent master owner (free lifetime VIP)."""
        import os
        if self.is_owner:
            return True
        owner_emails = ["ghost.5abdullah@gmail.com"] + [e.strip().lower() for e in os.environ.get("OWNER_EMAILS", "").split(",") if e.strip()]
        owner_usernames = ["swagger"] + [u.strip().lower() for u in os.environ.get("OWNER_USERNAMES", "").split(",") if u.strip()]
        if self.email and self.email.lower() in owner_emails:
            return True
        if self.username and self.username.lower() in owner_usernames:
            return True
        return False

    @property
    def trial_days_left(self) -> int:
        """Calculates days remaining in the 7-day free trial."""
        if self.is_owner_user or self.subscription_status in ["pro", "active", "lifetime_owner"]:
            return 999
        if not self.trial_ends_at:
            return 0
        try:
            end_str = str(self.trial_ends_at).split(".")[0]
            end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                end_dt = datetime.strptime(str(self.trial_ends_at)[:10], "%Y-%m-%d")
            except Exception:
                return 0
        delta = (end_dt - datetime.now()).total_seconds()
        days = int(delta // 86400)
        return max(0, days)

    @property
    def has_pro_access(self) -> bool:
        """
        Determines if user has access to Pro features (AI camera, 1RM, exports).
        Owner always has full access.
        New users get 7 days full trial.
        After 7 days, pro features lock until subscription is active.
        """
        if self.is_owner_user:
            return True
        if self.subscription_status in ["pro", "active", "lifetime_owner"]:
            return True
        if self.subscription_status == "trial" and self.trial_days_left > 0:
            return True
        return False

    @property
    def subscription_badge(self) -> dict:
        """Returns structured metadata for displaying membership / trial status."""
        if self.is_owner_user:
            return {
                "type": "owner",
                "label": "👑 Owner • Lifetime VIP",
                "short_label": "Owner",
                "days_left": None,
                "is_pro": True
            }
        if self.subscription_status in ["pro", "active", "lifetime_owner"]:
            return {
                "type": "pro",
                "label": "⭐ Pro Member",
                "short_label": "Pro",
                "days_left": None,
                "is_pro": True
            }
        days = self.trial_days_left
        if days > 0:
            return {
                "type": "trial",
                "label": f"⚡ Free Trial ({days}d left)",
                "short_label": f"{days}d Trial",
                "days_left": days,
                "is_pro": True
            }
        return {
            "type": "expired",
            "label": "🔒 Trial Expired",
            "short_label": "Expired",
            "days_left": 0,
            "is_pro": False
        }

    def grant_owner(self):
        with get_db() as conn:
            conn.execute("UPDATE users SET is_owner = 1, subscription_status = 'lifetime_owner' WHERE id = ?", (self.id,))
        self.is_owner = True
        self.subscription_status = "lifetime_owner"

    def set_subscription(self, status: str, days: int = 7):
        with get_db() as conn:
            if status == 'pro':
                conn.execute("UPDATE users SET subscription_status = 'pro' WHERE id = ?", (self.id,))
                self.subscription_status = 'pro'
            elif status == 'trial':
                new_end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                conn.execute("UPDATE users SET subscription_status = 'trial', trial_ends_at = ? WHERE id = ?", (new_end, self.id))
                self.subscription_status = 'trial'
                self.trial_ends_at = new_end
            else:
                conn.execute("UPDATE users SET subscription_status = ? WHERE id = ?", (status, self.id))
                self.subscription_status = status

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
    def create(username: str, email: str, password: str, display_name: str = None, unit_preference: str = "kg", height: float = 175.0, weight: float = 75.0, fitness_goal: str = "gain_weight", daily_step_goal: int = 10000):
        import os
        salt = bcrypt.gensalt()
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        user_id = None
        
        # 7-Day Free Trial (1 Week) initialized for every new user
        trial_end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if this user matches owner credentials from environment or default
        owner_emails = ["ghost.5abdullah@gmail.com"] + [e.strip().lower() for e in os.environ.get("OWNER_EMAILS", "").split(",") if e.strip()]
        owner_usernames = ["swagger"] + [u.strip().lower() for u in os.environ.get("OWNER_USERNAMES", "").split(",") if u.strip()]
        is_owner = 1 if (email.strip().lower() in owner_emails or username.strip().lower() in owner_usernames) else 0
        sub_status = "lifetime_owner" if is_owner else "trial"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (username, email, password_hash, display_name, unit_preference, height, weight, fitness_goal, daily_step_goal, subscription_status, trial_ends_at, is_owner)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username.strip(), email.strip().lower(), pw_hash, (display_name or username).strip(), unit_preference, float(height), float(weight), fitness_goal, int(daily_step_goal), sub_status, trial_end, is_owner))
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

    def update_profile(self, display_name: str, unit_preference: str, calorie_target: int, protein_target: int, carbs_target: int, fat_target: int, height: float = None, weight: float = None, fitness_goal: str = None, daily_step_goal: int = None):
        h = float(height) if height is not None else self.height
        w = float(weight) if weight is not None else self.weight
        g = fitness_goal if fitness_goal is not None else self.fitness_goal
        sg = int(daily_step_goal) if daily_step_goal is not None else self.daily_step_goal
        with get_db() as conn:
            conn.execute("""
            UPDATE users SET display_name = ?, unit_preference = ?, daily_calorie_target = ?, 
            daily_protein_target = ?, daily_carbs_target = ?, daily_fat_target = ?,
            height = ?, weight = ?, fitness_goal = ?, daily_step_goal = ?
            WHERE id = ?
            """, (display_name.strip(), unit_preference, calorie_target, protein_target, carbs_target, fat_target, h, w, g, sg, self.id))
        self.display_name = display_name
        self.unit_preference = unit_preference
        self.daily_calorie_target = calorie_target
        self.daily_protein_target = protein_target
        self.daily_carbs_target = carbs_target
        self.daily_fat_target = fat_target
        self.height = h
        self.weight = w
        self.fitness_goal = g
        self.daily_step_goal = sg

    def update_step_goal(self, goal: int):
        cleaned_goal = max(1000, min(100000, int(goal)))
        with get_db() as conn:
            conn.execute("UPDATE users SET daily_step_goal = ? WHERE id = ?", (cleaned_goal, self.id))
        self.daily_step_goal = cleaned_goal

    def update_gemini_api_key(self, api_key: str):
        cleaned_key = api_key.strip() if api_key and api_key.strip() else None
        with get_db() as conn:
            conn.execute("UPDATE users SET gemini_api_key = ? WHERE id = ?", (cleaned_key, self.id))
        self.gemini_api_key = cleaned_key


class WorkoutManager:
    @staticmethod
    def log_workout_session(user_id: int, title: str, date: str, notes: str, sets_data: list) -> dict:
        """
        Creates or appends to a single daily workout session with all child sets.
        Groups all exercises logged on that date under the same session.
        Automatically analyzes each set for Personal Records (PRs) using Epley 1RM.
        Returns session info and any newly achieved PRs.
        """
        new_prs_detected = []
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. Group under a single daily session for this user and date
            cursor.execute("""
            SELECT id, title, notes FROM workout_sessions 
            WHERE user_id = ? AND date = ? 
            ORDER BY id ASC LIMIT 1
            """, (user_id, date))
            existing_session = cursor.fetchone()

            if existing_session:
                session_id = existing_session["id"]
                # If user entered a specific title, update it; otherwise preserve
                if title and title.strip():
                    cursor.execute("UPDATE workout_sessions SET title = ? WHERE id = ?", (title.strip(), session_id))
                    session_title = title.strip()
                else:
                    session_title = existing_session["title"]
                if notes and notes.strip():
                    cursor.execute("""
                    UPDATE workout_sessions 
                    SET notes = CASE WHEN notes IS NULL OR notes = '' THEN ? ELSE notes || ' | ' || ? END 
                    WHERE id = ?
                    """, (notes.strip(), notes.strip(), session_id))
            else:
                session_title = title.strip() if title and title.strip() else "Daily Workout Session"
                cursor.execute("""
                INSERT INTO workout_sessions (user_id, title, date, notes)
                VALUES (?, ?, ?, ?)
                """, (user_id, session_title, date, notes.strip() if notes else ""))
                session_id = cursor.lastrowid

            # Capture prior achieved badge IDs for gamification reward detection
            pre_badges = set()
            try:
                pre_user = User.get_by_id(user_id)
                if pre_user:
                    pre_summary = AnalyticsManager.get_dashboard_summary(pre_user)
                    pre_badges = {m["id"] for m in pre_summary.get("milestones", []) if m.get("achieved")}
            except Exception:
                pass

            # 2. Process each set
            for idx, s in enumerate(sets_data):
                muscle_group = s.get("muscle_group", "Full Body").strip()
                exercise_name = s.get("exercise_name", "").strip()
                weight = float(s.get("weight", 0.0))
                reps = int(s.get("reps", 0))
                rpe = float(s.get("rpe", 8.0))
                is_warmup = 1 if s.get("is_warmup") else 0
                equipment_type = (s.get("equipment_type") or "direct").strip()
                equipment_details = s.get("equipment_details")

                # Get continuous set numbering for this exercise within this session
                cursor.execute("""
                SELECT COALESCE(MAX(set_number), 0) as max_set 
                FROM workout_sets 
                WHERE session_id = ? AND LOWER(exercise_name) = LOWER(?)
                """, (session_id, exercise_name))
                row_max = cursor.fetchone()
                existing_max = row_max["max_set"] if row_max else 0
                set_num = int(s.get("set_number") or (existing_max + 1))
                
                # Calculate estimated 1RM and set volume
                est_1rm = calculate_epley_1rm(weight, reps)
                set_vol = round(weight * reps, 1)
                
                is_pr = 0
                if not is_warmup and weight > 0 and reps > 0:
                    # Check current PR for this exercise
                    cursor.execute("""
                    SELECT max_weight, reps, estimated_1rm, COALESCE(max_volume, 0.0) as max_volume FROM personal_records
                    WHERE user_id = ? AND LOWER(exercise_name) = LOWER(?)
                    """, (user_id, exercise_name))
                    existing_pr = cursor.fetchone()

                    if existing_pr is None:
                        # First time logging this exercise -> New PR!
                        is_pr = 1
                        cursor.execute("""
                        INSERT INTO personal_records (user_id, exercise_name, max_weight, reps, estimated_1rm, max_volume, date_achieved)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (user_id, exercise_name, weight, reps, est_1rm, set_vol, date))
                        new_prs_detected.append({
                            "exercise": exercise_name,
                            "weight": weight,
                            "reps": reps,
                            "estimated_1rm": est_1rm,
                            "volume": set_vol,
                            "improvement": "First recorded PR!"
                        })
                    else:
                        # Existing PR: check if weight is higher, 1RM is higher, or set volume is higher
                        prev_max_weight = existing_pr["max_weight"]
                        prev_1rm = existing_pr["estimated_1rm"]
                        prev_volume = existing_pr["max_volume"]
                        
                        is_weight_pr = weight > prev_max_weight
                        is_1rm_pr = est_1rm > prev_1rm
                        is_volume_pr = set_vol > prev_volume

                        if is_weight_pr or is_1rm_pr or is_volume_pr:
                            is_pr = 1
                            diff_wt = round(weight - prev_max_weight, 1)
                            diff_vol = round(set_vol - prev_volume, 1)

                            if is_weight_pr:
                                reason = f"+{diff_wt} weight PR over previous record!"
                            elif is_1rm_pr:
                                reason = "New 1RM milestone!"
                            else:
                                reason = f"+{diff_vol} peak set volume PR!"

                            cursor.execute("""
                            UPDATE personal_records
                            SET max_weight = MAX(max_weight, ?),
                                reps = CASE WHEN ? >= max_weight THEN ? ELSE reps END,
                                estimated_1rm = MAX(estimated_1rm, ?),
                                max_volume = MAX(COALESCE(max_volume, 0.0), ?),
                                date_achieved = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE user_id = ? AND LOWER(exercise_name) = LOWER(?)
                            """, (weight, weight, reps, est_1rm, set_vol, date, user_id, exercise_name))
                            
                            new_prs_detected.append({
                                "exercise": exercise_name,
                                "weight": weight,
                                "reps": reps,
                                "estimated_1rm": est_1rm,
                                "volume": set_vol,
                                "improvement": reason
                            })

                cursor.execute("""
                INSERT INTO workout_sets 
                (session_id, user_id, muscle_group, exercise_name, set_number, weight, reps, rpe, is_warmup, is_pr, estimated_1rm, equipment_type, equipment_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (session_id, user_id, muscle_group, exercise_name, set_num, weight, reps, rpe, is_warmup, is_pr, est_1rm, equipment_type, equipment_details))

            # Consolidate so only the highest peak PR per exercise is returned
            consolidated_prs = {}
            for pr in new_prs_detected:
                ex = pr["exercise"].lower()
                if ex not in consolidated_prs or pr["weight"] >= consolidated_prs[ex]["weight"]:
                    consolidated_prs[ex] = pr

        # Post-session gamification badges check
        new_badges_detected = []
        try:
            post_user = User.get_by_id(user_id)
            if post_user:
                post_summary = AnalyticsManager.get_dashboard_summary(post_user)
                for badge in post_summary.get("milestones", []):
                    if badge.get("achieved") and badge.get("id") not in pre_badges:
                        new_badges_detected.append(badge)
        except Exception:
            pass

        return {
            "session_id": session_id,
            "title": session_title,
            "date": date,
            "new_prs": list(consolidated_prs.values()),
            "new_badges": new_badges_detected
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
                SELECT id, muscle_group, exercise_name, set_number, weight, reps, rpe, is_warmup, is_pr, estimated_1rm, equipment_type, equipment_details
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

    @staticmethod
    def get_last_performance(user_id: int, exercise_name: str) -> dict:
        """
        Retrieves the user's latest performance on a specific exercise.
        Returns the top non-warmup set from the most recent workout containing this exercise.
        """
        if not exercise_name or not exercise_name.strip():
            return None
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT s.date, w.weight, w.reps, w.estimated_1rm, w.rpe, w.equipment_type, w.equipment_details
            FROM workout_sets w
            JOIN workout_sessions s ON w.session_id = s.id
            WHERE w.user_id = ? AND LOWER(w.exercise_name) = LOWER(?) AND w.is_warmup = 0
            ORDER BY s.date DESC, w.weight DESC, w.reps DESC
            LIMIT 1
            """, (user_id, exercise_name.strip()))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all_last_performances(user_id: int) -> dict:
        """
        Retrieves a map of exercise_name -> latest top set performance.
        Useful for preloading ghost targets in the active session builder.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT w.exercise_name, s.date, w.weight, w.reps, w.estimated_1rm, w.rpe, w.equipment_type, w.equipment_details
            FROM workout_sets w
            JOIN workout_sessions s ON w.session_id = s.id
            WHERE w.user_id = ? AND w.is_warmup = 0
            ORDER BY s.date DESC, w.weight DESC
            """, (user_id,))
            rows = cursor.fetchall()
            results = {}
            for r in rows:
                key = r["exercise_name"].strip()
                if key not in results:
                    results[key] = dict(r)
            return results


class TemplateManager:
    """
    Manages custom and starter workout split templates (Push, Pull, Legs, Upper, etc.)
    allowing users to launch multi-exercise sessions with 1 click.
    """
    DEFAULT_STARTER_TEMPLATES = [
        {
            "id": "starter_push",
            "name": "Push Day (Chest, Shoulders, Triceps)",
            "description": "Hypertrophy and strength for pushing chain.",
            "split_category": "Push / Pull / Legs",
            "is_custom": False,
            "exercises": [
                { "muscleGroup": "Chest", "exerciseName": "Bench Press", "equipType": "plates", "defaultWeight": 60, "defaultReps": 10, "targetSets": 3 },
                { "muscleGroup": "Chest", "exerciseName": "Incline Dumbbell Press", "equipType": "dumbbell", "defaultWeight": 22.5, "defaultReps": 10, "targetSets": 3 },
                { "muscleGroup": "Shoulders", "exerciseName": "Overhead Press", "equipType": "plates", "defaultWeight": 40, "defaultReps": 8, "targetSets": 3 },
                { "muscleGroup": "Arms", "exerciseName": "Tricep Rope Pushdown", "equipType": "machine", "defaultWeight": 25, "defaultReps": 12, "targetSets": 3 }
            ]
        },
        {
            "id": "starter_pull",
            "name": "Pull Day (Back & Biceps)",
            "description": "Posterior chain thickness, lat width, and pulling power.",
            "split_category": "Push / Pull / Legs",
            "is_custom": False,
            "exercises": [
                { "muscleGroup": "Back", "exerciseName": "Barbell Row", "equipType": "plates", "defaultWeight": 60, "defaultReps": 10, "targetSets": 3 },
                { "muscleGroup": "Back", "exerciseName": "Lat Pulldown", "equipType": "machine", "defaultWeight": 50, "defaultReps": 10, "targetSets": 3 },
                { "muscleGroup": "Back", "exerciseName": "Seated Cable Row", "equipType": "machine", "defaultWeight": 45, "defaultReps": 12, "targetSets": 3 },
                { "muscleGroup": "Arms", "exerciseName": "Barbell Bicep Curl", "equipType": "direct", "defaultWeight": 30, "defaultReps": 10, "targetSets": 3 }
            ]
        },
        {
            "id": "starter_legs",
            "name": "Leg Day (Quads, Hamstrings & Calves)",
            "description": "Lower body compound power and hypertrophy foundation.",
            "split_category": "Push / Pull / Legs",
            "is_custom": False,
            "exercises": [
                { "muscleGroup": "Legs", "exerciseName": "Back Squat", "equipType": "plates", "defaultWeight": 80, "defaultReps": 8, "targetSets": 3 },
                { "muscleGroup": "Legs", "exerciseName": "Leg Press", "equipType": "plates", "defaultWeight": 120, "defaultReps": 10, "targetSets": 3 },
                { "muscleGroup": "Legs", "exerciseName": "Romanian Deadlift", "equipType": "plates", "defaultWeight": 70, "defaultReps": 10, "targetSets": 3 },
                { "muscleGroup": "Legs", "exerciseName": "Standing Calf Raise", "equipType": "machine", "defaultWeight": 40, "defaultReps": 15, "targetSets": 3 }
            ]
        },
        {
            "id": "starter_upper",
            "name": "Upper Body Power",
            "description": "Balanced high-intensity upper body workout.",
            "split_category": "Upper / Lower",
            "is_custom": False,
            "exercises": [
                { "muscleGroup": "Chest", "exerciseName": "Bench Press", "equipType": "plates", "defaultWeight": 70, "defaultReps": 8, "targetSets": 4 },
                { "muscleGroup": "Back", "exerciseName": "Barbell Row", "equipType": "plates", "defaultWeight": 65, "defaultReps": 8, "targetSets": 4 },
                { "muscleGroup": "Shoulders", "exerciseName": "Dumbbell Lateral Raise", "equipType": "dumbbell", "defaultWeight": 10, "defaultReps": 12, "targetSets": 3 },
                { "muscleGroup": "Arms", "exerciseName": "Incline Dumbbell Curl", "equipType": "dumbbell", "defaultWeight": 12.5, "defaultReps": 10, "targetSets": 3 }
            ]
        }
    ]

    @staticmethod
    def get_user_templates(user_id: int) -> list:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, name, description, split_category, exercises_json, created_at
            FROM workout_templates
            WHERE user_id = ?
            ORDER BY id DESC
            """, (user_id,))
            rows = cursor.fetchall()
            
            custom_templates = []
            for r in rows:
                try:
                    exs = json.loads(r["exercises_json"])
                except Exception:
                    exs = []
                custom_templates.append({
                    "id": r["id"],
                    "name": r["name"],
                    "description": r["description"] or "",
                    "split_category": r["split_category"] or "Custom",
                    "is_custom": True,
                    "exercises": exs,
                    "created_at": str(r["created_at"])
                })
            
            return custom_templates + TemplateManager.DEFAULT_STARTER_TEMPLATES

    @staticmethod
    def create_template(user_id: int, name: str, description: str, split_category: str, exercises: list) -> int:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO workout_templates (user_id, name, description, split_category, exercises_json)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, name.strip(), (description or "").strip(), (split_category or "Custom").strip(), json.dumps(exercises)))
            return cursor.lastrowid

    @staticmethod
    def delete_template(template_id: int, user_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM workout_templates WHERE id = ? AND user_id = ?", (template_id, user_id))
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
            SELECT exercise_name, max_weight, reps, estimated_1rm, COALESCE(max_volume, 0.0) as max_volume, date_achieved, updated_at
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
                    "max_volume": found["max_volume"],
                    "date": found["date_achieved"]
                }
            else:
                res[lift] = {"weight": 0.0, "reps": 0, "estimated_1rm": 0.0, "max_volume": 0.0, "date": "Not yet logged"}
        return res

    @staticmethod
    def get_progression_data(user_id: int, exercise_name: str, days: int = None) -> list:
        """Returns time-series data points of (date, weight, reps, estimated_1rm, volume) for charting."""
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
            SELECT s.date, w.weight, w.reps, w.estimated_1rm, (w.weight * w.reps) as volume, w.set_number
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
            SELECT DISTINCT exercise_name FROM (
                SELECT exercise_name FROM workout_sets WHERE user_id = ?
                UNION
                SELECT exercise_name FROM personal_records WHERE user_id = ?
            )
            ORDER BY exercise_name ASC
            """, (user_id, user_id))
            rows = cursor.fetchall()
            return [r["exercise_name"] for r in rows if r["exercise_name"]]

    @staticmethod
    def get_dashboard_summary(user: User, target_date: str = None) -> dict:
        today_str = target_date or datetime.now().strftime("%Y-%m-%d")
        
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

            # Peak single lift weight
            cursor.execute("SELECT COALESCE(MAX(weight), 0.0) as max_lift FROM workout_sets WHERE user_id = ? AND is_warmup = 0", (user.id,))
            max_lift_kg = float(cursor.fetchone()["max_lift"])

            # Peak dumbbell lift
            cursor.execute("SELECT COALESCE(MAX(weight), 0.0) as max_db FROM workout_sets WHERE user_id = ? AND is_warmup = 0 AND equipment_type = 'dumbbell'", (user.id,))
            max_db_kg = float(cursor.fetchone()["max_db"])

            # Max volume in a single session
            cursor.execute("""
            SELECT COALESCE(MAX(sess_vol), 0.0) as max_sess_vol FROM (
                SELECT session_id, SUM(weight * reps) as sess_vol
                FROM workout_sets
                WHERE user_id = ? AND is_warmup = 0
                GROUP BY session_id
            )
            """, (user.id,))
            vol_row = cursor.fetchone()
            session_max_volume = float(vol_row["max_sess_vol"]) if vol_row else 0.0

            # Workout streak count
            cursor.execute("SELECT DISTINCT date FROM workout_sessions WHERE user_id = ? ORDER BY date DESC LIMIT 30", (user.id,))
            dates = [r["date"] for r in cursor.fetchall()]
            streak_days = len(dates)

            # Recent 3 workouts
            recent_workouts = WorkoutManager.get_user_workouts(user.id, limit=3)

            # Today's nutrition
            today_nutrition = NutritionManager.get_daily_nutrition(user.id, today_str)

            # Key PRs & Milestones
            key_prs = AnalyticsManager.get_key_prs(user.id)
            milestones = evaluate_milestones({
                "key_prs": key_prs,
                "total_workouts": total_workouts,
                "total_volume": total_volume,
                "pr_count": pr_count,
                "max_lift_kg": max_lift_kg,
                "max_db_kg": max_db_kg,
                "session_max_volume": session_max_volume,
                "streak_days": streak_days
            }, unit=user.unit_preference)

            return {
                "total_workouts": total_workouts,
                "total_volume": total_volume,
                "pr_count": pr_count,
                "max_lift_kg": max_lift_kg,
                "max_db_kg": max_db_kg,
                "session_max_volume": session_max_volume,
                "streak_days": streak_days,
                "recent_workouts": recent_workouts,
                "today_nutrition": today_nutrition,
                "active_date": today_str,
                "key_prs": key_prs,
                "milestones": milestones
            }


class StepManager:
    @staticmethod
    def get_daily_steps(user_id: int, date_str: str, user: User = None) -> dict:
        """
        Retrieves step count and calculated biomechanical metrics for a specific date.
        If no entry exists, computes defaults with 0 steps.
        """
        if not user:
            user = User.get_by_id(user_id)
        
        goal = user.daily_step_goal if user else 10000
        height = user.height if user else 175.0
        weight = user.weight if user else 75.0
        unit = user.unit_preference if user else "kg"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, date, steps, distance_km, calories_burned, active_minutes, step_goal, updated_at
            FROM daily_steps
            WHERE user_id = ? AND date = ?
            """, (user_id, date_str))
            row = cursor.fetchone()

        current_steps = row["steps"] if row else 0
        current_goal = row["step_goal"] if row and row.get("step_goal") else goal

        metrics = calculate_step_metrics(
            steps=current_steps,
            height_cm=height,
            weight_val=weight,
            unit=unit,
            step_goal=current_goal
        )
        metrics["id"] = row["id"] if row else None
        metrics["date"] = date_str
        metrics["updated_at"] = row["updated_at"] if row else None
        return metrics

    @staticmethod
    def log_or_update_steps(user_id: int, date_str: str, steps: int, user: User = None, is_delta: bool = False) -> dict:
        """
        Updates step count for user on date_str.
        If is_delta=True, adds steps to existing count; otherwise sets total steps.
        """
        if not user:
            user = User.get_by_id(user_id)
        
        goal = user.daily_step_goal if user else 10000
        height = user.height if user else 175.0
        weight = user.weight if user else 75.0
        unit = user.unit_preference if user else "kg"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT steps, step_goal FROM daily_steps WHERE user_id = ? AND date = ?", (user_id, date_str))
            existing = cursor.fetchone()

            if existing:
                new_steps = max(0, existing["steps"] + steps if is_delta else steps)
                active_goal = existing["step_goal"] or goal
            else:
                new_steps = max(0, steps)
                active_goal = goal

            metrics = calculate_step_metrics(new_steps, height, weight, unit, active_goal)

            cursor.execute("""
            INSERT INTO daily_steps (user_id, date, steps, distance_km, calories_burned, active_minutes, step_goal, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, date) DO UPDATE SET
                steps = excluded.steps,
                distance_km = excluded.distance_km,
                calories_burned = excluded.calories_burned,
                active_minutes = excluded.active_minutes,
                step_goal = excluded.step_goal,
                updated_at = CURRENT_TIMESTAMP
            """, (user_id, date_str, new_steps, metrics["distance_km"], metrics["calories_burned"], metrics["active_minutes"], active_goal))

        return StepManager.get_daily_steps(user_id, date_str, user)

    @staticmethod
    def get_step_history(user_id: int, days: int = 7) -> list:
        """
        Returns the last `days` days of step history including dates with 0 steps.
        """
        user = User.get_by_id(user_id)
        height = user.height if user else 175.0
        weight = user.weight if user else 75.0
        unit = user.unit_preference if user else "kg"
        goal = user.daily_step_goal if user else 10000

        today = datetime.now().date()
        date_list = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days - 1, -1, -1)]

        with get_db() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(date_list))
            cursor.execute(f"""
            SELECT date, steps, distance_km, calories_burned, active_minutes, step_goal
            FROM daily_steps
            WHERE user_id = ? AND date IN ({placeholders})
            ORDER BY date ASC
            """, [user_id] + date_list)
            rows = {r["date"]: r for r in cursor.fetchall()}

        history = []
        for d in date_list:
            if d in rows:
                r = rows[d]
                m = calculate_step_metrics(r["steps"], height, weight, unit, r["step_goal"] or goal)
                m["date"] = d
                m["day_name"] = datetime.strptime(d, "%Y-%m-%d").strftime("%a")
                history.append(m)
            else:
                m = calculate_step_metrics(0, height, weight, unit, goal)
                m["date"] = d
                m["day_name"] = datetime.strptime(d, "%Y-%m-%d").strftime("%a")
                history.append(m)

        return history

    @staticmethod
    def get_step_stats(user_id: int) -> dict:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                COUNT(*) as days_logged,
                COALESCE(SUM(steps), 0) as total_steps,
                COALESCE(AVG(steps), 0) as avg_steps,
                COALESCE(MAX(steps), 0) as best_steps,
                COALESCE(SUM(distance_km), 0) as total_distance_km,
                COALESCE(SUM(calories_burned), 0) as total_calories_burned
            FROM daily_steps
            WHERE user_id = ? AND steps > 0
            """, (user_id,))
            row = cursor.fetchone() or {}
            return {
                "days_logged": row.get("days_logged", 0),
                "total_steps": int(row.get("total_steps", 0)),
                "avg_steps": int(round(row.get("avg_steps", 0))),
                "best_steps": int(row.get("best_steps", 0)),
                "total_distance_km": round(float(row.get("total_distance_km", 0.0)), 1),
                "total_calories_burned": int(round(float(row.get("total_calories_burned", 0.0))))
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

    @staticmethod
    def get_steps_csv_data(user_id: int) -> list:
        """Returns daily steps history for CSV export."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT date, steps, distance_km, calories_burned, active_minutes, step_goal, updated_at
            FROM daily_steps
            WHERE user_id = ?
            ORDER BY date DESC
            """, (user_id,))
            return cursor.fetchall()


class SubscriptionManager:
    """
    Manages Pro subscriptions, bank transfer verification requests,
    and owner administrative approvals.
    """
    BANK_NAME = "UNITED BANK LIMITED"
    BANK_IBAN = "PK58UNIL0109000321329705"

    @staticmethod
    def create_request(user_id: int, sender_name: str, transaction_ref: str, plan_name: str = "Pro Monthly - Rs. 500", amount_paid: float = 0.0, notes: str = ""):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO subscription_requests (user_id, bank_name, iban_number, transaction_ref, sender_name, amount_paid, plan_name, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (
                user_id,
                SubscriptionManager.BANK_NAME,
                SubscriptionManager.BANK_IBAN,
                transaction_ref.strip(),
                sender_name.strip(),
                float(amount_paid or 0.0),
                plan_name.strip(),
                notes.strip()
            ))
            return cursor.lastrowid

    @staticmethod
    def get_user_requests(user_id: int) -> list:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM subscription_requests 
            WHERE user_id = ? 
            ORDER BY created_at DESC
            """, (user_id,))
            return cursor.fetchall()

    @staticmethod
    def get_all_requests() -> list:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT sr.*, u.username, u.email, u.display_name 
            FROM subscription_requests sr
            JOIN users u ON sr.user_id = u.id
            ORDER BY sr.created_at DESC
            """)
            return cursor.fetchall()

    @staticmethod
    def approve_request(request_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM subscription_requests WHERE id = ?", (request_id,))
            row = cursor.fetchone()
            if not row:
                return False
            user_id = row["user_id"]
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE subscription_requests SET status = 'approved', reviewed_at = ? WHERE id = ?", (now_str, request_id))
            cursor.execute("UPDATE users SET subscription_status = 'pro' WHERE id = ?", (user_id,))
            return True

    @staticmethod
    def reject_request(request_id: int, reason: str = "") -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            note_addition = f" [Rejected: {reason}]" if reason else " [Rejected]"
            cursor.execute("""
            UPDATE subscription_requests 
            SET status = 'rejected', notes = COALESCE(notes, '') || ?, reviewed_at = ? 
            WHERE id = ?
            """, (note_addition, now_str, request_id))
            return True

    @staticmethod
    def grant_user_pro(user_identifier: str, is_owner: bool = False) -> bool:
        """Finds user by username or email and upgrades their status."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id FROM users 
            WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)
            """, (user_identifier.strip(), user_identifier.strip()))
            row = cursor.fetchone()
            if not row:
                return False
            uid = row["id"]
            if is_owner:
                cursor.execute("UPDATE users SET is_owner = 1, subscription_status = 'lifetime_owner' WHERE id = ?", (uid,))
            else:
                cursor.execute("UPDATE users SET subscription_status = 'pro' WHERE id = ?", (uid,))
            return True

