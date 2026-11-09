"""
Gym Tracker Pro - Database Engine
Provides SQLite connection management, schema initialization, and query utilities.
"""
import sqlite3
import os
from contextlib import contextmanager

# Supabase / PostgreSQL & Database Migration Support
RAW_DATABASE_URL = os.environ.get("DATABASE_URL")
if RAW_DATABASE_URL and RAW_DATABASE_URL.startswith("postgres://"):
    RAW_DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)

DATABASE_URL = RAW_DATABASE_URL
DB_PATH = os.path.join(os.path.dirname(__file__), "gym_tracker.db")
SQLALCHEMY_DATABASE_URI = DATABASE_URL or f"sqlite:///{DB_PATH}"

def dict_factory(cursor, row):
    """Returns sqlite rows as python dictionaries."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

@contextmanager
def get_db():
    """Context manager for thread-safe SQLite connection with foreign keys and dict factory."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = dict_factory
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initializes all database tables and indexes."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            unit_preference TEXT DEFAULT 'kg',
            daily_calorie_target INTEGER DEFAULT 2500,
            daily_protein_target INTEGER DEFAULT 160,
            daily_carbs_target INTEGER DEFAULT 250,
            daily_fat_target INTEGER DEFAULT 70,
            height REAL DEFAULT 175.0,
            weight REAL DEFAULT 75.0,
            fitness_goal TEXT DEFAULT 'gain_weight',
            gemini_api_key TEXT DEFAULT NULL,
            daily_step_goal INTEGER DEFAULT 10000,
            subscription_status TEXT DEFAULT 'trial',
            trial_ends_at TIMESTAMP,
            is_owner INTEGER DEFAULT 0,
            first_name TEXT DEFAULT NULL,
            fitness_objective TEXT DEFAULT 'tone',
            activity_level TEXT DEFAULT 'moderate',
            gender TEXT DEFAULT 'male',
            dob TEXT DEFAULT NULL,
            goal_weight REAL DEFAULT NULL,
            onboarding_completed INTEGER DEFAULT 0,
            water_goal_ml INTEGER DEFAULT 3000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Migration check for existing databases
        cursor.execute("PRAGMA table_info(users);")
        existing_cols = [c["name"] for c in cursor.fetchall()]
        if "height" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN height REAL DEFAULT 175.0;")
        if "weight" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN weight REAL DEFAULT 75.0;")
        if "fitness_goal" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN fitness_goal TEXT DEFAULT 'gain_weight';")
        if "gemini_api_key" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN gemini_api_key TEXT DEFAULT NULL;")
        if "daily_step_goal" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN daily_step_goal INTEGER DEFAULT 10000;")
        if "subscription_status" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'trial';")
        if "trial_ends_at" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN trial_ends_at TIMESTAMP;")
        if "is_owner" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_owner INTEGER DEFAULT 0;")
        if "first_name" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT NULL;")
        if "fitness_objective" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN fitness_objective TEXT DEFAULT 'tone';")
        if "activity_level" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN activity_level TEXT DEFAULT 'moderate';")
        if "gender" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN gender TEXT DEFAULT 'male';")
        if "dob" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT DEFAULT NULL;")
        if "goal_weight" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN goal_weight REAL DEFAULT NULL;")
        if "onboarding_completed" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN onboarding_completed INTEGER DEFAULT 0;")
        if "water_goal_ml" not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN water_goal_ml INTEGER DEFAULT 3000;")

        # Initialize trial_ends_at for existing users if NULL (7 days / 1 week from creation)
        cursor.execute("""
        UPDATE users 
        SET trial_ends_at = datetime(created_at, '+7 days')
        WHERE trial_ends_at IS NULL;
        """)

        # Workout Sessions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Workout Sets table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            muscle_group TEXT NOT NULL,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            weight REAL NOT NULL,
            reps INTEGER NOT NULL,
            rpe REAL DEFAULT 8.0,
            is_warmup INTEGER DEFAULT 0,
            is_pr INTEGER DEFAULT 0,
            estimated_1rm REAL,
            equipment_type TEXT DEFAULT 'direct',
            equipment_details TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Migration check for workout_sets columns
        cursor.execute("PRAGMA table_info(workout_sets);")
        existing_set_cols = [c["name"] for c in cursor.fetchall()]
        if "equipment_type" not in existing_set_cols:
            cursor.execute("ALTER TABLE workout_sets ADD COLUMN equipment_type TEXT DEFAULT 'direct';")
        if "equipment_details" not in existing_set_cols:
            cursor.execute("ALTER TABLE workout_sets ADD COLUMN equipment_details TEXT DEFAULT NULL;")

        # Nutrition Entries table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            food_name TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Personal Records table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exercise_name TEXT NOT NULL,
            max_weight REAL NOT NULL,
            reps INTEGER NOT NULL,
            estimated_1rm REAL NOT NULL,
            max_volume REAL DEFAULT 0.0,
            date_achieved TEXT NOT NULL,
            set_id INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, exercise_name)
        );
        """)

        # Migration check for personal_records columns
        cursor.execute("PRAGMA table_info(personal_records);")
        existing_pr_cols = [c["name"] for c in cursor.fetchall()]
        if "max_volume" not in existing_pr_cols:
            cursor.execute("ALTER TABLE personal_records ADD COLUMN max_volume REAL DEFAULT 0.0;")

        # Reusable Workout Split Templates table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            split_category TEXT DEFAULT 'Custom',
            exercises_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Daily Steps & Pedometer table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            steps INTEGER DEFAULT 0,
            distance_km REAL DEFAULT 0.0,
            calories_burned REAL DEFAULT 0.0,
            active_minutes INTEGER DEFAULT 0,
            step_goal INTEGER DEFAULT 10000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, date)
        );
        """)

        # Subscription payment verification requests table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscription_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            bank_name TEXT NOT NULL,
            iban_number TEXT NOT NULL,
            transaction_ref TEXT NOT NULL,
            sender_name TEXT,
            amount_paid REAL DEFAULT 0.0,
            plan_name TEXT DEFAULT 'Pro Monthly',
            status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP
        );
        """)

        # Daily Water Consumption table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_water (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            amount_ml INTEGER DEFAULT 0,
            goal_ml INTEGER DEFAULT 3000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, date)
        );
        """)

        # Custom Barcodes Table (Local & Supabase fallback for offline / custom scan items)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_barcodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            food_name TEXT NOT NULL,
            brand TEXT DEFAULT 'Packaged Item',
            serving_size TEXT DEFAULT '100g',
            calories REAL NOT NULL,
            protein REAL DEFAULT 0.0,
            carbs REAL DEFAULT 0.0,
            fat REAL DEFAULT 0.0,
            source TEXT DEFAULT 'custom', -- 'custom', 'ocr', 'openfoodfacts'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Onboarding Profiles Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS onboarding_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            first_name TEXT,
            gender TEXT DEFAULT 'male',
            dob TEXT,
            height REAL,
            weight REAL,
            goal_weight REAL,
            unit_preference TEXT DEFAULT 'kg',
            core_goal TEXT DEFAULT 'gain_weight',
            fitness_objective TEXT DEFAULT 'tone',
            activity_level TEXT DEFAULT 'moderate',
            calculated_bmr REAL,
            calculated_tdee REAL,
            calculated_calories INTEGER,
            calculated_protein INTEGER,
            calculated_carbs INTEGER,
            calculated_fat INTEGER,
            calculated_water_ml INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        );
        """)

        # Direct table aliases / schemas for workouts, prs, and meals
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            total_volume REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            exercise_name TEXT NOT NULL,
            max_weight REAL NOT NULL,
            reps INTEGER NOT NULL,
            estimated_1rm REAL NOT NULL,
            max_volume REAL DEFAULT 0.0,
            date_achieved TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, exercise_name)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            food_name TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON workout_sessions(user_id, date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sets_user_exercise ON workout_sets(user_id, exercise_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nutrition_user_date ON nutrition_entries(user_id, date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prs_user_exercise ON personal_records(user_id, exercise_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_steps_user_date ON daily_steps(user_id, date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_requests_user ON subscription_requests(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workout_templates_user ON workout_templates(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_user_date ON daily_water(user_id, date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_custom_barcodes_code ON custom_barcodes(barcode);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_onboarding_user ON onboarding_profiles(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workouts_user_date ON workouts(user_id, date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prs_lookup ON prs(user_id, exercise_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meals_user_date ON meals(user_id, date);")

        # Ensure permanent Master Owner account exists
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = 'swagger' OR LOWER(email) = 'ghost.5abdullah@gmail.com';")
        if not cursor.fetchone():
            import bcrypt
            salt = bcrypt.gensalt()
            pw_hash = bcrypt.hashpw(b"Swagger.5", salt).decode("utf-8")
            cursor.execute("""
            INSERT INTO users (username, email, password_hash, display_name, unit_preference, height, weight, fitness_goal, daily_step_goal, subscription_status, is_owner)
            VALUES ('swagger', 'ghost.5abdullah@gmail.com', ?, 'Swagger', 'kg', 175.0, 75.0, 'gain_weight', 10000, 'lifetime_owner', 1);
            """, (pw_hash,))

        print("Gym Tracker Pro database initialized successfully.")

if __name__ == "__main__":
    init_db()
