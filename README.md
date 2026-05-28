# Analysing Natural Language Data: Hedging in Reddit Mental Health Communities

---

## Research question

How do users of Reddit mental health communities use hedging expressions to soften personal claims and manage the risk of sharing difficult experiences? 

---

## Repository contents

```
├── reddit_hedging_scraper.py    
└── README.md                       
```

---
## Dataset Links
- https://www.reddit.com/r/Anxiety/?
- https://www.reddit.com/r/depression/?
---

## How the scraper works

The script (`reddit_hedging_scraper.py`) does the following steps:

1. **Fetches posts** from r/Anxiety and r/depression via Reddit's public JSON API (up to 50 posts per community)
2. **Filters out** removed, deleted and non-English posts at retrieval
3. **Splits** each post into sentences using punctuation-based regex
4. **Searches** each sentence for eight hedge expressions using pre-compiled look-around regex patterns
5. **Removes false positives** — e.g. *a little* next to quantity words like *water* or *food* is excluded
6. **Deduplicates** on hedge–sentence pairs, preserving co-occurrence (a sentence with two hedges is kept for both)
7. **Saves** the cleaned dataset to a timestamped CSV file and prints a summary

### Running the script

**Requirements**

```
Python 3.10+
requests
pandas
```

Install dependencies:

```bash
pip install requests pandas
```

Run:

```bash
python reddit_hedging_scraper.py
```

> **Note:** The script uses Reddit's public JSON API and does not require any API key or authentication. Because it only reads top-level post text, comment-level data is not included.

---

## Dataset structure

| Column | Description |
|---|---|
| `subreddit` | Source community (`Anxiety` or `depression`) |
| `hedge_expression` | The matched hedge phrase (e.g. `i think`) |
| `category` | Category assigned (see below) |
| `matched_sentence` | The full sentence containing the hedge |

---

## Hedge categories

| Category | Expressions | What it does |
|---|---|---|
| Epistemic uncertainty | *maybe*, *probably*, *I guess* | Expresses doubt or reduced certainty about a claim |
| Emotional softening | *kind of*, *sort of*, *a little* | Reduces the emotional intensity of a statement |
| Self-protective stance | *i think*, *i feel like* | Frames experience as personal opinion to lower social risk |

Categories were developed through repeated manual reading of the dataset and are grounded in Hyland's (1996) framework of epistemic modality.

---

## False-positive filter rules

Some hedge expressions appear in non-discursive contexts and are excluded:

| Hedge | Excluded when these words appear nearby |
|---|---|
| *a little* | water, food, money, bit, amount, sugar, salt |
| *kind of* | music, genre, type, category, sort |
| *sort of* | sorted, sort the, sorting |
| *i think* | i think therefore, computer, device |


