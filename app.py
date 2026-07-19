from flask import Flask, render_template, request
import os
import time
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

FACTCHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
NEWSAPI_URL = "https://newsapi.org/v2/everything"

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

model = None
vectorizer = None

try:
    import joblib
    model = joblib.load("models/best_fake_news_model.pkl")
    vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
    print("ML components loaded successfully")
except Exception as e:
    print(f"Model loading error: {e}")


def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_search_query(text):
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    stop_terms = {
        "the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "or",
        "in", "on", "for", "with", "as", "by", "at", "from", "that", "this",
        "it", "be", "has", "have", "had"
    }
    filtered = [w for w in words if w.lower() not in stop_terms]
    if not filtered:
        filtered = words
    return " ".join(filtered[:12])


def google_fact_check(text):
    print("[Google Fact Check] called")
    if not GOOGLE_API_KEY:
        print("[Google Fact Check] missing API key")
        return {"status": "Unavailable", "reason": "Missing GOOGLE_API_KEY"}

    try:
        query = build_search_query(text)
        params = {
            "query": query[:150],
            "languageCode": "en",
            "pageSize": 5,
            "key": GOOGLE_API_KEY
        }
        r = requests.get(FACTCHECK_URL, params=params, timeout=10)
        print("[Google Fact Check] URL:", r.url)
        print("[Google Fact Check] Status code:", r.status_code)
        print("[Google Fact Check] Body:", r.text[:500])

        data = r.json()
        claims = data.get("claims", [])
        if not claims:
            return {"status": "Not Found"}

        claim = claims[0]
        reviews = claim.get("claimReview", [])
        if not reviews:
            return {
                "status": "Found",
                "claim": claim.get("text", ""),
                "rating": "Unknown",
                "publisher": "Unknown",
                "url": "#"
            }

        review = reviews[0]
        return {
            "status": "Found",
            "claim": claim.get("text", ""),
            "rating": review.get("textualRating", "Unknown"),
            "publisher": review.get("publisher", {}).get("name", "Unknown"),
            "url": review.get("url", "#")
        }

    except Exception as e:
        print("[Google Fact Check] error:", e)
        return {"status": "Unavailable", "error": str(e)}


def news_search(text):
    print("[NewsAPI] called")
    if not NEWS_API_KEY:
        print("[NewsAPI] missing API key")
        return {"status": "Unavailable", "reason": "Missing NEWS_API_KEY"}

    try:
        query = build_search_query(text)
        params = {
            "q": query[:120],
            "language": "en",
            "pageSize": 5,
            "searchIn": "title,content",
            "sortBy": "relevancy",
            "apiKey": NEWS_API_KEY
        }
        r = requests.get(NEWSAPI_URL, params=params, timeout=10)
        print("[NewsAPI] URL:", r.url)
        print("[NewsAPI] Status code:", r.status_code)
        print("[NewsAPI] Body:", r.text[:500])

        data = r.json()
        articles = data.get("articles", [])
        if not articles:
            return {"status": "Not Found", "count": 0, "sources": []}

        sources = []
        for a in articles:
            src = a.get("source", {}).get("name")
            if src and src not in sources:
                sources.append(src)

        return {"status": "Found", "count": len(articles), "sources": sources[:5]}

    except Exception as e:
        print("[NewsAPI] error:", e)
        return {"status": "Unavailable", "error": str(e)}


def groq_verify(text):
    print("[Groq] called")
    if not groq_client:
        print("[Groq] missing API key")
        return "Unavailable: Missing GROQ_API_KEY"

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful news-analysis assistant. "
                        "Give one short reason whether the text looks credible or suspicious. "
                        "Do not say REAL or FAKE."
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0
        )
        answer = completion.choices[0].message.content.strip()
        print("[Groq] response:", answer)
        return answer
    except Exception as e:
        print("[Groq] error:", e)
        return f"Unavailable: {e}"


@app.route("/")
def home():
    stats = {"accuracy": "99.80%", "articles": "25K", "models_count": 4}
    return render_template(
        "index.html",
        stats=stats,
        section="home",
        prediction_done=False,
        live_data={"status": "N/A"},
        groq_result="N/A",
        news_verification={"status": "N/A"},
        confidence=0,
        prob_fake=0,
        prob_real=0,
        processing_time=0,
        result="N/A",
        final_status="N/A",
        any_found=False
    )


@app.route("/checker")
def checker():
    return render_template(
        "index.html",
        section="checker",
        prediction_done=False,
        live_data={"status": "N/A"},
        groq_result="N/A",
        news_verification={"status": "N/A"},
        confidence=0,
        prob_fake=0,
        prob_real=0,
        processing_time=0,
        result="N/A",
        final_status="N/A",
        any_found=False
    )


@app.route("/predict", methods=["POST"])
def predict():
    print("=== /predict called ===")
    start_time = time.time()
    text = request.form.get("news_text", "").strip()
    print("Input text length:", len(text))

    if not text:
        print("No text entered")
        return render_template(
            "index.html",
            prediction_done=False,
            section="checker",
            error="Please enter news text.",
            live_data={"status": "N/A"},
            groq_result="N/A",
            news_verification={"status": "N/A"},
            confidence=0,
            prob_fake=0,
            prob_real=0,
            processing_time=0,
            result="N/A",
            final_status="N/A",
            any_found=False
        )

    current_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    result = "NEEDS VERIFICATION"
    final_status = "NEEDS VERIFICATION"
    confidence = 0
    prob_fake = 0
    prob_real = 0
    live_data = {"status": "Skipped"}
    news_verification = {"status": "Skipped"}
    groq_result = "Skipped"

    try:
        if model is None or vectorizer is None:
            print("Model/vectorizer missing")
            return render_template(
                "index.html",
                prediction_done=False,
                section="checker",
                error="Model or Vectorizer not loaded.",
                live_data={"status": "N/A"},
                groq_result="N/A",
                news_verification={"status": "N/A"},
                confidence=0,
                prob_fake=0,
                prob_real=0,
                processing_time=0,
                result="N/A",
                final_status="N/A",
                any_found=False
            )

        clean_text = preprocess_text(text)
        print("Clean text:", clean_text[:200])

        vector = vectorizer.transform([clean_text])
        prediction = model.predict(vector)[0]
        probabilities = model.predict_proba(vector)[0]

        classes = list(model.classes_)
        proba_map = {cls: prob for cls, prob in zip(classes, probabilities)}

        prob_fake = round(float(proba_map.get(0, 0)) * 100, 2)
        prob_real = round(float(proba_map.get(1, 0)) * 100, 2)
        confidence = round(max(probabilities) * 100, 2)

        result = "REAL" if prediction == 1 else "FAKE"
        final_status = result

        print("Prediction:", prediction)
        print("Model classes:", classes)
        print("Probabilities:", probabilities)
        print("Prob fake:", prob_fake)
        print("Prob real:", prob_real)
        print("Result:", result)
        print("Confidence:", confidence)

    except Exception as e:
        print("Prediction Error:", e)
        result = "ERROR"
        final_status = "ERROR"

    if len(text) > 40:
        live_data = google_fact_check(text)
        news_verification = news_search(text)
        groq_result = groq_verify(text)
    else:
        print("Skipping live verification due to short text")

    any_found = (
        live_data.get("status") == "Found" or
        news_verification.get("status") == "Found"
    )

    groq_lower = groq_result.lower() if isinstance(groq_result, str) else ""
    suspicious = any(word in groq_lower for word in [
        "suspicious", "unlikely", "fake", "unusual", "not credible", "questionable"
    ])

    if result == "REAL" and not any_found and suspicious:
        final_status = "NEEDS VERIFICATION"
    elif result == "FAKE":
        final_status = "FAKE"

    processing_time = round(time.time() - start_time, 2)
    print("Processing time:", processing_time)
    print("Final status:", final_status)
    print("Any found:", any_found)

    return render_template(
        "index.html",
        prediction_done=True,
        section="checker",
        original_text=text,
        result=result,
        final_status=final_status,
        confidence=confidence,
        prob_fake=prob_fake,
        prob_real=prob_real,
        timestamp=current_time,
        processing_time=processing_time,
        live_data=live_data,
        groq_result=groq_result,
        news_verification=news_verification,
        any_found=any_found
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    error = None
    success = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            error = "All fields are required."
        elif "@" not in email or "." not in email:
            error = "Please enter a valid email address."
        else:
            success = "Message sent successfully!"

    return render_template(
        "index.html",
        section="contact",
        error=error,
        success=success,
        prediction_done=False,
        live_data={"status": "N/A"},
        groq_result="N/A",
        news_verification={"status": "N/A"},
        confidence=0,
        prob_fake=0,
        prob_real=0,
        processing_time=0,
        result="N/A",
        final_status="N/A",
        any_found=False
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)