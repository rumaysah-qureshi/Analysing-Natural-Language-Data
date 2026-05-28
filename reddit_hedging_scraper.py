import re
import time
import requests
import pandas as pd
from datetime import datetime

# CONFIGURATION

SUBREDDITS = ["Anxiety", "depression"]
POST_LIMIT = 50    # posts fetched per subreddit (Reddit API max per call)
MIN_WORDS  = 5     # minimum sentence length to include a match
SLEEP_SEC  = 2     # polite delay between subreddit requests (avoid 429s)

HEADERS = {
    # Identify the scraper to Reddit's servers – required to avoid 403 errors
    "User-Agent": "Mozilla/5.0 (compatible; LinguisticsCourseworkBot/1.0; SPC4004)"
}


# HEDGE TAXONOMY

HEDGES = {
    "maybe":       "Epistemic uncertainty",
    "probably":    "Epistemic uncertainty",
    "i guess":     "Epistemic uncertainty",
    "kind of":     "Emotional softening",
    "sort of":     "Emotional softening",
    "a little":    "Emotional softening",
    "i think":     "Self-protective stance",
    "i feel like": "Self-protective stance",
}


# FALSE-POSITIVE FILTER RULES

FALSE_POSITIVE_CONTEXTS = {
    "a little":   ["water", "food", "money", "bit", "amount", "sugar", "salt"],
    "kind of":    ["music", "genre", "type", "category", "sort"],
    "sort of":    ["sorted", "sort the", "sorting"],
    "i think":    ["i think therefore", "computer", "device"],
}


# PRE-COMPILE REGEX PATTERNS

PATTERNS = {}

for hedge_phrase in HEDGES:
    PATTERNS[hedge_phrase] = re.compile(
        r"(?<!\w)" + re.escape(hedge_phrase) + r"(?!\w)",
        re.IGNORECASE
    )

# SCRAPE

results = []

for sub in SUBREDDITS:
    print(f"\nFetching r/{sub} ...")

    # Request the subreddit 
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit={POST_LIMIT}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
    except requests.RequestException as exc:
        print(f"  Network error fetching r/{sub}: {exc}")
        response = None

    # Handle rate-limiting with a single retry
    if response is not None and response.status_code == 429:
        print(f"  Rate-limited on r/{sub} – waiting 10 s then retrying")
        time.sleep(10)
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
        except requests.RequestException as exc:
            print(f"  Retry also failed for r/{sub}: {exc}")
            response = None

    # Skip this subreddit on any non-200 response 
    if response is None or response.status_code != 200:
        if response is not None:
            print(f"  HTTP {response.status_code} for r/{sub} – skipping")
        time.sleep(SLEEP_SEC)
        continue

    posts = response.json()["data"]["children"]
    print(f"  Retrieved {len(posts)} posts")

    # Iterate over every post 
    for post in posts:
        title    = post["data"].get("title", "")
        selftext = post["data"].get("selftext", "")

        # Exclude placeholder strings for removed/deleted posts
        if selftext in ("[removed]", "[deleted]", ""):
            full_text = title
        else:
            full_text = f"{title}. {selftext}"

        # Split post text into sentences 
        sentences = re.split(r"(?<=[.!?])\s+", full_text.strip())

        # Track (hedge, sentence) pairs already recorded for this post to prevent the same pair being appended more than once
        seen_in_post = set()

        # Check each hedge expression against this post 
        for hedge, category in HEDGES.items():
            pattern = PATTERNS[hedge]

            # Fast check on the full post before iterating sentences
            if not pattern.search(full_text.lower()):
                continue

            # Find the first sentence containing this hedge
            for sentence in sentences:
                if not pattern.search(sentence.lower()):
                    continue

                sentence_clean = sentence.strip()

                # Enforce minimum sentence length
                if len(sentence_clean.split()) < MIN_WORDS:
                    continue

                # False-positive filter
                fp_words = FALSE_POSITIVE_CONTEXTS.get(hedge, [])
                sentence_lower = sentence_clean.lower()
                is_false_positive = any(w in sentence_lower for w in fp_words)

                if is_false_positive:
                    continue

                # Deduplication
                pair = (hedge, sentence_clean)
                if pair in seen_in_post:
                    continue
                seen_in_post.add(pair)

                results.append({
                    "subreddit":        sub,
                    "hedge_expression": hedge,
                    "category":         category,
                    "matched_sentence": sentence_clean,
                })

                # Take only the first matching sentence per hedge per post
                break

    time.sleep(SLEEP_SEC)


# BUILD AND CLEAN DATAFRAME

df = pd.DataFrame(results)

if df.empty:
    print("df empty")

else:
    # Remove rows with empty or missing sentences 
    df = df.dropna(subset=["matched_sentence"])
    df = df[df["matched_sentence"].str.strip().ne("")]

    # Deduplicate 
    df = df.drop_duplicates(subset=["hedge_expression", "matched_sentence"])

    df = df.reset_index(drop=True)

    # Save dataset 
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = f"reddit_hedging_dataset_{timestamp}.csv"
    df.to_csv(output_path, index=False)
    print(f"\nDataset saved to: {output_path}")

    # Summary statistics
    print(f"\nTotal examples:    {len(df)}")
    print(f"Unique subreddits: {df['subreddit'].nunique()}")

    print("\n--- Examples by category ---")
    print(df["category"].value_counts().to_string())

    print("\n--- Examples by subreddit ---")
    print(df["subreddit"].value_counts().to_string())

    print("\n--- Examples by hedge expression ---")
    print(df["hedge_expression"].value_counts().to_string())

    print("\n--- Cross-tabulation: subreddit × category ---")
    print(df.groupby(["subreddit", "category"]).size().unstack(fill_value=0).to_string())

    print("\n--- Sample rows ---")
    print(df[["subreddit", "hedge_expression", "category", "matched_sentence"]]
          .head(10).to_string(index=False))