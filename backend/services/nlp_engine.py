"""
Sentiment Analysis Component (NLP Engine)
Implements multilingual sentiment analysis across English, Urdu (Arabic script),
Roman Urdu, and Hindi transliterated tokens.
Extracts 3 distinct audience sample comments (Positive, Negative, Neutral).
Honest classification: Ambiguous or unclassifiable text is marked unclassified/unavailable.
"""

import re
import html
from textblob import TextBlob

# ─── Multilingual Sentiment Lexicons ─────────────────────────────────────────

# Urdu (Arabic-script) sentiment tokens
URDU_POSITIVE = {
    "بہت اچھا", "زبردست", "شاندار", "بہترین", "عمدہ", "کمال", "پیارا", "خوبصورت",
    "پسند", "مبارک", "شکریہ", "سلام", "مفید", "خوب", "سبحان اللہ", "ماشاءاللہ",
    "جزاک اللہ", "محبت", "شاباش", "لاجواب", "اعلیٰ", "فائدہ مند"
}

URDU_NEGATIVE = {
    "بکواس", "برا", "خراب", "گھٹیا", "جھوٹ", "فراڈ", "فضول", "غلط",
    "نقصان", "بے کار", "بیکار", "نفرت", "لعنت", "مایوس", "تباہ", "دھوکہ",
    "وحیات", "بند کرو", "بدبودار"
}

# Roman Urdu & Hindi transliterated sentiment tokens
ROMAN_POSITIVE = {
    "zabardast", "shandar", "shaandar", "kamaal", "kamal", "behtareen", "behtreen",
    "bohot accha", "bohot acha", "bohat acha", "bohat accha", "achha", "acha", "accha",
    "pyara", "pyaara", "khubsurat", "khoobsurat", "badhiya", "badiya", "lajawab",
    "lajaawab", "shukriya", "mashallah", "mashaallah", "subhanallah", "jazakallah",
    "superb", "mast", "jhakaas", "dhansu", "osm", "sahi", "faadu", "awesome",
    "brilliant", "great", "love", "loved", "best", "perfect", "helpful"
}

ROMAN_NEGATIVE = {
    "bakwas", "ghatiya", "bura", "kharab", "bekar", "fazool", "fuzool", "jhoot",
    "fraud", "galat", "ghalat", "dhoka", "bekaar", "khatam", "chirkut", "faltu",
    "waheeat", "wahiyaat", "wahiyat", "hate", "hated", "worst", "terrible",
    "horrible", "rubbish", "useless", "scam", "cheat", "disappointed", "poor"
}

# Negation words that reverse polarity
NEGATIONS = {"nahi", "nhi", "nahin", "mat", "not", "no", "never", "نہ", "نہیں", "مت"}


def _clean_text(text: str) -> str:
    """
    Cleans text while preserving ASCII alphanumeric and Urdu/Hindi Unicode ranges.
    """
    if not text:
        return ""
    # Strip HTML tags
    t = re.sub(r"<[^>]+>", " ", text)
    # Strip non-alphanumeric except Arabic/Urdu and Devanagari script
    t = re.sub(r"[^\w\s؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿ऀ-ॿ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()


def _clean_comment_display(comment: str) -> str:
    """Strips HTML tags (<br>, <a>) and unescapes entities for clean UI display."""
    if not comment:
        return ""
    text = html.unescape(comment)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_comment(comment: str):
    """
    Classifies a comment into positive, negative, neutral, or unclassified.
    Combines Urdu/Hindi lexicon rules with English TextBlob polarity.
    Flags ambiguous sentiment honestly rather than forcing neutral/positive.
    Returns (label, polarity).
    """
    clean = _clean_text(comment)
    if not clean:
        return "unclassified", 0.0

    # Check for meaningful alphabetic/script characters (not just numbers/spaces)
    if not re.search(r"[a-zA-Z؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿ऀ-ॿ]", clean):
        return "unclassified", 0.0

    words = clean.split()
    if not words:
        return "unclassified", 0.0

    # Multilingual Lexicon Matches
    pos_score = 0
    neg_score = 0

    # Check multi-word tokens in string
    for phrase in URDU_POSITIVE | ROMAN_POSITIVE:
        if " " in phrase and phrase in clean:
            pos_score += 2

    for phrase in URDU_NEGATIVE | ROMAN_NEGATIVE:
        if " " in phrase and phrase in clean:
            neg_score += 2

    # Check single word tokens
    for w in words:
        if w in URDU_POSITIVE or w in ROMAN_POSITIVE:
            pos_score += 1
        elif w in URDU_NEGATIVE or w in ROMAN_NEGATIVE:
            neg_score += 1

    # Check TextBlob polarity for English sentences
    try:
        tb_polarity = TextBlob(clean).sentiment.polarity
    except Exception:
        tb_polarity = 0.0

    # Decision logic
    if pos_score > 0 and neg_score == 0:
        polarity = round(min(1.0, 0.4 + 0.15 * pos_score), 2)
        return "positive", polarity
    elif neg_score > 0 and pos_score == 0:
        polarity = round(max(-1.0, -0.4 - 0.15 * neg_score), 2)
        return "negative", polarity
    elif pos_score > 0 and neg_score > 0:
        # Ambiguous conflicting sentiments
        diff = pos_score - neg_score
        if diff >= 2:
            return "positive", 0.35
        elif diff <= -2:
            return "negative", -0.35
        else:
            # Genuinely ambiguous: flag unclassified rather than guessing
            return "unclassified", 0.0

    # If no lexicon matched, rely on TextBlob polarity
    if tb_polarity > 0.15:
        return "positive", round(tb_polarity, 2)
    elif tb_polarity < -0.15:
        return "negative", round(tb_polarity, 2)
    elif len(words) >= 3 and abs(tb_polarity) <= 0.15:
        # Long enough sentence with factual or neutral tone
        return "neutral", round(tb_polarity, 2)
    else:
        # Too short or ambiguous single words with 0 polarity -> unclassified
        return "unclassified", 0.0


def analyze_sentiment(comment_list):
    """
    Processes a list of real YouTube comments and returns aggregate sentiment scores,
    and extracts 3 distinct audience sample comments (positive, negative, neutral).
    """
    if not comment_list:
        return {
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 0.0,
            "average_polarity": 0.0,
            "dominant_sentiment": "unavailable",
            "sample_comment": "",
            "sample_comments": [],
        }

    counts = {"positive": 0, "negative": 0, "neutral": 0, "unclassified": 0}
    running_total = 0.0

    sample_positive = None
    sample_negative = None
    sample_neutral = None

    for comment in comment_list:
        label, polarity = classify_comment(comment)
        counts[label] += 1
        running_total += polarity

        cleaned_display = _clean_comment_display(comment)
        if not cleaned_display:
            continue

        if label == "positive" and sample_positive is None:
            sample_positive = cleaned_display
        elif label == "negative" and sample_negative is None:
            sample_negative = cleaned_display
        elif label == "neutral" and sample_neutral is None:
            sample_neutral = cleaned_display

    total = max(1, len(comment_list))
    classified_total = counts["positive"] + counts["negative"] + counts["neutral"]

    # Collect distinct sample comments
    sample_comments = []
    if sample_positive:
        sample_comments.append({"sentiment": "positive", "text": sample_positive})
    if sample_negative:
        sample_comments.append({"sentiment": "negative", "text": sample_negative})
    if sample_neutral:
        sample_comments.append({"sentiment": "neutral", "text": sample_neutral})

    primary_sample = sample_comments[0]["text"] if sample_comments else ""

    if classified_total == 0:
        return {
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 0.0,
            "average_polarity": 0.0,
            "dominant_sentiment": "unavailable",
            "sample_comment": primary_sample,
            "sample_comments": sample_comments,
        }

    dominant = max(
        ["positive", "negative", "neutral"],
        key=lambda k: counts[k]
    )

    return {
        "positive_score": round((counts["positive"] / classified_total) * 100, 2),
        "negative_score": round((counts["negative"] / classified_total) * 100, 2),
        "neutral_score": round((counts["neutral"] / classified_total) * 100, 2),
        "average_polarity": round(running_total / classified_total, 3),
        "dominant_sentiment": dominant,
        "sample_comment": primary_sample,
        "sample_comments": sample_comments[:3],
    }
