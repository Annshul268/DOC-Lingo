import re

# Common Hinglish stopwords / grammatical markers
HINGLISH_PATTERNS = [
    r"\bkya\b", r"\bkyu\b", r"\bkyun\b", r"\bkaise\b", r"\bkab\b", r"\bkaha\b", r"\bkahan\b",
    r"\bhai\b", r"\bhain\b", r"\btha\b", r"\bthe\b", r"\bthi\b", r"\bhoga\b", r"\bhogi\b",
    r"\bmein\b", r"\bme\b", r"\bko\b", r"\bse\b", r"\bka\b", r"\bki\b", r"\bke\b",
    r"\bkar\b", r"\bkare\b", r"\bkaro\b", r"\bkarta\b", r"\bkarte\b", r"\bkarti\b",
    r"\bhota\b", r"\bhote\b", r"\bhoti\b", r"\byeh\b", r"\bwoh\b", r"\bwo\b", r"\bya\b",
    r"\baur\b", r"\bpar\b", r"\bpe\b", r"\bbatao\b", r"\bsamjhao\b", r"\bkarein\b",
    r"\bek\b", r"\bdoosre\b", r"\bdusre\b", r"\baap\b", r"\btum\b", r"\bhum\b"
]

DEVANAGARI_RANGE = re.compile(r'[\u0900-\u097F]')

def detect_language(text: str) -> str:
    """
    Detects whether text is Hindi (Devanagari script), Hinglish (Roman script Hindi), or English.
    Returns: 'hi', 'hinglish', or 'en'
    """
    if not text or not text.strip():
        return "en"
    
    # Check for Devanagari characters
    devanagari_chars = len(DEVANAGARI_RANGE.findall(text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', text))
    
    if total_alpha > 0 and (devanagari_chars / total_alpha) > 0.2:
        return "hi"
    
    # Check for Hinglish words in Roman script
    text_lower = text.lower()
    hinglish_matches = sum(1 for pattern in HINGLISH_PATTERNS if re.search(pattern, text_lower))
    
    # If 2 or more Hinglish markers or a high proportion of words
    words = text_lower.split()
    if hinglish_matches >= 1:
        return "hinglish"
        
    return "en"
