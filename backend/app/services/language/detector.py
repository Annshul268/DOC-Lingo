import re

# High-confidence Hinglish markers that do NOT collide with common English words
DISTINCT_HINGLISH_WORDS = {
    # Question words
    "kya", "kyu", "kyun", "kaise", "kab", "kaha", "kahan", "kitna", "kitne", "kitni", "kaun", "kisko", "kisme",
    # Auxiliary verbs & copulas
    "hai", "hain", "tha", "thi", "thien", "hoga", "hogi", "hoge", "honge", "hona", "hote", "hoti", "hota",
    # Postpositions & case markers
    "mein", "ko", "se", "ka", "ki", "ke", "liye", "par", "pe", "tak", "saath", "baare",
    # Verbs / action words
    "kar", "kare", "karo", "karta", "karte", "karti", "karein", "karna", "kiya", "kiye", "kiyi",
    "batao", "bataiye", "samjhao", "samjhaye", "dekho", "dekhiye", "bolo", "boli", "boliye", "bola", "gaya", "gayi", "gaye",
    "milta", "milte", "milti", "mila", "mile", "aata", "aate", "aati", "raha", "rahe", "rahi", "sakta", "sakte", "sakti",
    # Pronouns & demonstratives
    "yeh", "woh", "wo", "iss", "uss", "inka", "unka", "isme", "usme",
    "aap", "aapka", "aapki", "aapke", "tum", "tumhara", "tumhari", "tumhare", "hamara", "mera", "meri", "mere",
    # Conjunctions & adverbs
    "aur", "ya", "lekin", "magar", "parantu", "kyunki", "isliye", "bhi", "toh",
    # Other common words
    "ek", "doosre", "dusre", "kuch", "sabse", "sabhi", "bahut", "jyada", "kam", "accha", "acha", "sahi"
}

# Context-dependent words that exist in both Hinglish and English (e.g. "is" = 'this' in Hindi, but copula in English; "the" = 'were' in Hindi, but article in English; "to", "me")
AMBIGUOUS_WORDS = {"is", "the", "to", "me", "do", "in", "so", "hi"}

# Common English function words
COMMON_ENGLISH_WORDS = {
    "the", "what", "which", "who", "whom", "this", "that", "these", "those", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "how", "why", "when", "where",
    "of", "in", "to", "for", "with", "on", "at", "by", "from", "about", "into", "through", "during",
    "and", "or", "but", "if", "because", "as", "until", "while", "can", "could", "should", "would",
    "will", "shall", "may", "might", "must", "explain", "summarize", "describe", "purpose", "objective",
    "tell", "show", "give", "list", "define", "difference", "between"
}

DEVANAGARI_RANGE = re.compile(r'[\u0900-\u097F]')
WORD_REGEX = re.compile(r"[a-zA-Z\u0900-\u097F']+")

def detect_language(text: str) -> str:
    """
    Detects whether text is Hindi (Devanagari script: 'hi'),
    Hinglish (Roman script Hindi / mixed Hindi-English: 'hinglish'),
    or English ('en').
    """
    if not text or not text.strip():
        return "en"
    
    # 1. Check for Devanagari characters
    devanagari_chars = len(DEVANAGARI_RANGE.findall(text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0900-\u097F]', text))
    
    # If Devanagari is present in meaningful quantity (>15% of alphabetical characters)
    if devanagari_chars >= 2 and total_alpha > 0 and (devanagari_chars / total_alpha) >= 0.15:
        return "hi"
    
    # 2. Extract Roman words
    words = [w.lower() for w in WORD_REGEX.findall(text)]
    if not words:
        return "en"
    
    distinct_hinglish_count = sum(1 for w in words if w in DISTINCT_HINGLISH_WORDS)
    ambiguous_count = sum(1 for w in words if w in AMBIGUOUS_WORDS)
    english_count = sum(1 for w in words if w in COMMON_ENGLISH_WORDS)
    
    # If unambiguous Hinglish words exist (e.g. "kya", "hai", "ka", "ki", "ke", "karo", "kitna", "baare", "ye")
    if distinct_hinglish_count >= 1:
        return "hinglish"
    
    # If only ambiguous words exist along with unambiguous English question words ("what", "why", "how", "this", "which"), it's English
    if english_count >= 2 and distinct_hinglish_count == 0:
        return "en"
        
    return "en"
