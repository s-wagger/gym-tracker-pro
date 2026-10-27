# GYM TRACKER PRO

**High-Performance Progressive Web Application (PWA) for Workout Tracking & Fitness Analytics**

![Gym Tracker Pro Header](static/icons/icon-192.png)

---

## 1. Executive Summary & Core Objectives

**Gym Tracker Pro** is a modern, high-contrast full-stack web application designed for individual workout tracking and personal fitness analytics. It enables users to log daily training sessions, track personal records (PRs), compute estimated 1-Rep Max (1RM) metrics, monitor daily caloric intake and macro splits, and export comprehensive training history to standard CSV format.

The platform is explicitly optimized for deployment as an installable **Progressive Web App (PWA)**, allowing native-like operational capability on mobile devices (iOS and Android) while bypassing app store registration fees and approval delays.

---

## 2. Architectural System Modules

| Module Reference | Module Name | Primary Functions & Capabilities |
| :--- | :--- | :--- |
| **M1** | **User Access Control** | User registration, password hashing (`bcrypt`), session management (`Flask-Login`), and account maintenance routes for profile configurations and unit preferences (`kg`/`lbs`). |
| **M2** | **Interface & Experience** | High-contrast dark aesthetic (#121212 slate, #1E1E1E cards, #CCFF00 neon lime, #FFD700 gold), 3D card tilt interactions, micro-animations, public dynamic landing page with motivational quotes and live 1RM preview. |
| **M3** | **Personal Hub Dashboard** | Dynamic user welcome header, motivational feeds with instant refresh, quick-glance KPI metrics, and structured 3D tilt routing cards to all operational modules. |
| **M4** | **Exercise Logger** | Dynamic multi-set entries (weight, reps, RPE, warmup toggle), workout logging with muscle group and exercise presets (plus custom exercise support), live session volume tally, and filterable session history (muscle group, exercise name, date). |
| **M5** | **Nutrition & Macro Tracker** | Itemized meal logging (Breakfast, Lunch, Dinner, Snack, Post-Workout), daily caloric budget progress bars, and macronutrient balance tracking (Protein, Carbohydrates, Fat) with visual targets vs. consumption progress. |
| **M6** | **1RM Analytical Engine** | Formula-driven calculation engine implementing the standard Epley equation: $1\text{RM} = W \times (1 + \frac{R}{30})$, formula comparison with Brzycki & Lombardi, and automatic generation of periodized training zones (50%, 75%, 85%, 90% of 1RM). |
| **M7** | **PR Analytics & Milestones** | Centralized record dashboard aggregating maximum weight achieved across key lifts (Bench Press, Back Squat, Deadlift, Overhead Press), automated all-time record detection for newly logged sets, milestone club badges (1000-lb Club, 225lb Bench, etc.), and Chart.js progression curves. |
| **M8** | **Data Export Subsystem** | Full user-owned data portability offering one-click localized generation and export of entire user datasets: `workouts.csv`, `nutrition.csv`, `personal_records.csv`, and complete master archive `complete_data.zip`. |

---

## 3. Technology Stack & PWA Infrastructure

- **Backend API**: Python 3 (Flask, Flask-Login, Werkzeug)
- **Database Engine**: SQLite 3 with context managers, foreign keys (`PRAGMA foreign_keys = ON;`), and dictionary factories
- **Cryptography & Security**: `bcrypt` salted password hashing
- **Frontend UI/UX**: HTML5, Tailwind CSS, Vanilla JS, CSS 3D Transforms (custom tilt interactions), Chart.js
- **PWA Infrastructure**:
  - `manifest.json`: Standalone display mode, theme colors (`#121212`), high-contrast icons, quick launcher shortcuts
  - `sw.js`: Service worker implementing asset pre-caching, network-first page navigation, and cache fallback
  - `offline.html`: Custom branded offline shell

---

## 4. Mathematical Formula Specification

### 1-Rep Max (1RM) Standard Formula
Gym Tracker Pro implements the established **Epley Formula** as its primary analytical standard:

$$\text{1RM} = W \times \left(1 + \frac{R}{30}\right)$$

Where:
- $W$ = Weight lifted (in preferred unit: kg or lbs)
- $R$ = Repetitions completed ($R = 1 \implies 1\text{RM} = W$)

### Periodized Training Zones Breakdown
The system automatically generates structured training percentages from the calculated 1RM:

| Zone Percentage | Rep Range | Intensity Category | Primary Training Stimulus |
| :--- | :--- | :--- | :--- |
| **100% 1RM** | 1 Rep | Maximum Effort | True 1RM Test / Competition Peak |
| **95% 1RM** | 1 - 2 Reps | Very High | Neural recruitment & heavy singles |
| **90% 1RM** | 3 - 4 Reps | High | Maximum strength development |
| **85% 1RM** | 5 - 6 Reps | Sub-Maximal | Strength-hypertrophy & myofibrillar growth |
| **80% 1RM** | 7 - 8 Reps | Moderate-High | Optimal muscle hypertrophy & size |
| **75% 1RM** | 9 - 10 Reps | Moderate | High volume hypertrophy & work capacity |
| **70% 1RM** | 11 - 12 Reps | Moderate | Muscular endurance & conditioning |
| **60% 1RM** | 12 - 15 Reps | Light-Moderate | Dynamic effort & explosive bar speed |
| **50% 1RM** | 15 - 20 Reps | Light | Active recovery, deload, & motor drilling |

---

## 5. Mobile PWA Installation Protocol

Gym Tracker Pro runs directly in any modern mobile browser without downloading from an app store:

### Android (Chrome / Edge):
1. Open the hosted URL in Google Chrome.
2. Tap the **"Install App"** button in the header or tap Chrome's three-dot menu `⋮`.
3. Select **"Add to Home screen"** or **"Install App"**.
4. Gym Tracker Pro will install to your app drawer and run in standalone fullscreen mode.

### iOS (Safari):
1. Open the hosted URL in Safari.
2. Tap the **Share** button (box with an arrow pointing up) at the bottom.
3. Scroll down and tap **"Add to Home Screen"**.
4. Tap **Add** in the top right. Launch directly from your home screen.

---

## 6. Getting Started & Setup

### Prerequisites
- Python 3.10+
- `pip`

### Installation
1. Clone or navigate to the project directory:
   ```bash
   cd "GYM TRACKER"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database and seed demo data:
   ```bash
   python seed_demo_data.py
   ```
   *This seeds a ready-to-test athlete profile with past workouts, key PRs, and meals:*
   - **Username**: `demo_athlete`
   - **Password**: `password123`

4. Launch the application:
   ```bash
   python app.py
   ```
   Open your browser at `http://127.0.0.1:5000`.

---

## 7. Running Automated Tests

A comprehensive unit test suite is included, verifying the mathematical formulas, database integrity, bcrypt password security, automatic PR detection, nutrition calculations, and PWA endpoints:

```bash
python -m unittest tests/test_gym_tracker.py
```

All 13 test suites verify:
- Epley 1RM formula correctness
- Training zones percentage breakdowns
- Bcrypt password hashing & authentication
- Multi-set logging & automated all-time record detection
- Itemized nutrition logging and daily macronutrient sums
- One-click CSV and ZIP data generation
- PWA Web App Manifest and Service Worker validity

---

## 8. Directory Structure

```
GYM TRACKER/
│
├── app.py                     # Main Flask application and API route endpoints
├── config.py                  # Application configuration & secret keys
├── database.py                # Thread-safe SQLite engine with foreign keys
├── models.py                  # User, Workout, Nutrition, PR, & Export managers
├── formulas.py                # 1RM standard math, training zones, & milestones
├── seed_demo_data.py          # Demo profile generator with workouts & PRs
├── generate_icons.py          # PWA icon generator (192, 512, maskable)
├── requirements.txt           # Python dependency requirements
├── README.md                  # Complete architectural & operational manual
│
├── static/
│   ├── css/
│   │   └── style.css          # High-contrast theme (#121212, #CCFF00, #FFD700)
│   ├── js/
│   │   ├── app.js             # 3D tilt engine, dynamic quotes, toasts
│   │   ├── pwa.js             # Service Worker registration & install prompts
│   │   ├── logger.js          # Dynamic set adder/remover, PR notifications
│   │   ├── nutrition.js       # Macro progress bars & itemized meal tracker
│   │   ├── calculator.js      # Interactive 1RM engine & training zones
│   │   └── analytics.js       # Chart.js progression curves & volume history
│   ├── icons/
│   │   ├── icon-192.png       # 192x192 PWA icon
│   │   ├── icon-512.png       # 512x512 PWA icon
│   │   ├── icon-maskable.png  # 512x512 maskable adaptive icon
│   │   ├── apple-touch-icon.png
│   │   └── favicon.png
│   ├── manifest.json          # Web App Manifest specification
│   └── sw.js                  # Service Worker with pre-caching & offline fallback
│
├── templates/
│   ├── base.html              # Base shell with nav, bottom bar, toasts, PWA headers
│   ├── landing.html           # Public landing page with CTA, 3D cards, quote card
│   ├── dashboard.html         # Personal Hub dashboard with 3D routing & KPIs
│   ├── workouts.html          # Dynamic multi-set workout logger & history
│   ├── nutrition.html         # Calorie & Macro tracker with target progress bars
│   ├── one_rep_max.html       # 1RM Analytical Engine & periodized training zones
│   ├── analytics.html         # Key lift PRs, milestones, & Chart.js graph
│   ├── export.html            # One-click localized CSV and ZIP export engine
│   ├── profile.html           # Target macro configurations & bcrypt security
│   ├── offline.html           # PWA offline fallback shell
│   └── auth/
│       ├── login.html         # High-contrast login interface
│       └── register.html      # Athlete registration with unit preferences
│
└── tests/
    └── test_gym_tracker.py    # Complete automated unit test suite
```
