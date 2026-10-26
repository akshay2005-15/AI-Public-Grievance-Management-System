import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

DATA_PATH = "dataset/complaints.csv"
MODEL_DIR = "models"

data = pd.read_csv(DATA_PATH).dropna().drop_duplicates()
X = data["complaint"].astype(str)
y = data["category"].astype(str)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

model = LogisticRegression(max_iter=1000, class_weight="balanced")
model.fit(X_train_vec, y_train)

predictions = model.predict(X_test_vec)
print("Model training completed.")
print(f"Test accuracy: {accuracy_score(y_test, predictions) * 100:.2f}%")
print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(model, os.path.join(MODEL_DIR, "grievance_model.pkl"))
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
print("\nSaved model files in the models folder.")
