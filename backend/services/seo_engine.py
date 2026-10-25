"""
Plexudo YouTube SEO Intelligence Engine v1
===========================================
Pure, deterministic heuristic evaluation of YouTube video metadata.
No external network calls, no clock, no database access, no randomness.

DISCLAIMER:
"Plexudo metadata heuristic, not a YouTube ranking factor"
YouTube's search and discovery algorithm relies on viewer engagement,
retention, CTR, and satisfaction. This engine evaluates metadata quality,
readability, search snippet optimization, and compliance with YouTube guidelines.
"""

import re
import unicodedata
from collections import Counter
from typing import Any

ENGINE_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
DISCLAIMER_TEXT = "Plexudo metadata heuristic, not a YouTube ranking factor"

# -----------------------------------------------------------------------------
# Stopword Dictionaries
# Stopwords never count toward keyword repetition or relevance calculations.
# -----------------------------------------------------------------------------

ENGLISH_STOPWORDS: set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "itself", "just", "me", "more", "most", "my", "myself", "no", "nor",
    "not", "now", "of", "off", "on", "once", "only", "or", "other", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours",
    "yourself", "yourselves",
}

# Roman Urdu stopwords explicitly specified in contract
ROMAN_URDU_STOPWORDS: set[str] = {
    "hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "me", "par", "aur", "ya",
    "kaise", "kya", "kyun", "ye", "yeh", "wo", "woh", "ek", "apna", "apne", "apni",
    "liye", "tak", "bhi", "to", "karo", "karein", "karna", "tha", "thi", "the",
    "wala", "wali", "wale", "kuch", "sab", "ab", "kab", "jab", "batao", "chahye",
}

# Urdu script stopwords for native Nastaliq/Arabic-script support
URDU_SCRIPT_STOPWORDS: set[str] = {
    "ہے", "ہیں", "کا", "کی", "کے", "کو", "سے", "میں", "پر", "اور", "یا",
    "کیسے", "کیا", "کیوں", "یہ", "وہ", "ایک", "اپنا", "اپنے", "اپنى",
    "لیے", "تک", "بھی", "تو", "تھا", "تھی", "تھے", "کریں", "کرو", "کرنا",
}

ALL_STOPWORDS: set[str] = ENGLISH_STOPWORDS | ROMAN_URDU_STOPWORDS | URDU_SCRIPT_STOPWORDS


# -----------------------------------------------------------------------------
# Pure Text Normalization & Tokenization Utilities
# -----------------------------------------------------------------------------

def normalize_text(text: str | None) -> str:
    """Normalize text using Unicode NFKC and casefolding for robust cross-script matching."""
    if not text:
        return ""
    return unicodedata.normalize("NFKC", str(text)).casefold()


def tokenize(text: str | None) -> list[str]:
    """
    Extract alphanumeric word tokens supporting Latin, Urdu, Hindi, Devanagari, etc.
    Strips punctuation while retaining natural word boundaries across scripts.
    """
    norm = normalize_text(text)
    if not norm:
        return []
    # Match any sequence of unicode word characters, preserving hyphenated compounds if alphanumeric
    raw_tokens = re.findall(r"(?u)\b[\w'-]+\b", norm)
    tokens: list[str] = []
    for t in raw_tokens:
        clean = t.strip("'-")
        if clean:
            tokens.append(clean)
    return tokens


def get_content_tokens(tokens: list[str]) -> list[str]:
    """Filter out stopwords and single-character noise; retains semantic content words."""
    return [t for t in tokens if t not in ALL_STOPWORDS and len(t) > 1]


# -----------------------------------------------------------------------------
# Component Scoring Functions
# -----------------------------------------------------------------------------

def calculate_youtube_tag_chars(tags: list[str]) -> int:
    """
    Calculate the exact character count enforced by YouTube Studio and the YouTube Data API.
    Multi-word tags (or tags containing whitespace or commas) are wrapped in quotation marks ("..."),
    and all tags are joined by comma separators.
    """
    clean_tags = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
    if not clean_tags:
        return 0
    total = 0
    for t in clean_tags:
        if t.startswith('"') and t.endswith('"') and len(t) >= 2:
            total += len(t)
        elif any(c in t for c in (" ", "\t", ",")):
            total += len(t) + 2
        else:
            total += len(t)
    total += max(0, len(clean_tags) - 1)
    return total


def evaluate_title(title: str) -> dict[str, Any]:
    """
    Evaluate Title Quality (Max 25 points).
    Rationale:
    - Length: YouTube allows max 100 characters. 30-70 characters is optimal for CTR
      and mobile search snippet readability without cut-off.
    - All-caps: Hurting readability and triggering clickbait spam filters.
    - Word repetition: Inefficient and looks spammy in short titles.
    - Punctuation: Excessive punctuation (!!!, ???) degrades trustworthiness.
    - Content depth: Must convey clear topic keywords beyond generic fillers.
    """
    clean_title = (title or "").strip()
    char_len = len(clean_title)
    tokens = tokenize(clean_title)
    content_tokens = get_content_tokens(tokens)

    checks: list[dict[str, Any]] = []
    suggestions: list[dict[str, Any]] = []

    # 1. Length scoring (10 points)
    length_pts = 0
    if 30 <= char_len <= 70:
        length_pts = 10
        checks.append({
            "id": "title_length",
            "component": "title",
            "status": "pass",
            "message": f"Optimal title length ({char_len} characters, fits mobile screens without truncation)."
        })
    elif 20 <= char_len < 30:
        length_pts = 7
        checks.append({
            "id": "title_length",
            "component": "title",
            "status": "warn",
            "message": f"Title is slightly short ({char_len} chars). 30-70 chars provides stronger context."
        })
        suggestions.append({
            "priority": 3,
            "impact": "medium",
            "component": "title",
            "message": "Expand title with key benefit or format (e.g., 'Step-by-Step Guide' or 'in 2026').",
            "fix": "Add a descriptive secondary clause to reach 30-70 characters."
        })
    elif 71 <= char_len <= 80:
        length_pts = 7
        checks.append({
            "id": "title_length",
            "component": "title",
            "status": "warn",
            "message": f"Title is {char_len} chars. It may truncate on some mobile search screens."
        })
    elif 81 <= char_len <= 100:
        length_pts = 4
        checks.append({
            "id": "title_length",
            "component": "title",
            "status": "warn",
            "message": f"Title is {char_len} chars and will truncate on mobile search results (70+ chars)."
        })
        suggestions.append({
            "priority": 2,
            "impact": "high",
            "component": "title",
            "message": "Front-load critical keywords and trim title below 70 characters.",
            "fix": "Shorten title to under 70 characters so the core hook is visible on mobile."
        })
    elif char_len > 100:
        length_pts = 0
        checks.append({
            "id": "title_length",
            "component": "title",
            "status": "fail",
            "message": f"Title exceeds YouTube's 100-character maximum ({char_len} chars)."
        })
        suggestions.append({
            "priority": 1,
            "impact": "critical",
            "component": "title",
            "message": "Shorten title immediately. YouTube will reject or truncate titles exceeding 100 chars.",
            "fix": "Trim title to 70 characters or fewer."
        })
    else:  # char_len < 20
        length_pts = 3 if char_len > 0 else 0
        checks.append({
            "id": "title_length",
            "component": "title",
            "status": "fail" if char_len == 0 else "warn",
            "message": "Title is empty." if char_len == 0 else f"Title is very short ({char_len} chars)."
        })
        suggestions.append({
            "priority": 1 if char_len == 0 else 2,
            "impact": "critical" if char_len == 0 else "high",
            "component": "title",
            "message": "Write a descriptive, engaging title between 30 and 70 characters.",
            "fix": "Create a clear 30-70 character title."
        })

    # 2. Capitalization / ALL CAPS check (5 points)
    caps_pts = 5
    alpha_chars = [c for c in clean_title if c.isalpha()]
    if len(alpha_chars) >= 10:
        upper_count = sum(1 for c in alpha_chars if c.isupper())
        ratio = upper_count / len(alpha_chars)
        if ratio > 0.70:
            caps_pts = 0
            checks.append({
                "id": "title_all_caps",
                "component": "title",
                "status": "warn",
                "message": f"Title is mostly uppercase ({int(ratio * 100)}% capital letters). Reduces readability."
            })
            suggestions.append({
                "priority": 2,
                "impact": "medium",
                "component": "title",
                "message": "Use Title Case or sentence case instead of ALL CAPS.",
                "fix": "Capitalize only the first letter of major words or the opening word."
            })
        else:
            checks.append({
                "id": "title_all_caps",
                "component": "title",
                "status": "pass",
                "message": "Appropriate capitalization balance."
            })
    else:
        checks.append({
            "id": "title_all_caps",
            "component": "title",
            "status": "pass",
            "message": "Appropriate capitalization balance."
        })

    # 3. Repeated non-stopword tokens (5 points)
    repetition_pts = 5
    token_counts = Counter(content_tokens)
    repeated_words = [w for w, c in token_counts.items() if c > 1]
    if repeated_words:
        max_repeats = max(token_counts.values())
        if max_repeats >= 3 or len(repeated_words) >= 2:
            repetition_pts = 0
            status_rep = "fail"
        else:
            repetition_pts = 2
            status_rep = "warn"
        rep_list = ", ".join(sorted(repeated_words))
        checks.append({
            "id": "title_repetition",
            "component": "title",
            "status": status_rep,
            "message": f"Repeated content words in title: '{rep_list}'."
        })
        suggestions.append({
            "priority": 2,
            "impact": "medium",
            "component": "title",
            "message": f"Remove duplicate word '{repeated_words[0]}' from the title to save space.",
            "fix": "Replace duplicate words with complementary synonyms or audience terms."
        })
    else:
        checks.append({
            "id": "title_repetition",
            "component": "title",
            "status": "pass",
            "message": "No redundant word repetition in title."
        })

    # 4. Excessive punctuation / emoji clusters (3 points)
    punct_pts = 3
    excess_punct = bool(re.search(r"[!?\.]{3,}", clean_title))
    excess_symbols = bool(re.search(r"[\$#%&*]{3,}", clean_title))
    if excess_punct or excess_symbols:
        punct_pts = 0
        checks.append({
            "id": "title_punctuation",
            "component": "title",
            "status": "warn",
            "message": "Title contains excessive punctuation or symbol clusters (e.g. '!!!', '???')."
        })
        suggestions.append({
            "priority": 3,
            "impact": "low",
            "component": "title",
            "message": "Limit punctuation to a single question mark, colon, or pipe.",
            "fix": "Clean up trailing exclamation marks or question mark clusters."
        })
    else:
        checks.append({
            "id": "title_punctuation",
            "component": "title",
            "status": "pass",
            "message": "Clean punctuation without spammy character clusters."
        })

    # 5. Descriptive content depth (2 points)
    content_pts = 2
    if len(content_tokens) < 2 and char_len > 0:
        content_pts = 0
        checks.append({
            "id": "title_content_depth",
            "component": "title",
            "status": "warn",
            "message": "Title contains very few descriptive topic words."
        })
    else:
        checks.append({
            "id": "title_content_depth",
            "component": "title",
            "status": "pass" if char_len > 0 else "fail",
            "message": "Title conveys clear topic keywords." if char_len > 0 else "Missing title keywords."
        })

    total_pts = round(float(length_pts + caps_pts + repetition_pts + punct_pts + content_pts), 1)
    status = "pass" if total_pts >= 20 else ("warn" if total_pts >= 12 else "fail")

    return {
        "id": "title",
        "label": "Title Optimization",
        "points": total_pts,
        "max": 25,
        "status": status,
        "evidence": f"{char_len}/100 chars, {len(content_tokens)} content words, {caps_pts}/5 caps balance",
        "checks": checks,
        "suggestions": suggestions,
    }


def evaluate_focus_keyword(
    focus_keyword: str | None,
    title: str,
    description: str,
    tags: list[str]
) -> dict[str, Any]:
    """
    Evaluate Focus Keyword Relevance (Max 25 points).
    Rationale:
    - Title presence (early position bonus): Having the focus keyword early in the title
      aligns with search intent when viewers scan results.
    - Description first 150 chars: The opening 150 chars appear in search snippets.
    - Tags: Ensures metadata consistency across YouTube indexing fields.
    If no focus keyword is supplied, marks component as "unavailable" and returns None points.
    """
    raw_fk = (focus_keyword or "").strip()
    if not raw_fk:
        return {
            "id": "focus_keyword",
            "label": "Focus Keyword Alignment",
            "points": None,
            "max": 25,
            "status": "unavailable",
            "evidence": "No focus keyword supplied; component excluded from base score calculation.",
            "checks": [{
                "id": "focus_keyword_availability",
                "component": "focus_keyword",
                "status": "unavailable",
                "message": "No focus keyword provided. Add a target topic to evaluate keyword alignment."
            }],
            "suggestions": [{
                "priority": 2,
                "impact": "high",
                "component": "focus_keyword",
                "message": "Specify a focus keyword (e.g. 'free fire sensitivity' or 'python tutorial') to test search alignment.",
                "fix": "Enter your primary target keyword in the focus keyword field."
            }],
        }

    norm_fk = normalize_text(raw_fk)
    fk_tokens = tokenize(raw_fk)
    fk_content = get_content_tokens(fk_tokens)

    norm_title = normalize_text(title)
    norm_desc = normalize_text(description)
    desc_first150 = norm_desc[:150]
    norm_tags = [normalize_text(t) for t in tags if t]

    checks: list[dict[str, Any]] = []
    suggestions: list[dict[str, Any]] = []

    # If focus keyword consists solely of stopwords
    if not fk_content:
        return {
            "id": "focus_keyword",
            "label": "Focus Keyword Alignment",
            "points": 0.0,
            "max": 25,
            "status": "warn",
            "evidence": f"Focus keyword '{raw_fk}' contains only generic stopwords.",
            "checks": [{
                "id": "focus_keyword_validity",
                "component": "focus_keyword",
                "status": "warn",
                "message": f"Focus keyword '{raw_fk}' consists only of stopwords. Use a descriptive subject."
            }],
            "suggestions": [{
                "priority": 1,
                "impact": "high",
                "component": "focus_keyword",
                "message": "Replace generic stopword with an actionable target search phrase.",
                "fix": "Target a topic phrase containing 2-4 descriptive nouns or verbs."
            }],
        }

    # 1. Title presence & position (10 points)
    title_pts = 0
    # Exact phrase check
    if norm_fk in norm_title:
        idx = norm_title.find(norm_fk)
        if idx <= 35:
            title_pts = 10
            checks.append({
                "id": "fk_in_title",
                "component": "focus_keyword",
                "status": "pass",
                "message": f"Focus keyword appears in early position of title (char {idx})."
            })
        else:
            title_pts = 7
            checks.append({
                "id": "fk_in_title",
                "component": "focus_keyword",
                "status": "pass",
                "message": "Focus keyword appears in title, but later in the phrase."
            })
            suggestions.append({
                "priority": 3,
                "impact": "medium",
                "component": "focus_keyword",
                "message": "Move your focus keyword closer to the beginning of the title for faster scanning.",
                "fix": "Place target keyword in the first 35 characters of the title."
            })
    else:
        # Check token coverage
        title_tokens = set(tokenize(title))
        matched_tokens = [t for t in fk_content if t in title_tokens]
        coverage = len(matched_tokens) / len(fk_content)
        if coverage == 1.0:
            title_pts = 6
            checks.append({
                "id": "fk_in_title",
                "component": "focus_keyword",
                "status": "warn",
                "message": "All focus keyword words appear in the title, but not as an exact phrase."
            })
            suggestions.append({
                "priority": 2,
                "impact": "medium",
                "component": "focus_keyword",
                "message": f"Group words into the exact phrase '{raw_fk}' within your title.",
                "fix": f"Include the unbroken phrase '{raw_fk}' in your title."
            })
        elif coverage >= 0.5:
            title_pts = 3
            checks.append({
                "id": "fk_in_title",
                "component": "focus_keyword",
                "status": "warn",
                "message": "Only partial focus keyword tokens appear in the title."
            })
            suggestions.append({
                "priority": 2,
                "impact": "high",
                "component": "focus_keyword",
                "message": f"Include the full focus keyword '{raw_fk}' in the title.",
                "fix": f"Add '{raw_fk}' to the title."
            })
        else:
            title_pts = 0
            checks.append({
                "id": "fk_in_title",
                "component": "focus_keyword",
                "status": "fail",
                "message": f"Focus keyword '{raw_fk}' is missing from the title."
            })
            suggestions.append({
                "priority": 1,
                "impact": "critical",
                "component": "focus_keyword",
                "message": f"Add your focus keyword '{raw_fk}' directly to the video title.",
                "fix": f"Incorporate '{raw_fk}' in the title."
            })

    # 2. Description first 150 chars (8 points)
    desc_pts = 0
    if norm_fk in desc_first150:
        desc_pts = 8
        checks.append({
            "id": "fk_in_desc_snippet",
            "component": "focus_keyword",
            "status": "pass",
            "message": "Focus keyword appears in the first 150 characters of description."
        })
    elif norm_fk in norm_desc:
        desc_pts = 4
        checks.append({
            "id": "fk_in_desc_snippet",
            "component": "focus_keyword",
            "status": "warn",
            "message": "Focus keyword is in description, but buried after the 150-character fold."
        })
        suggestions.append({
            "priority": 2,
            "impact": "high",
            "component": "focus_keyword",
            "message": f"Move '{raw_fk}' into the first two sentences of your description.",
            "fix": "Rephrase opening sentence to introduce the focus keyword immediately."
        })
    else:
        desc_tokens = set(tokenize(desc_first150))
        matched_tokens = [t for t in fk_content if t in desc_tokens]
        if len(matched_tokens) == len(fk_content):
            desc_pts = 5
            checks.append({
                "id": "fk_in_desc_snippet",
                "component": "focus_keyword",
                "status": "warn",
                "message": "Focus keyword tokens appear in description snippet, but separated."
            })
        elif norm_desc:
            desc_pts = 0
            checks.append({
                "id": "fk_in_desc_snippet",
                "component": "focus_keyword",
                "status": "fail",
                "message": f"Focus keyword '{raw_fk}' is completely missing from description."
            })
            suggestions.append({
                "priority": 1,
                "impact": "high",
                "component": "focus_keyword",
                "message": f"Naturally mention '{raw_fk}' in the first two sentences of the description.",
                "fix": f"Include '{raw_fk}' in the opening description summary."
            })
        else:
            desc_pts = 0
            checks.append({
                "id": "fk_in_desc_snippet",
                "component": "focus_keyword",
                "status": "fail",
                "message": "Description is empty; focus keyword cannot be indexed."
            })

    # 3. Present in tags (7 points)
    tag_pts = 0
    if not norm_tags:
        # If user didn't enter tags, don't brutally fail if YouTube says tags are minimal,
        # but warn about tag synergy.
        tag_pts = 3
        checks.append({
            "id": "fk_in_tags",
            "component": "focus_keyword",
            "status": "warn",
            "message": "No tags provided to reinforce focus keyword synergy."
        })
        suggestions.append({
            "priority": 3,
            "impact": "low",
            "component": "focus_keyword",
            "message": f"Add '{raw_fk}' as one of your YouTube tags.",
            "fix": f"Add tag: '{raw_fk}'."
        })
    elif any(norm_fk == t for t in norm_tags):
        tag_pts = 7
        checks.append({
            "id": "fk_in_tags",
            "component": "focus_keyword",
            "status": "pass",
            "message": f"Exact focus keyword '{raw_fk}' is included in tags."
        })
    elif any(norm_fk in t or all(tok in t for tok in fk_content) for t in norm_tags):
        tag_pts = 5
        checks.append({
            "id": "fk_in_tags",
            "component": "focus_keyword",
            "status": "pass",
            "message": "Focus keyword phrase is embedded within video tags."
        })
    else:
        tag_pts = 0
        checks.append({
            "id": "fk_in_tags",
            "component": "focus_keyword",
            "status": "warn",
            "message": f"Focus keyword '{raw_fk}' is not present in tags."
        })
        suggestions.append({
            "priority": 3,
            "impact": "low",
            "component": "focus_keyword",
            "message": f"Add '{raw_fk}' to your tags list for consistency.",
            "fix": f"Add '{raw_fk}' as a tag."
        })

    total_pts = round(float(title_pts + desc_pts + tag_pts), 1)
    status = "pass" if total_pts >= 20 else ("warn" if total_pts >= 12 else "fail")

    return {
        "id": "focus_keyword",
        "label": "Focus Keyword Alignment",
        "points": total_pts,
        "max": 25,
        "status": status,
        "evidence": f"Title: {title_pts}/10, Description: {desc_pts}/8, Tags: {tag_pts}/7",
        "checks": checks,
        "suggestions": suggestions,
    }


def evaluate_description(description: str) -> dict[str, Any]:
    """
    Evaluate Description Quality (Max 20 points).
    Rationale:
    - Length bands: YouTube permits up to 5,000 characters. Comprehensive descriptions
      (250+ chars) help YouTube understand content context, index chapters, and inform viewers.
    - Informative opening: The first 150 characters should introduce the video topic naturally,
      rather than opening immediately with raw links, promo codes, or hashtags.
    - Hashtags: YouTube recommends 3-5 relevant hashtags. Official YouTube policy states exceeding 60 hashtags causes YouTube to ignore all hashtags.
    - Keyword dump: Repeating unnatural lists of comma-separated keywords violates YouTube
      anti-spam policies.
    """
    clean_desc = (description or "").strip()
    char_len = len(clean_desc)
    byte_len = len(clean_desc.encode("utf-8"))
    checks: list[dict[str, Any]] = []
    suggestions: list[dict[str, Any]] = []

    # 1. Platform Limit & Length bands (8 points)
    # YouTube Data API v3 specifies: snippet.description maximum 5000 bytes.
    length_pts = 0
    if byte_len > 5000:
        length_pts = 0
        checks.append({
            "id": "desc_length",
            "component": "description",
            "status": "fail",
            "message": f"YouTube Platform Limit: Description exceeds YouTube Data API maximum of 5,000 bytes ({byte_len} bytes in UTF-8). Upload will be rejected by YouTube."
        })
        suggestions.append({
            "priority": 1,
            "impact": "critical",
            "component": "description",
            "message": f"Trim description by {byte_len - 5000} bytes to stay within YouTube's 5,000-byte platform limit.",
            "fix": "Shorten description below 5,000 UTF-8 bytes."
        })
    elif char_len >= 250:
        length_pts = 8
        checks.append({
            "id": "desc_length",
            "component": "description",
            "status": "pass",
            "message": f"Plexudo Tip: Comprehensive description length ({char_len} characters, {byte_len}/5000 bytes)."
        })
    elif 100 <= char_len < 250:
        length_pts = 5
        checks.append({
            "id": "desc_length",
            "component": "description",
            "status": "pass",
            "message": f"Plexudo Tip: Adequate description length ({char_len} chars, {byte_len}/5000 bytes). Expanding to 250+ chars adds SEO depth."
        })
        suggestions.append({
            "priority": 3,
            "impact": "medium",
            "component": "description",
            "message": "Add an outline, timestamps, or key takeaways to reach 250+ characters.",
            "fix": "Expand description with a 2-3 paragraph breakdown of the video."
        })
    elif 1 <= char_len < 100:
        length_pts = 2
        checks.append({
            "id": "desc_length",
            "component": "description",
            "status": "warn",
            "message": f"Plexudo Tip: Description is very brief ({char_len} chars, {byte_len}/5000 bytes). Under 100 chars provides little context."
        })
        suggestions.append({
            "priority": 2,
            "impact": "high",
            "component": "description",
            "message": "Write a 150-300 word description summarizing the video and answering viewer questions.",
            "fix": "Write at least 2 full sentences explaining what happens in the video."
        })
    else:  # char_len == 0
        length_pts = 0
        checks.append({
            "id": "desc_length",
            "component": "description",
            "status": "fail",
            "message": "Description is completely empty."
        })
        suggestions.append({
            "priority": 1,
            "impact": "critical",
            "component": "description",
            "message": "Provide a descriptive summary. Empty descriptions handicap discovery.",
            "fix": "Add a complete video description."
        })

    # 2. Informative first lines (6 points)
    opening_pts = 6
    if char_len > 0:
        first_150 = clean_desc[:150].strip()
        has_leading_link = bool(re.match(r"^(https?://|www\.)", first_150, re.IGNORECASE))
        has_leading_hashtag = bool(re.match(r"^#", first_150))
        lines = [line.strip() for line in clean_desc.splitlines() if line.strip()]
        first_line = lines[0] if lines else ""

        if has_leading_link or first_line.startswith(("http://", "https://", "www.")):
            opening_pts = 2
            checks.append({
                "id": "desc_informative_opening",
                "component": "description",
                "status": "warn",
                "message": "Description opens with a link. Search snippets will show a URL instead of content."
            })
            suggestions.append({
                "priority": 2,
                "impact": "high",
                "component": "description",
                "message": "Place social and affiliate links after 2-3 sentences of natural video summary.",
                "fix": "Move links below the opening summary paragraphs."
            })
        elif has_leading_hashtag or first_line.startswith("#"):
            opening_pts = 3
            checks.append({
                "id": "desc_informative_opening",
                "component": "description",
                "status": "warn",
                "message": "Description opens with hashtags. Lead with natural sentences describing the video."
            })
            suggestions.append({
                "priority": 3,
                "impact": "medium",
                "component": "description",
                "message": "Move hashtags to the bottom of the description.",
                "fix": "Begin with a natural sentence introducing the video."
            })
        else:
            checks.append({
                "id": "desc_informative_opening",
                "component": "description",
                "status": "pass",
                "message": "Informative opening snippet before links or social disclaimers."
            })
    else:
        opening_pts = 0
        checks.append({
            "id": "desc_informative_opening",
            "component": "description",
            "status": "fail",
            "message": "Missing opening description."
        })

    # 3. Hashtag usage (3 points)
    # YouTube Official Policy: "If a video has more than 60 hashtags, we'll ignore each hashtag on that video."
    # Plexudo Creator Advice: 3-5 relevant hashtags is the recommended sweet spot.
    hashtag_pts = 3
    hashtags = re.findall(r"(?u)#[\w]+", clean_desc)
    ht_count = len(hashtags)
    if ht_count > 60:
        hashtag_pts = 0
        checks.append({
            "id": "desc_hashtags",
            "component": "description",
            "status": "fail",
            "message": f"YouTube Policy Violation: Over 60 hashtags detected ({ht_count}). Official YouTube policy states videos with more than 60 hashtags will have each hashtag ignored, and may be flagged for over-tagging."
        })
        suggestions.append({
            "priority": 1,
            "impact": "critical",
            "component": "description",
            "message": f"Reduce hashtags immediately. YouTube ignores all hashtags when exceeding 60 hashtags ({ht_count} found).",
            "fix": "Delete excessive hashtags so total count is at most 3-5 (strictly <= 60)."
        })
    elif 6 <= ht_count <= 60:
        hashtag_pts = 1
        checks.append({
            "id": "desc_hashtags",
            "component": "description",
            "status": "warn",
            "message": f"Plexudo Tip: Contains {ht_count} hashtags. Within YouTube's 60-hashtag limit, but Plexudo recommends 3-5 focused hashtags for cleaner presentation."
        })
        suggestions.append({
            "priority": 3,
            "impact": "low",
            "component": "description",
            "message": "Plexudo tip: Trim hashtags to 3-5 focused tags to avoid visual clutter.",
            "fix": "Keep 3-5 top hashtags."
        })
    elif 1 <= ht_count <= 5:
        hashtag_pts = 3
        checks.append({
            "id": "desc_hashtags",
            "component": "description",
            "status": "pass",
            "message": f"Optimal hashtag count ({ht_count} hashtags; aligns with Plexudo recommendation of 3-5)."
        })
    else:  # ht_count == 0
        hashtag_pts = 2
        checks.append({
            "id": "desc_hashtags",
            "component": "description",
            "status": "pass",
            "message": "No hashtags used (neutral; hashtags are optional on YouTube)."
        })

    # 4. Keyword dump check (3 points)
    dump_pts = 3
    # Detect comma-separated keyword list blocks (e.g., "tag1, tag2, tag3, tag4, tag5")
    comma_dumps = False
    for line in clean_desc.splitlines():
        trimmed = line.strip()
        if trimmed.count(",") >= 5 and len(trimmed) > 50:
            tokens_in_line = tokenize(trimmed)
            if len(tokens_in_line) > 6:
                comma_dumps = True
                break

    if comma_dumps:
        dump_pts = 0
        checks.append({
            "id": "desc_keyword_dump",
            "component": "description",
            "status": "fail",
            "message": "Comma-separated tag list detected in description. Violates YouTube spam policies."
        })
        suggestions.append({
            "priority": 1,
            "impact": "critical",
            "component": "description",
            "message": "Remove blocks of comma-separated keywords from the description to prevent spam strikes.",
            "fix": "Delete raw tag lists and integrate keywords naturally into complete sentences."
        })
    else:
        checks.append({
            "id": "desc_keyword_dump",
            "component": "description",
            "status": "pass",
            "message": "No spammy keyword dump blocks detected."
        })

    total_pts = round(float(length_pts + opening_pts + hashtag_pts + dump_pts), 1)
    status = "pass" if total_pts >= 16 else ("warn" if total_pts >= 10 else "fail")

    return {
        "id": "description",
        "label": "Description Quality",
        "points": total_pts,
        "max": 20,
        "status": status,
        "evidence": f"{char_len} chars ({byte_len}/5000 bytes), {ht_count} hashtags, opening snippet quality {opening_pts}/6",
        "checks": checks,
        "suggestions": suggestions,
    }


def evaluate_natural_consistency(
    title: str,
    description: str,
    tags: list[str]
) -> dict[str, Any]:
    """
    Evaluate Natural Keyword Consistency & Stuffing Detection (Max 20 points).
    Rationale:
    - Cross-field overlap (10 pts): Title keywords naturally appearing in the description
      and tags reinforce semantic topic clarity without spamming.
    - Anti-stuffing (10 pts): Artificially repeating the same non-stopword token excessively
      (>4% of description words or repeated 6+ times in short text) harms readability and
      triggers YouTube spam filters.
    """
    title_tokens = tokenize(title)
    title_content = get_content_tokens(title_tokens)

    desc_tokens = tokenize(description)
    desc_content = get_content_tokens(desc_tokens)

    tag_tokens: list[str] = []
    for t in tags:
        tag_tokens.extend(tokenize(t))
    tag_content = get_content_tokens(tag_tokens)

    checks: list[dict[str, Any]] = []
    suggestions: list[dict[str, Any]] = []

    # 1. Title/Description/Tags overlap (10 points)
    overlap_pts = 0
    if not title_content:
        overlap_pts = 0
        checks.append({
            "id": "keyword_overlap",
            "component": "natural_consistency",
            "status": "warn",
            "message": "No title content words available to measure cross-metadata overlap."
        })
    else:
        desc_token_set = set(desc_content)
        tag_token_set = set(tag_content)

        # Count how many title content words appear in description
        in_desc_count = sum(1 for w in title_content if w in desc_token_set)
        desc_ratio = in_desc_count / len(title_content)

        # Count how many title content words appear in tags
        in_tags_count = sum(1 for w in title_content if w in tag_token_set)
        tags_ratio = in_tags_count / len(title_content) if tag_content else 0.5  # neutral if tags omitted

        combined_ratio = (desc_ratio * 0.7) + (tags_ratio * 0.3)

        if combined_ratio >= 0.50:
            overlap_pts = 10
            checks.append({
                "id": "keyword_overlap",
                "component": "natural_consistency",
                "status": "pass",
                "message": f"Strong semantic consistency between title, description, and tags ({int(desc_ratio*100)}% title words present in description)."
            })
        elif combined_ratio >= 0.25:
            overlap_pts = 6
            checks.append({
                "id": "keyword_overlap",
                "component": "natural_consistency",
                "status": "pass",
                "message": f"Moderate semantic consistency ({int(desc_ratio*100)}% title keywords in description)."
            })
            suggestions.append({
                "priority": 3,
                "impact": "medium",
                "component": "natural_consistency",
                "message": "Naturally incorporate key phrases from your title into the description body.",
                "fix": "Mention title keywords in the body of your description."
            })
        elif in_desc_count >= 1:
            overlap_pts = 3
            checks.append({
                "id": "keyword_overlap",
                "component": "natural_consistency",
                "status": "warn",
                "message": "Weak overlap between title and description."
            })
            suggestions.append({
                "priority": 2,
                "impact": "high",
                "component": "natural_consistency",
                "message": "Reinforce title topic keywords in the opening paragraph of the description.",
                "fix": "Add the main title concepts into your description summary."
            })
        else:
            overlap_pts = 0
            checks.append({
                "id": "keyword_overlap",
                "component": "natural_consistency",
                "status": "fail",
                "message": "None of the title keywords appear in the description."
            })
            suggestions.append({
                "priority": 1,
                "impact": "high",
                "component": "natural_consistency",
                "message": "Align description with your title. Currently no title keywords appear in description.",
                "fix": "Explain the title's topic directly in the description."
            })

    # 2. Keyword stuffing detection (10 points)
    stuffing_pts = 10
    stuffed_tokens: list[str] = []

    if desc_content:
        counts = Counter(desc_content)
        total_content = len(desc_content)

        for word, count in counts.items():
            # Stuffing rules:
            # - In short description (<50 content tokens): repeated > 5 times
            # - In longer description: single word exceeds 4% of total content tokens AND repeated >= 6 times
            if total_content < 50 and count >= 5:
                stuffed_tokens.append(f"{word} ({count}x)")
            elif total_content >= 50 and (count / total_content) > 0.04 and count >= 6:
                stuffed_tokens.append(f"{word} ({int((count/total_content)*100)}%)")

    if stuffed_tokens:
        if len(stuffed_tokens) >= 2 or any("x" in s and int(s.split("(")[1].replace("x)", "")) >= 8 for s in stuffed_tokens):
            stuffing_pts = 0
            status_stf = "fail"
        else:
            stuffing_pts = 4
            status_stf = "warn"

        stf_summary = ", ".join(sorted(stuffed_tokens))
        checks.append({
            "id": "keyword_stuffing",
            "component": "natural_consistency",
            "status": status_stf,
            "message": f"Keyword repetition detected in description: {stf_summary}."
        })
        suggestions.append({
            "priority": 1 if stuffing_pts == 0 else 2,
            "impact": "high",
            "component": "natural_consistency",
            "message": f"Reduce repetitive usage of '{stuffed_tokens[0]}'. Write naturally for viewers.",
            "fix": "Use pronouns, synonyms, or rephrase sentences to avoid keyword repetition."
        })
    else:
        checks.append({
            "id": "keyword_stuffing",
            "component": "natural_consistency",
            "status": "pass",
            "message": "Natural keyword density without stuffing or repetitive spam patterns."
        })

    total_pts = round(float(overlap_pts + stuffing_pts), 1)
    status = "pass" if total_pts >= 16 else ("warn" if total_pts >= 10 else "fail")

    return {
        "id": "natural_consistency",
        "label": "Natural Keyword Consistency",
        "points": total_pts,
        "max": 20,
        "status": status,
        "evidence": f"Overlap: {overlap_pts}/10, Stuffing check: {stuffing_pts}/10",
        "checks": checks,
        "suggestions": suggestions,
    }


def evaluate_tags(
    tags: list[str],
    title: str,
    description: str,
    focus_keyword: str | None = None
) -> dict[str, Any]:
    """
    Evaluate Tags Quality (Low weight: Max 10 points).
    Rationale:
    - Official YouTube guidance states: "Tags play a minimal role in video discovery...
      they can be useful if your video content is commonly misspelled. Otherwise, tags
      play a minimal role."
    - Missing tags is completely neutral and never a failure.
    - NO points are awarded for tag count (15+) or character inflation (400+).
    - Checks focus on YouTube 500-character total limit compliance, duplicate removal,
      and basic relevance.
    """
    checks: list[dict[str, Any]] = []
    suggestions: list[dict[str, Any]] = []

    clean_tags = [t.strip() for t in tags if isinstance(t, str) and t.strip()]

    # Missing tags is neutral, never a failure
    if not clean_tags:
        checks.append({
            "id": "tag_status",
            "component": "tags",
            "status": "pass",
            "message": "No tags provided. YouTube confirms tags play a minimal role in discovery; no penalty applied."
        })
        return {
            "id": "tags",
            "label": "Tags Optimization",
            "points": 10.0,
            "max": 10,
            "status": "pass",
            "evidence": "0 tags provided (neutral per YouTube guidance; 10/10 awarded)",
            "checks": checks,
            "suggestions": [],
        }

    # 1. Total character count under YouTube's 500-char limit (4 points)
    # YouTube Studio and API calculate tag capacity by enclosing multi-word tags in quotes and joining with commas.
    total_tag_chars = calculate_youtube_tag_chars(clean_tags)
    limit_pts = 4
    if total_tag_chars > 500:
        limit_pts = 0
        checks.append({
            "id": "tag_char_limit",
            "component": "tags",
            "status": "fail",
            "message": f"YouTube Platform Limit: Tag formatted characters ({total_tag_chars}/500 chars) exceed YouTube's 500-character limit. Note multi-word tags include quotation marks and commas per YouTube requirements."
        })
        suggestions.append({
            "priority": 1,
            "impact": "critical",
            "component": "tags",
            "message": f"Remove {total_tag_chars - 500} characters of tags to comply with YouTube limits.",
            "fix": "Delete low-value or overly long tags until total character count is under 500."
        })
    else:
        checks.append({
            "id": "tag_char_limit",
            "component": "tags",
            "status": "pass",
            "message": f"YouTube Platform Limit: Tag volume within YouTube's 500-character limit ({total_tag_chars}/500 chars)."
        })

    # 2. Duplicate tags check (3 points)
    dup_pts = 3
    normalized_tags = [normalize_text(t) for t in clean_tags]
    counts = Counter(normalized_tags)
    duplicates = [t for t, c in counts.items() if c > 1]

    if duplicates:
        dup_pts = 0 if len(duplicates) >= 3 else 1
        dup_list = ", ".join(sorted(duplicates))
        checks.append({
            "id": "tag_duplicates",
            "component": "tags",
            "status": "warn",
            "message": f"Duplicate tags found after normalization: {dup_list}."
        })
        suggestions.append({
            "priority": 3,
            "impact": "low",
            "component": "tags",
            "message": f"Remove duplicate tags ({duplicates[0]}). They waste character space.",
            "fix": "Remove identical or case-insensitive duplicate tags."
        })
    else:
        checks.append({
            "id": "tag_duplicates",
            "component": "tags",
            "status": "pass",
            "message": "All tags are unique."
        })

    # 3. Basic topic relevance (3 points)
    rel_pts = 3
    ref_tokens = set(get_content_tokens(tokenize(title)))
    ref_tokens |= set(get_content_tokens(tokenize(description[:300])))
    if focus_keyword:
        ref_tokens |= set(get_content_tokens(tokenize(focus_keyword)))

    if ref_tokens:
        relevant_tags = 0
        for tag in clean_tags:
            tag_toks = set(tokenize(tag))
            if tag_toks & ref_tokens:
                relevant_tags += 1

        rel_ratio = relevant_tags / len(clean_tags)
        if rel_ratio >= 0.30:
            rel_pts = 3
            checks.append({
                "id": "tag_relevance",
                "component": "tags",
                "status": "pass",
                "message": f"Tags align well with video topic ({relevant_tags}/{len(clean_tags)} relevant tags)."
            })
        else:
            rel_pts = 1
            checks.append({
                "id": "tag_relevance",
                "component": "tags",
                "status": "warn",
                "message": f"Few tags share keywords with title/description ({relevant_tags}/{len(clean_tags)})."
            })
            suggestions.append({
                "priority": 3,
                "impact": "low",
                "component": "tags",
                "message": "Include common misspellings or direct variations of your title topic in tags.",
                "fix": "Align tags with the core title keywords."
            })
    else:
        checks.append({
            "id": "tag_relevance",
            "component": "tags",
            "status": "pass",
            "message": "Tags evaluated."
        })

    total_pts = round(float(limit_pts + dup_pts + rel_pts), 1)
    status = "pass" if total_pts >= 8 else ("warn" if total_pts >= 5 else "fail")

    return {
        "id": "tags",
        "label": "Tags Optimization",
        "points": total_pts,
        "max": 10,
        "status": status,
        "evidence": f"{len(clean_tags)} tags, {total_tag_chars}/500 characters used",
        "checks": checks,
        "suggestions": suggestions,
    }


# -----------------------------------------------------------------------------
# Main Public Interface
# -----------------------------------------------------------------------------

def analyze_seo_metadata(
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    focus_keyword: str | None = None,
    language: str = "auto",
) -> dict[str, Any]:
    """
    Pure, deterministic SEO Intelligence evaluation function.
    Returns structured scoring, component breakdowns, checks, suggestions,
    and unavailable telemetry states.
    """
    tag_list = tags if (tags is not None and isinstance(tags, list)) else []

    title_eval = evaluate_title(title)
    fk_eval = evaluate_focus_keyword(focus_keyword, title, description, tag_list)
    desc_eval = evaluate_description(description)
    nat_eval = evaluate_natural_consistency(title, description, tag_list)
    tag_eval = evaluate_tags(tag_list, title, description, focus_keyword)

    components = [title_eval, fk_eval, desc_eval, nat_eval, tag_eval]

    # Collect all checks and suggestions
    all_checks: list[dict[str, Any]] = []
    all_suggestions: list[dict[str, Any]] = []
    breakdown: list[dict[str, Any]] = []

    applied_components: list[str] = []
    unavailable_components: list[str] = []
    earned_pts = 0.0
    available_max = 0

    for comp in components:
        breakdown.append({
            "id": comp["id"],
            "label": comp["label"],
            "points": comp["points"],
            "max": comp["max"],
            "status": comp["status"],
            "evidence": comp["evidence"],
        })
        all_checks.extend(comp.get("checks", []))
        all_suggestions.extend(comp.get("suggestions", []))

        if comp["points"] is not None:
            earned_pts += float(comp["points"])
            available_max += comp["max"]
            applied_components.append(comp["id"])
        else:
            unavailable_components.append(comp["id"])

    # Score calculation over available components, scaled to 0-100
    if available_max > 0:
        scaled_score = round((earned_pts / float(available_max)) * 100.0, 1)
        final_score = max(0.0, min(100.0, scaled_score))
    else:
        final_score = 0.0

    score_basis = {
        "available_max": available_max,
        "raw_earned": round(earned_pts, 1),
        "applied_components": applied_components,
        "unavailable_components": unavailable_components,
        "normalized_to_100": available_max != 100,
    }

    # Sort suggestions deterministically by priority (1=critical, 2=high, 3=medium/low)
    # then by component id
    sorted_suggestions = sorted(
        all_suggestions,
        key=lambda s: (s.get("priority", 99), s.get("component", ""), s.get("message", ""))
    )

    # Sort checks deterministically by component then id
    sorted_checks = sorted(
        all_checks,
        key=lambda c: (c.get("component", ""), c.get("id", ""))
    )

    unavailable_telemetry = {
        "observed_performance": {
            "status": "unavailable",
            "reason": "Requires authenticated YouTube Analytics API access; Plexudo operates in 100% anonymous, privacy-first mode."
        },
        "ranking_evidence": {
            "status": "unavailable",
            "reason": "Plexudo does not track search result position scraping or guarantee ranking outcomes."
        },
        "vph": {
            "status": "unavailable",
            "reason": "Real-time views-per-hour requires multi-snapshot historical polling not collected during static metadata analysis."
        }
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "engine_version": ENGINE_VERSION,
        "score": final_score,
        "score_basis": score_basis,
        "breakdown": breakdown,
        "checks": sorted_checks,
        "suggestions": sorted_suggestions,
        "unavailable": unavailable_telemetry,
        "disclaimer": DISCLAIMER_TEXT,
    }
