import requests
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import feedparser

# ============================
# API KEYS
# ============================

NEWS_API_KEY = "8fb84925f40946a6be0515f317d2b69d"
GNEWS_API_KEY = "7e35bc1cc80010142a1d6f1f3f4adf5d"
GOOGLE_API_KEY = "AIzaSyAGpTeGDrRDx_4qOirW28MYrJkB1RaIAv8"

# ============================
# OUTPUT FILE
# ============================

OUTPUT_FILE = "combined_news_dataset_2026.json"

dataset = []

# ============================
# NEWS API
# ============================

def fetch_newsapi():

    print("Fetching NewsAPI...")

    queries = [
        "india",
        "world",
        "technology",
        "sports",
        "business",
        "politics",
        "health",
        "science"
        "education",
    "economy",
    "finance",
    "startup",
    "ai",
    "artificial intelligence",
    "cybersecurity",
    "climate",
    "space",
    "isro",
    "nasa",
    "cricket",
    "football",
    "olympics",
    "entertainment",
    "bollywood",
    "hollywood"
    ]

    for q in queries:

        params = {
            "q": q,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 100,
            "apiKey": "8fb84925f40946a6be0515f317d2b69d"
        }

        r = requests.get(
            "https://newsapi.org/v2/everything",
            params=params
        )

        if r.status_code != 200:
            print(q, "failed")
            continue

        articles = r.json().get("articles", [])

        for a in articles:

            dataset.append({

                "title": a.get("title"),

                "text": a.get("description"),

                "content": a.get("content"),

                "source": a.get("source", {}).get("name"),

                "date": a.get("publishedAt"),

                "label": "REAL"

            })

        print(q, len(articles))


# ============================
# GNEWS
# ============================

def fetch_gnews():

    print("Fetching GNews...")

    url="https://gnews.io/api/v4/search"

    params={

        "q":"news",

        "lang":"en",

        "max":100,

        "apikey":"7e35bc1cc80010142a1d6f1f3f4adf5d"
    }

    r=requests.get(url,params=params)

    if r.status_code!=200:

        print("GNews Error")

        return

    articles=r.json().get("articles",[])

    for a in articles:

        dataset.append({

            "title":a.get("title"),

            "text":a.get("description"),

            "content":a.get("content"),

            "source":a.get("source",{}).get("name"),

            "date":a.get("publishedAt"),

            "label":"REAL"

        })

    print(len(articles),"articles added.")
    
# ============================
# GOOGLE FACT CHECK
# ============================

def fetch_google_factcheck():

    print("Fetching Google Fact Check...")

    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    queries = [
        "fake",
        "false",
        "misinformation",
        "covid",
        "election",
        "politics",
        "AI",
        "war",
        "health",
        "vaccine",
        "india",
        "usa",
        "climate"
    ]

    params = {
        "languageCode": "en",
        "key": "AIzaSyAGpTeGDrRDx_4qOirW28MYrJkB1RaIAv8"
    }

    try:

        total = 0

        for q in queries:

            params["query"] = q

            r = requests.get(url, params=params, timeout=10)

            if r.status_code != 200:
                continue

            claims = r.json().get("claims", [])

            for claim in claims:

                review = claim.get("claimReview", [{}])[0]

                dataset.append({

                    "title": claim.get("text", ""),

                    "text": claim.get("text", ""),

                    "content": claim.get("text", ""),

                    "source": review.get("publisher", {}).get("name", "Google Fact Check"),

                    "date": review.get("reviewDate", datetime.now().strftime("%Y-%m-%d")),

                    "label": "FAKE"

                })

                total += 1

        print(total, "fake claims added.")

    except Exception as e:

        print("Google Fact Check:", e)


# ============================
# RSS NEWS FETCHER
# ============================

RSS_FEEDS = [

# International
"https://feeds.bbci.co.uk/news/rss.xml",
"https://rss.cnn.com/rss/edition.rss",
"https://www.reutersagency.com/feed/?best-topics=news",
"https://apnews.com/hub/ap-top-news?output=rss",
"https://feeds.skynews.com/feeds/rss/home.xml",

# India
"https://www.thehindu.com/news/?service=rss",
"https://feeds.feedburner.com/ndtvnews-top-stories",
"https://indianexpress.com/section/india/feed/",
"https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
"https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",

# Tech
"https://feeds.arstechnica.com/arstechnica/index",
"https://www.theverge.com/rss/index.xml",
"https://techcrunch.com/feed/",

# Business
"https://www.cnbc.com/id/100003114/device/rss/rss.html",
"https://www.moneycontrol.com/rss/latestnews.xml",

# Sports
"https://www.espn.com/espn/rss/news",
"https://www.skysports.com/rss/12040",

# Science
"https://www.sciencedaily.com/rss/all.xml"


]


def fetch_rss():

    print("Fetching RSS Feeds...")

    total = 0

    for feed_url in RSS_FEEDS:

        try:

            feed = feedparser.parse(feed_url)

            for entry in feed.entries:

                dataset.append({

                    "title": getattr(entry, "title", ""),

                    "text": getattr(entry, "summary", ""),

                    "content": getattr(entry, "summary", ""),

                    "source": getattr(feed.feed, "title", "RSS"),

                    "date": getattr(entry, "published", datetime.now().strftime("%Y-%m-%d")),

                    "label": "REAL"

                })

                total += 1

        except:

            pass

    print(total, "RSS articles added.")    

# ============================
# REMOVE DUPLICATES
# ============================

def remove_duplicates():

    global dataset

    print("\nRemoving duplicate articles...")

    unique = {}

    for article in dataset:

        key = (
            str(article.get("title", "")).strip().lower()
            + str(article.get("source", "")).strip().lower()
        )

        unique[key] = article

    dataset = list(unique.values())

    print(f"Dataset Size : {len(dataset)}")


# ============================
# SAVE DATASET
# ============================

def save_dataset():

    print("\nSaving Dataset...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        json.dump(dataset, f, indent=4, ensure_ascii=False)

    print(f"\nDataset Saved Successfully : {OUTPUT_FILE}")


# ============================
# MAIN
# ============================

if __name__ == "__main__":

    print("=" * 60)
    print("AUTO DATASET GENERATOR")
    print("=" * 60)

    fetch_newsapi()

    fetch_gnews()

    fetch_google_factcheck()

    fetch_rss()

    remove_duplicates()

    save_dataset()

    print("=" * 60)
    print("Completed Successfully")
    print("=" * 60)    