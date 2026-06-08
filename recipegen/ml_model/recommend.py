import pandas as pd
import numpy as np
import os
import re
import pickle
from django.conf import settings


# ─────────────────────────────────────────────
# Dataset paths
# ─────────────────────────────────────────────
def _path(filename):
    return os.path.join(settings.BASE_DIR, 'ml_model', filename)


# ─────────────────────────────────────────────
# Ingredient Categories Loader
# ─────────────────────────────────────────────
def load_ingredient_categories():
    df = pd.read_excel(_path('ingredient_categories.xlsx'))
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Category', 'Ingredient'])

    cats = {}
    for _, row in df.iterrows():
        cat = str(row['Category']).strip()
        ing = str(row['Ingredient']).strip()
        if cat and ing:
            cats.setdefault(cat, []).append(ing)

    for cat in cats:
        cats[cat] = list(dict.fromkeys(cats[cat]))
    return cats


def get_ingredient_categories():
    return load_ingredient_categories()


# ─────────────────────────────────────────────
# Recipe Dataset Loader
# ─────────────────────────────────────────────
def load_recipes():
    data = pd.read_excel(_path('Recipe Dataset.xlsx'))
    data.columns = data.columns.str.strip().str.lower().str.replace(' ', '_')

    rename_map = {}
    if 'recipe_name' in data.columns:
        rename_map['recipe_name'] = 'name'
    elif 'recipe' in data.columns:
        rename_map['recipe'] = 'name'

    for candidate in ['steps_to_cook', 'steps', 'number_of_steps']:
        if candidate in data.columns:
            rename_map[candidate] = 'steps'
            break

    data.rename(columns=rename_map, inplace=True)

    if 'difficulty_level' not in data.columns:
        data['difficulty_level'] = 'easy'
    if 'is_veg' not in data.columns:
        data['is_veg'] = True

    data['ingredients'] = data['ingredients'].fillna('')
    data['steps'] = data['steps'].fillna('')
    data['difficulty_level'] = data['difficulty_level'].str.lower().str.strip()
    data['is_veg'] = data['is_veg'].astype(bool)

    return data


# ─────────────────────────────────────────────
# Ingredient Normalizer
# ─────────────────────────────────────────────
def normalize_ingredients(ingredient_text):
    text = str(ingredient_text).lower()
    ingredients = set()
    for part in text.split(','):
        part = part.strip()
        if not part:
            continue
        parens = re.findall(r'\((.*?)\)', part)
        if parens:
            for p in parens:
                for item in re.split(r'[/,]', p):
                    t = item.strip()
                    if t:
                        ingredients.add(t)
            part = re.sub(r'\(.*?\)', '', part).strip()
        if part:
            ingredients.add(part)
    return ingredients


# ─────────────────────────────────────────────
# Parse steps from text
# ─────────────────────────────────────────────
def parse_steps(steps_text):
    text = str(steps_text)
    if ';' in text:
        return [s.strip() for s in text.split(';') if s.strip()]
    elif '\n' in text:
        return [s.strip() for s in text.split('\n') if s.strip()]
    else:
        return [text.strip()] if text.strip() else []


# ─────────────────────────────────────────────
# Build recipe dict from a dataframe row
# ─────────────────────────────────────────────
def _row_to_recipe(row):
    return {
        'name': str(row['name']),
        'ingredients': str(row['ingredients']),
        'difficulty_level': str(row.get('difficulty_level', 'easy')).lower(),
        'is_veg': bool(row.get('is_veg', True)),
        'steps': parse_steps(row['steps']),
    }


# ─────────────────────────────────────────────
# Subset Match Recommendation (strict / flexible)
# ─────────────────────────────────────────────
def subset_recommend(selected_ingredients, diet=None, difficulty=None, match_mode='strict'):
    if not selected_ingredients:
        return []

    data = load_recipes()
    selected_set = {i.lower().strip() for i in selected_ingredients}

    # Apply veg/non-veg filter
    if diet == 'veg':
        data = data[data['is_veg'] == True]
    elif diet == 'nonveg':
        data = data[data['is_veg'] == False]

    # Apply difficulty filter
    if difficulty and difficulty != 'all':
        data = data[data['difficulty_level'] == difficulty.lower()]

    results = []
    for _, row in data.iterrows():
        recipe_ings = normalize_ingredients(row['ingredients'])
        if match_mode == 'strict':
            match = selected_set.issubset(recipe_ings)
        else:
            # Flexible: at least 1 ingredient matches (or 40% if many selected)
            overlap = len(selected_set & recipe_ings)
            threshold = max(1, int(len(selected_set) * 0.4))
            match = overlap >= threshold

        if match:
            results.append(_row_to_recipe(row))

    return results


# ─────────────────────────────────────────────
# ML Recommendation (TF-IDF + NearestNeighbors)
# ─────────────────────────────────────────────
def ml_recommend(selected_ingredients, diet=None, difficulty=None, n=10):
    if not selected_ingredients:
        return []

    vectorizer_path = _path('vectorizer.pkl')
    model_path = _path('recipe_model.pkl')

    if not os.path.exists(vectorizer_path) or not os.path.exists(model_path):
        # Fall back to subset if model not trained yet
        return subset_recommend(selected_ingredients, diet, difficulty, match_mode='flexible')

    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    data = load_recipes()

    # Apply filters before ML scoring
    filtered = data.copy()
    if diet == 'veg':
        filtered = filtered[filtered['is_veg'] == True]
    elif diet == 'nonveg':
        filtered = filtered[filtered['is_veg'] == False]
    if difficulty and difficulty != 'all':
        filtered = filtered[filtered['difficulty_level'] == difficulty.lower()]

    if filtered.empty:
        return []

    # Vectorize query
    query = ' '.join(selected_ingredients).lower().replace(',', ' ')
    query_vec = vectorizer.transform([query])

    # Vectorize filtered recipes
    filtered_vecs = vectorizer.transform(
        filtered['ingredients'].str.lower().str.replace(',', ' ')
    )

    # Cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    scores = cosine_similarity(query_vec, filtered_vecs)[0]

    # Get top-n indices
    top_n = min(n, len(scores))
    top_indices = np.argsort(scores)[::-1][:top_n]

    results = []
    for idx in top_indices:
        if scores[idx] > 0.05:   # minimum relevance threshold
            row = filtered.iloc[idx]
            r = _row_to_recipe(row)
            r['score'] = round(float(scores[idx]) * 100, 1)
            results.append(r)

    return results


# ─────────────────────────────────────────────
# Collaborative Filtering
# ─────────────────────────────────────────────
def collaborative_recommend(user, n=6):
    """
    Find users who saved similar recipes and recommend
    what they saved that the current user hasn't seen.
    """
    try:
        from accounts.models import UserRecipeInteraction

        # Get current user's saved recipe titles
        my_titles = set(
            UserRecipeInteraction.objects.filter(user=user)
            .values_list('recipe_title', flat=True)
        )

        if not my_titles:
            return []

        # Find other users who saved at least one same recipe
        from django.contrib.auth.models import User as DjangoUser
        from django.db.models import Count

        similar_users = (
            UserRecipeInteraction.objects
            .filter(recipe_title__in=my_titles)
            .exclude(user=user)
            .values('user')
            .annotate(shared=Count('recipe_title'))
            .order_by('-shared')
            .values_list('user', flat=True)[:20]
        )

        if not similar_users:
            return []

        # Get recipes those users saved that current user hasn't
        candidate_titles = (
            UserRecipeInteraction.objects
            .filter(user__in=similar_users)
            .exclude(recipe_title__in=my_titles)
            .values('recipe_title', 'ingredients')
            .annotate(saves=Count('recipe_title'))
            .order_by('-saves')[:n]
        )

        results = []
        data = load_recipes()
        for item in candidate_titles:
            title = item['recipe_title']
            match = data[data['name'].str.lower() == title.lower()]
            if not match.empty:
                results.append(_row_to_recipe(match.iloc[0]))
            else:
                # Reconstruct from saved interaction data
                results.append({
                    'name': title,
                    'ingredients': item['ingredients'],
                    'difficulty_level': 'easy',
                    'is_veg': True,
                    'steps': [],
                })
        return results

    except Exception:
        return []


# ─────────────────────────────────────────────
# Main entry point used by views
# ─────────────────────────────────────────────
def recommend_recipe(selected_ingredients, diet=None, difficulty=None,
                     match_mode='strict', use_ml=False):
    if use_ml:
        return ml_recommend(selected_ingredients, diet, difficulty)
    else:
        return subset_recommend(selected_ingredients, diet, difficulty, match_mode)
