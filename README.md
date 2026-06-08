## ✨ Features
 
### Core
- 🔐 User authentication — Sign Up, Login, Logout
- 🗂️ 7 ingredient categories — Vegetables, Fruits, Spices, Meat, Grains, Dairy, Other
- 📋 Recipe history — every recipe you save is stored per user
- 👤 Profile page — change username and upload a profile picture
### Filtering & Search
- 🥦 **Veg / Non-Veg filter** — show only vegetarian or non-vegetarian recipes
- ⚡ **Difficulty filter** — Easy, Medium, or Hard
- 🔍 **Search bar** on history page — search saved recipes by name
- ⭐ **Favourites** — star any saved recipe, filter history by favourites only
### ML & Recommendations
- 🎯 **Strict match mode** — only shows recipes that contain ALL selected ingredients
- 🔄 **Flexible match mode** — shows recipes with at least 40% ingredient overlap (always returns results)
- 🤖 **ML mode (TF-IDF + Cosine Similarity)** — ranks recipes by ingredient relevance, shows a match score % bar on each card
- 👥 **Collaborative filtering** — recommends recipes saved by users with similar tastes
---
 
## 🛠️ Tech Stack
 
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Django 5.2 |
| ML Engine | scikit-learn (TF-IDF, NearestNeighbors, cosine similarity) |
| Database | SQLite (via Django ORM) |
| Frontend | Bootstrap 5.3, Font Awesome 6, vanilla JS |
| Data | pandas, openpyxl (Excel datasets) |
| Media | Pillow (profile image uploads) |
 
---
 
## 📁 Project Structure
 
```
recipegen/
├── manage.py
├── requirements.txt
├── db.sqlite3
│
├── receipe_dashboard/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                   # Main Django app
│   ├── models.py               # Profile, Recipe, RecipeHistory, UserRecipeInteraction
│   ├── views.py                # All views (home, dashboard, recommend, history, profile)
│   ├── urls.py                 # URL routing
│   ├── forms.py                # UserUpdateForm, ProfileUpdateForm
│   ├── signals.py              # Auto-create Profile on user signup
│   ├── admin.py
│   ├── migrations/
│   └── templates/
│       ├── base.html           # Sidebar layout shared across all pages
│       ├── home.html
│       ├── login.html
│       ├── signup.html
│       ├── dashboard.html      # Category cards + filter bar
│       ├── recommend.html      # Recipe result cards
│       ├── history.html        # Saved recipes with search/filter
│       └── profile.html        # Edit profile modal
│
├── ml_model/                   # ML package
│   ├── recommend.py            # All recommendation logic
│   ├── train_model.py          # Training script (TF-IDF + NearestNeighbors)
│   ├── recipe_model.pkl        # Trained model (auto-generated)
│   ├── vectorizer.pkl          # Trained vectorizer (auto-generated)
│   ├── Recipe Dataset.xlsx     # 168 recipes with ingredients, steps, difficulty
│   └── ingredient_categories.xlsx  # Ingredients grouped by category
│
├── static/
│   └── css/main.css
└── media/
    └── default.jpg             # Default profile picture
```
 
---
 
## 🚀 How to Run
 
### Prerequisites
- Python 3.10 or higher
- pip
### 1. Extract and navigate
 
**Windows:**
```
Right-click recipegen.zip → Extract All → Desktop
```
Then open Command Prompt:
```cmd
cd C:\Users\YourName\Desktop\recipegen\recipegen
```
 
**Mac / Linux:**
```bash
unzip recipegen.zip
cd recipegen/recipegen
```
 
### 2. Create a virtual environment
```bash
python -m venv venv
```
 
Activate it:
```bash
# Windows
venv\Scripts\activate
 
# Mac / Linux
source venv/bin/activate
```
 
You should see `(venv)` at the start of your terminal prompt.
 
### 3. Install dependencies
```bash
pip install -r requirements.txt
```
 
### 4. Run database migrations
```bash
python manage.py migrate
```
 
### 5. (Optional) Create an admin account
```bash
python manage.py createsuperuser
```
 
### 6. (Optional) Retrain the ML model
```bash
python ml_model/train_model.py
```
The pre-trained `.pkl` files are already included, so this step is only needed if you modify the dataset.
 
### 7. Start the server
```bash
python manage.py runserver
```
 
Open your browser and go to: **http://127.0.0.1:8000**
 
---
 
## 🧠 How the ML Works
 
### Dataset
`Recipe Dataset.xlsx` contains **168 recipes** with:
- Recipe name
- Ingredients (comma-separated)
- Difficulty level (easy / medium / hard)
- Steps to cook
- Is vegetarian (True / False)
### Two Recommendation Modes
 
**Mode 1 — Subset Match (default)**
```
User selects: ["banana", "milk", "honey"]
 
For each recipe in dataset:
  Does recipe contain banana AND milk AND honey?
    YES → include it
    NO  → skip
 
Strict: ALL ingredients must match
Flexible: at least 40% must match
```
 
**Mode 2 — ML Mode (TF-IDF + Cosine Similarity)**
```
User selects: ["banana", "milk"]
         ↓
Query string: "banana milk"
         ↓
TF-IDF vectorizer converts it to a numeric vector
         ↓
Cosine similarity calculated against all 168 recipe vectors
         ↓
Top 10 most similar recipes returned, ranked by score %
```
This always returns results and works even with just one ingredient.
 
**Mode 3 — Collaborative Filtering**
```
You saved: Banana Smoothie, Yogurt Smoothie
User B saved: Banana Smoothie, Banana Pancakes
User C saved: Yogurt Smoothie, Mango Lassi
 
→ RecipeGen recommends: Banana Pancakes, Mango Lassi to you
```
Powered by the `UserRecipeInteraction` table which logs every recipe saved.
 
---
 
## 🗃️ Database Models
 
```python
Profile               # One-to-one with User; stores profile image
Recipe                # User-created recipe entries
RecipeHistory         # Recipes saved via "Use" button; includes
                      # difficulty_level, is_veg, is_favorite
UserRecipeInteraction # Log of all saves; powers collaborative filtering
```
 
---
 
## 🔌 API Endpoints
 
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Home / landing page |
| GET/POST | `/signup/` | Create account |
| GET/POST | `/login/` | Login |
| GET | `/logout/` | Logout |
| GET | `/dashboard/` | Main dashboard |
| POST | `/recommend/` | Get recipe recommendations |
| POST | `/save-recipe/` | Save a recipe to history |
| GET | `/history/` | View saved recipe history |
| POST | `/history/favorite/<pk>/` | Toggle favourite (AJAX) |
| POST | `/history/delete/<pk>/` | Delete from history (AJAX) |
| GET/POST | `/profile/` | View and edit profile |
| GET | `/admin/` | Django admin panel |
 
---
 
## 🔮 Possible Future Improvements
 
- **Claude API integration** — Generate brand new recipes on the fly using AI instead of searching a fixed dataset
- **Nutrition info** — Display calories, macros per recipe
- **Shopping list** — Export selected ingredients as a shopping list
- **Recipe ratings** — Let users rate recipes 1–5 stars for better collaborative filtering
- **Social sharing** — Share a recipe via a public link
- **Recipe upload** — Let users add their own recipes to the dataset
- **Mobile app** — React Native frontend backed by Django REST API
- **Docker deployment** — Containerise with Docker Compose for easy cloud deployment
---
 
## 🐛 Known Issues & Notes
 
- The ML model (`.pkl` files) is pre-trained and included. If you add recipes to the dataset, re-run `python ml_model/train_model.py` to retrain.
- Collaborative filtering only activates once multiple users have saved recipes — it returns no suggestions for brand new accounts.
- Profile images are stored locally in `media/profile_pics/`. For production, configure an S3 bucket via `django-storages`.
- `DEBUG = True` is set for local development. Set it to `False` and configure `ALLOWED_HOSTS` before any public deployment.
