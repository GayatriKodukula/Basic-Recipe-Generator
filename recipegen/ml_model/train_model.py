"""
RecipeGen – ML Model Training Script
Run:  python ml_model/train_model.py
"""
import os, sys, pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, 'Recipe Dataset.xlsx')
MODEL_PATH = os.path.join(SCRIPT_DIR, 'recipe_model.pkl')
VECTORIZER_PATH = os.path.join(SCRIPT_DIR, 'vectorizer.pkl')


def train():
    print("Loading dataset...")
    data = pd.read_excel(DATASET_PATH)
    data.columns = data.columns.str.strip().str.lower().str.replace(' ', '_')
    data['ingredients'] = data['ingredients'].fillna('').str.lower().str.replace(',', ' ')
    print(f"Loaded {len(data)} recipes.")

    print("Vectorizing with TF-IDF...")
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(data['ingredients'])

    print("Training NearestNeighbors (cosine)...")
    model = NearestNeighbors(metric='cosine', algorithm='brute')
    model.fit(X)

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(VECTORIZER_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)

    print(f"Saved: {MODEL_PATH}")
    print(f"Saved: {VECTORIZER_PATH}")
    print("Done!")


if __name__ == '__main__':
    train()
