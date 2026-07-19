import pandas as pd
import json
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.metrics import accuracy_score

# Load JSON dataset
with open("combined_news_dataset_2026.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Merge real + fake news
all_news = data["real_news"] + data["fake_news"]

# Convert to DataFrame
df = pd.DataFrame(all_news)

# Create text column
df["text"] = df["headline"] + " " + df["description"]

# Features and labels
X = df["text"]
y = df["label"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer(stop_words='english')

X_train_vectorized = vectorizer.fit_transform(X_train)
X_test_vectorized = vectorizer.transform(X_test)

# Train model
model = PassiveAggressiveClassifier(max_iter=1000)

model.fit(X_train_vectorized, y_train)

# Prediction
y_pred = model.predict(X_test_vectorized)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)

print("Accuracy:", accuracy * 100)

# Save model and vectorizer
joblib.dump(model, "fake_news_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model Saved Successfully")