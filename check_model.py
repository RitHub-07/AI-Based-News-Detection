import os
import joblib

MODEL_PATH = "models/best_fake_news_model.pkl"
VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"

def inspect_object(path, name):
    print(f"\n--- {name} ---")
    if not os.path.exists(path):
        print("File not found:", path)
        return

    try:
        obj = joblib.load(path)
        print("Type:", type(obj))
        print("Class:", obj.__class__.__name__)
        print("Module:", obj.__class__.__module__)

        if hasattr(obj, "get_params"):
            try:
                print("Params:", obj.get_params())
            except Exception as e:
                print("Params error:", e)

        if hasattr(obj, "classes_"):
            print("Classes:", obj.classes_)

        if hasattr(obj, "vocabulary_"):
            print("Vocabulary size:", len(obj.vocabulary_))

        if hasattr(obj, "idf_"):
            print("IDF length:", len(obj.idf_))

    except Exception as e:
        print("Load error:", e)

if __name__ == "__main__":
    inspect_object(MODEL_PATH, "MODEL")
    inspect_object(VECTORIZER_PATH, "VECTORIZER")