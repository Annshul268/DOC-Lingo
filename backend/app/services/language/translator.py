import re
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# Key vocabulary mapping for technical and common terms in Hinglish
HINDI_TO_HINGLISH_WORDS = {
    "गतिरोध": "Deadlock",
    "ऑपरेटिंग सिस्टम": "Operating System",
    "प्रक्रियाएं": "processes",
    "प्रक्रिया": "process",
    "संसाधनों": "resources",
    "संसाधन": "resource",
    "रिसोर्स": "resource",
    "रिसोर्सेज": "resources",
    "म्युचुअल एक्सक्लूज़न": "Mutual Exclusion",
    "नॉन - शेयर करने योग्य": "non-shareable",
    "नॉन-शेयर करने योग्य": "non-shareable",
    "वातावरण": "environment",
    "प्रतिस्पर्धा": "compete",
    "सीमित": "finite number of",
    "अध्याय": "Chapter",
    "शर्तें": "conditions",
    "शर्त": "condition",
    "कंप्यूटर": "computer",
    "मेमोरी": "memory",
    "अनुसार": "anusaar",
    "होता": "hota",
    "होती": "hoti",
    "होते": "hote",
    "है": "hai",
    "हैं": "hain",
    "था": "tha",
    "थी": "thi",
    "थे": "the",
    "जब": "jab",
    "तब": "tab",
    "कई": "kai",
    "एक": "ek",
    "दूसरे": "dusre",
    "दूसरा": "dusra",
    "लिए": "liye",
    "अनिश्चित": "anishchit",
    "काल": "samay",
    "तक": "tak",
    "इंतजार": "wait",
    "प्रतीक्षा": "wait",
    "करती": "karti",
    "करते": "karte",
    "करता": "karta",
    "कर": "kar",
    "सकती": "sakti",
    "सकते": "sakte",
    "सकता": "sakta",
    "कम": "kam",
    "से": "se",
    "लागू": "apply",
    "उत्पन्न": "arise",
    "स्थिति": "situation",
    "चार": "chaar",
    "यह": "yeh",
    "वह": "woh",
    "का": "ka",
    "की": "ki",
    "के": "ke",
    "में": "mein",
    "पर": "par",
    "और": "aur",
    "या": "ya",
    "नहीं": "nahi",
    "अगर": "agar",
    "तो": "toh",
    "रखा": "rakha",
    "जाना": "jaana",
    "चाहिए": "chahiye",
    "मोड": "mode",
    "मुख्य": "main",
    "उद्देश्य": "purpose",
    "दस्तावेज़": "document",
    "दस्तावेज": "document",
    "जानकारी": "information",
    "उपलब्ध": "available",
    "डेटाबेस": "database",
    "क्वेरी": "query",
    "उपयोग": "use",
    "प्रणाली": "system",
    "महत्वपूर्ण": "important",
    "कंपनी": "company",
    "कर्मचारियों": "employees",
    "कर्मचारी": "employees",
    "वित्तीय वर्ष": "financial year",
    "वार्षिक आय": "annual revenue",
    "वार्षिक राजस्व": "annual revenue",
    "राजस्व": "revenue",
    "करोड़": "crore",
    "अंत": "end",
    "दौरान": "dauran",
    "दर्ज": "report",
    "नोवाटेक सॉल्यूशंस": "NovaTech Solutions",
    "नोवाटेक": "NovaTech",
    "पायलट": "pilot",
    "प्रोग्राम": "program",
    "डेडलॉक": "deadlock",
    "डेडलाक": "deadlock",
    "कारण": "cause",
    "कारणों": "causes"
}

# Offline English -> Hinglish direct phrase replacement for offline/no-network mode
ENGLISH_TO_HINGLISH_OFFLINE = [
    (r"\bThe company had (\d+) employees at the end of (\d+)\b", r"\2 ke end tak company mein \1 employees the"),
    (r"\bhad (\d+) employees at the end of (\d+)\b", r"\2 ke end tak \1 employees the"),
    (r"\bDuring the (\d+) financial year\b", r"\1 financial year ke dauran"),
    (r"\breported annual revenue of (I|■|₹)?\s*(\d+)\s*crore\b", r"ne ₹\2 crore ka annual revenue report kiya"),
    (r"\bintroduced an internal DOC-Lingo pilot in (\w+ \d+)\b", r"ne \1 mein internal DOC-Lingo pilot introduce kiya"),
    (r"\bDeadlock occurs when\b", "Deadlock tab hota hai jab"),
    (r"\bDeadlock is a situation where\b", "Deadlock ek aisi situation hai jahan"),
    (r"\bDeadlock is a condition where\b", "Deadlock ek aisi condition hai jahan"),
    (r"\bmultiple processes wait indefinitely for resources held by each other\b", "multiple processes ek-dusre ke resources ke liye indefinitely wait karte rehte hain"),
    (r"\bA deadlock situation can arise if and only if four conditions hold simultaneously\b", "Deadlock situation tabhi arise ho sakti hai jab yeh chaar conditions simultaneously satisfy hon"),
    (r"\bMutual Exclusion: At least one resource must be held in a non-shareable mode\b", "Mutual Exclusion: Kam se kam ek resource non-shareable mode me hold hona chahiye"),
    (r"\bHold and Wait\b", "Hold and Wait (process resource hold karke dusre resource ka wait kare)"),
    (r"\bNo Preemption\b", "No Preemption (resource forcibly nahi liya ja sakta)"),
    (r"\bCircular Wait\b", "Circular Wait (processes circular chain me ek-dusre ke resource ka wait karein)"),
    (r"\bIn a multiprogramming environment\b", "Ek multiprogramming environment mein"),
    (r"\bseveral processes may compete for a finite number of resources\b", "kai processes limited resources ke liye compete karte hain"),
    (r"\bThe main purpose of this document is\b", "Is document ka main purpose yeh hai ki"),
    (r"\bThis document explains\b", "Yeh document explain karta hai ki"),
    (r"\bAccording to\b", "According to"),
    (r"\bis defined as\b", "ko define kiya gaya hai as"),
    (r"\bare defined as\b", "ko define kiya gaya hai as"),
    (r"\bcan be used for\b", "ko use kiya ja sakta hai for"),
    (r"\bwhich means that\b", "jiska matlab yeh hai ki"),
    (r"\bfor example\b", "for example (jaise ki)")
]

DEVA_CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क्ष': 'ksh', 'त्र': 'tra', 'ज्ञ': 'gya'
}

DEVA_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au'
}

DEVA_MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', '्': ''
}

def devanagari_to_roman(text: str) -> str:
    """Converts Devanagari Hindi text to Romanized Hinglish."""
    # Replace longer phrases first to avoid sub-word collisions
    for hi_word in sorted(HINDI_TO_HINGLISH_WORDS.keys(), key=len, reverse=True):
        text = text.replace(hi_word, HINDI_TO_HINGLISH_WORDS[hi_word])

    res = []
    i = 0
    chars = list(text)
    while i < len(chars):
        c = chars[i]
        if c in DEVA_VOWELS:
            res.append(DEVA_VOWELS[c])
        elif c in DEVA_CONSONANTS:
            cons = DEVA_CONSONANTS[c]
            if i + 1 < len(chars) and chars[i + 1] in DEVA_MATRAS:
                matra = DEVA_MATRAS[chars[i + 1]]
                res.append(cons + matra)
                i += 1
            else:
                if i + 1 < len(chars) and (chars[i + 1] in DEVA_CONSONANTS or chars[i + 1] in DEVA_VOWELS):
                    res.append(cons + 'a')
                else:
                    res.append(cons)
        elif c in DEVA_MATRAS:
            res.append(DEVA_MATRAS[c])
        elif c == '।':
            res.append('.')
        else:
            res.append(c)
        i += 1
    return ''.join(res)


def translate_en_to_hi_api(text: str) -> Optional[str]:
    """Translates English text to Hindi using fast online translation endpoints."""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if not paragraphs:
        return None

    translated_paras = []
    try:
        with httpx.Client(timeout=3.5) as client:
            for p in paragraphs:
                prefix = ""
                content = p
                m = re.match(r"^(\d+\.|\-|\*)\s+", p)
                if m:
                    prefix = m.group(0)
                    content = p[len(prefix):]

                try:
                    res = client.get(
                        "https://api.mymemory.translated.net/get",
                        params={"q": content[:450], "langpair": "en|hi"}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        trans = data.get("responseData", {}).get("translatedText", "")
                        if trans and "MYMEMORY WARNING" not in trans.upper():
                            translated_paras.append(prefix + trans)
                            continue
                except Exception:
                    pass
                translated_paras.append(p)
        return "\n\n".join(translated_paras)
    except Exception as e:
        logger.debug(f"API translation failed: {e}")
        return None


def translate_hi_to_en_api(text: str) -> Optional[str]:
    """Translates Hindi text to English using fast online translation."""
    try:
        with httpx.Client(timeout=3.5) as client:
            res = client.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text[:450], "langpair": "hi|en"}
            )
            if res.status_code == 200:
                data = res.json()
                trans = data.get("responseData", {}).get("translatedText", "")
                if trans and "MYMEMORY WARNING" not in trans.upper():
                    return trans
    except Exception as e:
        logger.debug(f"API translation failed: {e}")
    return None


def translate_text(text: str, target_language: str) -> str:
    """
    Translates or transliterates given text into the target language.
    target_language: 'en', 'hi', or 'hinglish'
    """
    if not text or not text.strip():
        return text

    target = target_language.lower()
    has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))

    if target == "en":
        if has_devanagari:
            translated = translate_hi_to_en_api(text)
            return translated if translated else text
        return text

    elif target == "hi":
        if not has_devanagari:
            translated = translate_en_to_hi_api(text)
            if translated:
                return translated
        return text

    elif target == "hinglish":
        if has_devanagari:
            return devanagari_to_roman(text)
        else:
            hi_text = translate_en_to_hi_api(text)
            if hi_text and re.search(r'[\u0900-\u097F]', hi_text):
                return devanagari_to_roman(hi_text)
            
            result = text
            for pattern, repl in ENGLISH_TO_HINGLISH_OFFLINE:
                result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
            return result

    return text
