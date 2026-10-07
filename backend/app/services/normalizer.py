"""
RemitMind Semantic Shield & Text Normalization Engine
Guards against unicode evasion, zero-width steganography, homoglyphs, and leet-speak.
Used by ScamShield pre-flight interception to neutralize evasion attacks.
"""

import re
import unicodedata

# 1. Zero-width and invisible control codepoints
ZERO_WIDTH_REGEX = re.compile(
    r"[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E\u2060-\u2064\u00AD\u034F\u180E]"
)

# 2. Cyrillic and Greek homoglyphs mapped to Latin counterparts
HOMOGLYPH_MAP = {
    # Cyrillic lowercase
    "а": "a", "в": "b", "с": "c", "е": "e", "о": "o", "р": "p", "ѕ": "s",
    "х": "x", "у": "y", "і": "i", "ј": "j", "к": "k", "м": "m", "т": "t",
    "н": "h", "г": "r", "д": "d",
    # Cyrillic uppercase
    "А": "a", "В": "b", "С": "c", "Е": "e", "Н": "h", "І": "i", "К": "k",
    "М": "m", "О": "o", "Р": "p", "Т": "t", "Х": "x", "Ү": "y", "Г": "r",
    # Greek
    "α": "a", "β": "b", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o",
    "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
    "Α": "a", "Β": "b", "Ε": "e", "Ι": "i", "Κ": "k", "Ν": "n", "Ο": "o",
    "Ρ": "p", "Τ": "t",
    # Common leet / symbol substitutions
    "@": "a", "$": "s", "0": "o", "!": "i", "|": "l", "3": "e",
    "4": "a", "5": "s", "7": "t", "8": "b", "1": "l"
}

# 3. Bangla digits to standard numerals
BANGLA_DIGIT_MAP = {
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9"
}

def strip_zero_width(text: str) -> str:
    """Removes all invisible zero-width and bidirectional formatting characters."""
    if not text:
        return ""
    return ZERO_WIDTH_REGEX.sub("", text)

def fold_homoglyphs(text: str) -> str:
    """Replaces common Cyrillic, Greek, and symbol homoglyphs with standard characters."""
    chars = []
    for ch in text:
        if ch in HOMOGLYPH_MAP:
            chars.append(HOMOGLYPH_MAP[ch])
        elif ch in BANGLA_DIGIT_MAP:
            chars.append(BANGLA_DIGIT_MAP[ch])
        else:
            chars.append(ch)
    return "".join(chars)

def normalize_text_for_scamshield(text: str) -> tuple[str, str]:
    """
    Transforms text through rigorous normalization:
    1. Zero-width character stripping
    2. NFKC unicode canonical normalization
    3. Lowercase folding
    4. Homoglyph and leet substitution
    5. Returns (standard_normalized, collapsed_delimiter_normalized)
       - standard_normalized: words separated by single spaces
       - collapsed_normalized: inter-character punctuation (dots, hyphens, asterisks) removed
    """
    if not text:
        return "", ""

    # Step 1: Strip zero-width & invisible marks
    cleaned = strip_zero_width(text)

    # Step 2: NFKC decomposition (transforms fullwidth Latin 'ｌｏｔｔｅｒｙ' -> 'lottery')
    nfkc = unicodedata.normalize("NFKC", cleaned)

    # Step 3: Lowercase
    lowered = nfkc.lower()

    # Step 4: Fold Cyrillic/Greek/Leet homoglyphs and Bangla digits
    folded = fold_homoglyphs(lowered)

    # Step 5: Clean whitespace
    standard_norm = re.sub(r"\s+", " ", folded).strip()

    # Step 6: Create delimiter-collapsed version (e.g. 'l.o.t.t.e.r.y' -> 'lottery', 'b_f_i_u' -> 'bfiu')
    # Collapse punctuation between letters but keep words separated
    collapsed_norm = re.sub(r"[\.\-\_\*\,\:\;\~\#\^\/\\\+]", "", standard_norm)
    collapsed_norm = re.sub(r"\s+", " ", collapsed_norm).strip()

    return standard_norm, collapsed_norm

def contains_scam_keyword(text: str, keywords: list[str]) -> bool:
    """
    Evaluates whether any keyword exists in the text after robust anti-evasion normalization.
    Tests both space-preserved and delimiter-collapsed representations.
    """
    if not text:
        return False

    standard_norm, collapsed_norm = normalize_text_for_scamshield(text)

    for kw in keywords:
        kw_norm, kw_collapsed = normalize_text_for_scamshield(kw)
        if kw_norm and kw_norm in standard_norm:
            return True
        if kw_collapsed and kw_collapsed in collapsed_norm:
            return True

    return False
