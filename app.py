"""
Gym Tracker Pro - Main Flask Application Server
Progressive Web Application (PWA) with complete fitness analytics,
workout logging, 1RM engine, macro tracking, and CSV data export.
"""
import io
import csv
import zipfile
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    jsonify, send_file, send_from_directory, Response, make_response
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)

from config import Config
from database import init_db
from models import (
    User, WorkoutManager, NutritionManager,
    AnalyticsManager, ExportManager
)
from formulas import (
    calculate_epley_1rm, calculate_brzycki_1rm,
    calculate_lombardi_1rm, get_training_zones, evaluate_milestones
)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access Gym Tracker Pro."
login_manager.login_message_category = "info"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

# PWA Static Routes (Service Worker and Manifest)
@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")

@app.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory("static", "sw.js", mimetype="application/javascript"))
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route("/offline.html")
def offline():
    return render_template("offline.html")

# -------------------------------------------------------------
# Module 2: Landing Page & Micro-Interactions
# -------------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

# -------------------------------------------------------------
# Module 1: User Access Control & Security
# -------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        display_name = request.form.get("display_name", "").strip()
        unit_pref = request.form.get("unit_preference", "kg")

        # Validation
        if not username or not email or not password:
            flash("All fields marked with an asterisk are required.", "error")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/register.html")

        if User.get_by_username(username):
            flash("Username is already taken. Please choose another.", "error")
            return render_template("auth/register.html")

        if User.get_by_email(email):
            flash("An account with this email address already exists.", "error")
            return render_template("auth/register.html")

        try:
            user = User.create(
                username=username,
                email=email,
                password=password,
                display_name=display_name or username,
                unit_preference=unit_pref
            )
            login_user(user)
            flash(f"Welcome to Gym Tracker Pro, {user.display_name}! 💪", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("Registration failed due to a server error. Please try again.", "error")
            return render_template("auth/register.html")

    return render_template("auth/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not identifier or not password:
            flash("Please provide your username/email and password.", "error")
            return render_template("auth/login.html")

        # Check by email or username
        user = User.get_by_email(identifier) if "@" in identifier else User.get_by_username(identifier)
        if not user:
            # Fallback check both
            user = User.get_by_username(identifier) or User.get_by_email(identifier)

        if user and user.verify_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.display_name}! Ready to crush today's goals?", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        else:
            flash("Invalid username/email or password.", "error")
            return render_template("auth/login.html")

    return render_template("auth/login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            display_name = request.form.get("display_name", "").strip()
            unit_pref = request.form.get("unit_preference", "kg")
            calories = int(request.form.get("daily_calorie_target") or 2500)
            protein = int(request.form.get("daily_protein_target") or 160)
            carbs = int(request.form.get("daily_carbs_target") or 250)
            fat = int(request.form.get("daily_fat_target") or 70)

            current_user.update_profile(display_name, unit_pref, calories, protein, carbs, fat)
            flash("Profile preferences and nutrition targets updated successfully!", "success")

        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_new_password", "")

            if not current_user.verify_password(current_pw):
                flash("Current password is incorrect.", "error")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "error")
            elif len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "error")
            else:
                current_user.update_password(new_pw)
                flash("Password updated successfully!", "success")

        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)

# -------------------------------------------------------------
# Module 3: Personal Hub (Dashboard)
# -------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    summary = AnalyticsManager.get_dashboard_summary(current_user)
    return render_template("dashboard.html", user=current_user, summary=summary)

# -------------------------------------------------------------
# Module 4: Workout & Exercise Logger
# -------------------------------------------------------------
@app.route("/workouts")
@login_required
def workouts():
    today_str = datetime.now().strftime("%Y-%m-%d")
    sessions = WorkoutManager.get_user_workouts(current_user.id)
    return render_template("workouts.html", user=current_user, sessions=sessions, today=today_str)

@app.route("/api/workouts", methods=["GET"])
@login_required
def api_get_workouts():
    muscle = request.args.get("muscle")
    exercise = request.args.get("exercise")
    date = request.args.get("date")
    sessions = WorkoutManager.get_user_workouts(current_user.id, muscle, exercise, date)
    return jsonify({"success": True, "sessions": sessions})

@app.route("/api/workouts/log", methods=["POST"])
@login_required
def api_log_workout():
    data = request.get_json() or {}
    title = data.get("title", "Training Session")
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    notes = data.get("notes", "")
    sets = data.get("sets", [])

    if not sets:
        return jsonify({"success": False, "error": "No exercise sets provided."}), 400

    result = WorkoutManager.log_workout_session(current_user.id, title, date, notes, sets)
    return jsonify({"success": True, **result})

@app.route("/api/workouts/<int:session_id>", methods=["DELETE"])
@login_required
def api_delete_workout(session_id):
    success = WorkoutManager.delete_session(session_id, current_user.id)
    return jsonify({"success": success})

# -------------------------------------------------------------
# Module 5: Calorie & Macro Tracking
# -------------------------------------------------------------
@app.route("/nutrition")
@login_required
def nutrition():
    today_str = datetime.now().strftime("%Y-%m-%d")
    nutrition_data = NutritionManager.get_daily_nutrition(current_user.id, today_str)
    targets = {
        "calories": current_user.daily_calorie_target,
        "protein": current_user.daily_protein_target,
        "carbs": current_user.daily_carbs_target,
        "fat": current_user.daily_fat_target
    }
    return render_template(
        "nutrition.html",
        user=current_user,
        today=today_str,
        nutrition=nutrition_data,
        targets=targets
    )

@app.route("/api/nutrition", methods=["GET"])
@login_required
def api_get_nutrition():
    date_str = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    nutrition_data = NutritionManager.get_daily_nutrition(current_user.id, date_str)
    targets = {
        "calories": current_user.daily_calorie_target,
        "protein": current_user.daily_protein_target,
        "carbs": current_user.daily_carbs_target,
        "fat": current_user.daily_fat_target
    }
    return jsonify({
        "success": True,
        "date": date_str,
        "totals": nutrition_data["totals"],
        "grouped": nutrition_data["grouped"],
        "targets": targets
    })

@app.route("/api/nutrition/log", methods=["POST"])
@login_required
def api_log_nutrition():
    data = request.get_json() or {}
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    meal_type = data.get("meal_type", "Snack")
    food_name = data.get("food_name", "").strip()
    calories = float(data.get("calories", 0))
    protein = float(data.get("protein", 0))
    carbs = float(data.get("carbs", 0))
    fat = float(data.get("fat", 0))

    if not food_name:
        return jsonify({"success": False, "error": "Food item name is required."}), 400

    entry_id = NutritionManager.log_meal(
        user_id=current_user.id,
        date=date,
        meal_type=meal_type,
        food_name=food_name,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat
    )
    return jsonify({"success": True, "entry_id": entry_id})

@app.route("/api/nutrition/<int:entry_id>", methods=["DELETE"])
@login_required
def api_delete_nutrition(entry_id):
    success = NutritionManager.delete_meal(entry_id, current_user.id)
    return jsonify({"success": success})

# -------------------------------------------------------------
# Module 6: 1RM Analytical Engine
# -------------------------------------------------------------
@app.route("/one-rep-max")
@login_required
def one_rep_max():
    distinct_exercises = AnalyticsManager.get_distinct_exercises(current_user.id)
    if not distinct_exercises:
        distinct_exercises = ["Bench Press", "Back Squat", "Deadlift", "Overhead Press"]
    return render_template(
        "one_rep_max.html",
        user=current_user,
        exercises=distinct_exercises
    )

@app.route("/api/1rm/calculate", methods=["GET", "POST"])
def api_calculate_1rm():
    if request.method == "POST":
        data = request.get_json() or {}
        weight = float(data.get("weight", 0))
        reps = int(data.get("reps", 0))
        unit = data.get("unit", "kg")
    else:
        weight = float(request.args.get("weight", 0))
        reps = int(request.args.get("reps", 0))
        unit = request.args.get("unit", "kg")

    epley = calculate_epley_1rm(weight, reps)
    brzycki = calculate_brzycki_1rm(weight, reps)
    lombardi = calculate_lombardi_1rm(weight, reps)
    zones = get_training_zones(epley, unit=unit)

    return jsonify({
        "weight": weight,
        "reps": reps,
        "unit": unit,
        "epley_1rm": epley,
        "brzycki_1rm": brzycki,
        "lombardi_1rm": lombardi,
        "training_zones": zones
    })

@app.route("/api/prs/save", methods=["POST"])
@login_required
def api_save_calculated_pr():
    data = request.get_json() or {}
    exercise = data.get("exercise_name")
    weight = float(data.get("weight", 0))
    reps = int(data.get("reps", 0))
    est_1rm = float(data.get("estimated_1rm", 0))
    date = data.get("date") or datetime.now().strftime("%Y-%m-%d")

    if not exercise or weight <= 0 or reps <= 0:
        return jsonify({"success": False, "error": "Invalid PR data"}), 400

    from database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO personal_records (user_id, exercise_name, max_weight, reps, estimated_1rm, date_achieved)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, exercise_name) DO UPDATE SET
            max_weight = MAX(max_weight, excluded.max_weight),
            reps = CASE WHEN excluded.max_weight >= max_weight THEN excluded.reps ELSE reps END,
            estimated_1rm = MAX(estimated_1rm, excluded.estimated_1rm),
            date_achieved = excluded.date_achieved,
            updated_at = CURRENT_TIMESTAMP
        """, (current_user.id, exercise, weight, reps, est_1rm, date))

    return jsonify({"success": True})

# -------------------------------------------------------------
# Module 7: PR Analytics & Milestones
# -------------------------------------------------------------
@app.route("/analytics")
@login_required
def analytics():
    records = AnalyticsManager.get_personal_records(current_user.id)
    key_prs = AnalyticsManager.get_key_prs(current_user.id)
    distinct_exercises = AnalyticsManager.get_distinct_exercises(current_user.id)
    if not distinct_exercises:
        distinct_exercises = ["Bench Press", "Back Squat", "Deadlift", "Overhead Press"]

    dashboard_summary = AnalyticsManager.get_dashboard_summary(current_user)
    milestones = dashboard_summary["milestones"]

    return render_template(
        "analytics.html",
        user=current_user,
        records=records,
        key_prs=key_prs,
        exercises=distinct_exercises,
        milestones=milestones
    )

@app.route("/api/analytics/progression")
@login_required
def api_analytics_progression():
    exercise = request.args.get("exercise", "Bench Press")
    days = request.args.get("days", type=int)
    points = AnalyticsManager.get_progression_data(current_user.id, exercise, days)
    return jsonify({"success": True, "exercise": exercise, "points": points})

@app.route("/api/analytics/volume-history")
@login_required
def api_analytics_volume():
    sessions = WorkoutManager.get_user_workouts(current_user.id, limit=20)
    # Reverse so it flows chronologically
    chronological = list(reversed(sessions))
    return jsonify({"success": True, "sessions": chronological})

# -------------------------------------------------------------
# Module 8: Data Export Engine
# -------------------------------------------------------------
@app.route("/export")
@login_required
def export_view():
    return render_template("export.html", user=current_user)

@app.route("/export/workouts.csv")
@login_required
def export_workouts_csv():
    data = ExportManager.get_workouts_csv_data(current_user.id)
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Date", "Workout Title", "Muscle Group", "Exercise Name",
        "Set Number", "Weight", "Reps", "RPE", "Is Warmup",
        "Is Personal Record", "Estimated 1RM", "Total Volume", "Notes"
    ])
    
    for row in data:
        writer.writerow([
            row["date"],
            row["title"],
            row["muscle_group"],
            row["exercise_name"],
            row["set_number"],
            row["weight"],
            row["reps"],
            row["rpe"],
            "Yes" if row["is_warmup"] else "No",
            "Yes" if row["is_pr"] else "No",
            row["estimated_1rm"],
            row["volume"],
            row["notes"]
        ])

    output.seek(0)
    filename = f"gym_tracker_workouts_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/export/nutrition.csv")
@login_required
def export_nutrition_csv():
    data = ExportManager.get_nutrition_csv_data(current_user.id)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Date", "Meal Type", "Food Name", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)", "Logged At"])

    for row in data:
        writer.writerow([
            row["date"],
            row["meal_type"],
            row["food_name"],
            row["calories"],
            row["protein"],
            row["carbs"],
            row["fat"],
            row["created_at"]
        ])

    output.seek(0)
    filename = f"gym_tracker_nutrition_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/export/prs.csv")
@login_required
def export_prs_csv():
    data = ExportManager.get_prs_csv_data(current_user.id)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Exercise Name", "Max Weight", "Reps", "Estimated 1RM", "Date Achieved", "Last Updated"])

    for row in data:
        writer.writerow([
            row["exercise_name"],
            row["max_weight"],
            row["reps"],
            row["estimated_1rm"],
            row["date_achieved"],
            row["updated_at"]
        ])

    output.seek(0)
    filename = f"gym_tracker_personal_records_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/export/all")
@login_required
def export_all_zip():
    """Generates an in-memory ZIP package containing all 3 exported CSV datasets."""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Workouts
        workouts_data = ExportManager.get_workouts_csv_data(current_user.id)
        w_io = io.StringIO()
        w_writer = csv.writer(w_io)
        w_writer.writerow([
            "Date", "Workout Title", "Muscle Group", "Exercise Name",
            "Set Number", "Weight", "Reps", "RPE", "Is Warmup",
            "Is Personal Record", "Estimated 1RM", "Total Volume", "Notes"
        ])
        for r in workouts_data:
            w_writer.writerow([
                r["date"], r["title"], r["muscle_group"], r["exercise_name"],
                r["set_number"], r["weight"], r["reps"], r["rpe"],
                "Yes" if r["is_warmup"] else "No", "Yes" if r["is_pr"] else "No",
                r["estimated_1rm"], r["volume"], r["notes"]
            ])
        zf.writestr("workouts.csv", w_io.getvalue().encode("utf-8"))

        # 2. Nutrition
        nutr_data = ExportManager.get_nutrition_csv_data(current_user.id)
        n_io = io.StringIO()
        n_writer = csv.writer(n_io)
        n_writer.writerow(["Date", "Meal Type", "Food Name", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)", "Logged At"])
        for r in nutr_data:
            n_writer.writerow([r["date"], r["meal_type"], r["food_name"], r["calories"], r["protein"], r["carbs"], r["fat"], r["created_at"]])
        zf.writestr("nutrition.csv", n_io.getvalue().encode("utf-8"))

        # 3. PRs
        prs_data = ExportManager.get_prs_csv_data(current_user.id)
        p_io = io.StringIO()
        p_writer = csv.writer(p_io)
        p_writer.writerow(["Exercise Name", "Max Weight", "Reps", "Estimated 1RM", "Date Achieved", "Last Updated"])
        for r in prs_data:
            p_writer.writerow([r["exercise_name"], r["max_weight"], r["reps"], r["estimated_1rm"], r["date_achieved"], r["updated_at"]])
        zf.writestr("personal_records.csv", p_io.getvalue().encode("utf-8"))

    zip_buffer.seek(0)
    zip_filename = f"gym_tracker_complete_data_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.zip"
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zip_filename
    )

# -------------------------------------------------------------
# Application Initializer
# -------------------------------------------------------------
with app.app_context():
    init_db()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
