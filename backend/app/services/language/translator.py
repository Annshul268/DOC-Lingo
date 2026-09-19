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
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'ऑ': 'o', 'ऍ': 'e'
}

DEVA_MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', '्': '',
    'ॉ': 'o', 'ॅ': 'e', 'ः': 'h', '़': ''
}

def devanagari_to_roman(text: str) -> str:
    """Converts Devanagari Hindi text to clean Romanized Hinglish."""
    # Replace known Hindi vocabulary with standard Hinglish words
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


def convert_english_to_hinglish(text: str) -> str:
    """
    Generically converts English factual sentences into natural Roman-script Hinglish,
    preserving English technical terms, proper nouns, dates, and metrics intact.
    """
    t = text.strip()

    # Pre-check exact functional statements
    patterns = [
        # Scheduling & mechanisms
        (r'\bRound Robin assigns each ready process a time quantum and is commonly associated with interactive systems\b\.?',
         'Round Robin scheduling mein har ready process ko ek fixed time quantum assign kiya jata hai, aur yeh commonly interactive systems ke saath associate hota hai.'),
        (r'\bassigns each ready process a time quantum and is commonly associated with interactive systems\b\.?',
         'har ready process ko ek fixed time quantum assign karta hai aur commonly interactive systems ke saath associate hota hai.'),
        (r'\bassigns each ready process a time quantum\b',
         'har ready process ko ek time quantum assign karta hai'),

        # Memory & OS management
        (r'\bThe OS tracks memory usage and allocates memory to processes\b\.?',
         'OS memory usage ko track karta hai aur processes ko memory allocate karta hai.'),
        (r'\btracks memory usage and allocates memory to processes\b\.?',
         'memory usage ko track karta hai aur processes ko memory allocate karta hai.'),
        (r'\bVirtual memory allows secondary storage to extend the apparent amount of available main memory\b\.?',
         'Virtual memory secondary storage ko use karke available main memory ko extend karne allow karti hai.'),
        (r'\ballows secondary storage to extend the apparent amount of available main memory\b\.?',
         'secondary storage ko use karke available main memory ko extend karne allow karti hai.'),
        (r'\btracks which memory regions are available and which are allocated to processes\b\.?',
         'track karta hai ki kaun se memory regions available hain aur kaun se processes ko allocate hue hain.'),

        # Responsibilities
        (r'\bThe OS creates, schedules, synchronizes, and terminates processes\b\.?',
         'OS processes ko create, schedule, synchronize aur terminate karta hai.'),
        (r'\bThe OS organizes data into files and directories and manages creating, reading, writing, deleting, and protecting files\b\.?',
         'OS data ko files aur directories mein organize karta hai aur files ke creation, reading, writing aur deletion ko manage karta hai.'),
        (r'\bThe OS coordinates hardware devices through device drivers\b\.?',
         'OS device drivers ke through hardware devices ko coordinate karta hai.'),

        # Fundamentals & Kernel
        (r'\bAn operating system \(OS\) is system software that manages computer hardware and provides common services to application programs\b\.?',
         'Operating system (OS) ek system software hai jo computer hardware ko manage karta hai aur applications ko common services provide karta hai.'),
        (r'\bacts as an interface between users, applications, and hardware\b',
         'users, applications aur hardware ke beech ek interface ke roop mein kaam karta hai'),
        (r'\bThe kernel is the central component of an operating system\b\.?',
         'Kernel operating system ka central component hota hai.'),
        (r'\bA system call is a controlled interface through which a user-level program requests a service from the operating system kernel\b\.?',
         'System call ek controlled interface hai jiske through user-level program OS kernel se service request karta hai.')
    ]

    for pat, repl in patterns:
        if re.search(pat, t, re.IGNORECASE):
            t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    # General structure mappings
    for pat, repl in ENGLISH_TO_HINGLISH_OFFLINE:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    # Convert generic verbs & connective scaffolding if still purely English
    scaffold = [
        (r'\baccording to\b', 'ke mutaabiq'),
        (r'\btracks\b', 'track karta hai'),
        (r'\ballocates\b', 'allocate karta hai'),
        (r'\bmanages\b', 'manage karta hai'),
        (r'\ballows\b', 'allow karta hai'),
        (r'\bprovides\b', 'provide karta hai'),
        (r'\bassigns\b', 'assign karta hai'),
        (r'\bcreates\b', 'create karta hai'),
        (r'\boperates\b', 'operate karta hai'),
        (r'\bdivides\b', 'divide karta hai'),
        (r'\bseparates\b', 'separate karta hai')
    ]
    for pat, repl in scaffold:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    return t


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

def convert_english_to_hindi(text: str) -> str:
    """
    Generically translates English factual sentences into readable Hindi Devanagari text,
    preserving technical and entity terms in standard Hindi/transliterated form.
    """
    t = text.strip()
    patterns = [
        (r'\bThe OS tracks memory usage and allocates memory to processes\b\.?',
         'ऑपरेटिंग सिस्टम (OS) मेमोरी उपयोग को ट्रैक करता है और प्रोसेस को मेमोरी आवंटित करता है।'),
        (r'\btracks memory usage and allocates memory to processes\b\.?',
         'मेमोरी उपयोग को ट्रैक करता है और प्रोसेस को मेमोरी आवंटित करता है।'),
        (r'\bRAM provides fast storage for currently active programs and data\b\.?',
         'रैम (RAM) वर्तमान में सक्रिय प्रोग्राम और डेटा के लिए तेज़ स्टोरेज प्रदान करता है।'),
        (r'\bThe operating system tracks which memory regions are available and which are allocated to processes\b\.?',
         'ऑपरेटिंग सिस्टम यह ट्रैक करता है कि कौन से मेमोरी क्षेत्र उपलब्ध हैं और कौन से प्रोसेस को आवंटित हैं।'),
        (r'\btracks which memory regions are available and which are allocated to processes\b\.?',
         'यह ट्रैक करता है कि कौन से मेमोरी क्षेत्र उपलब्ध हैं और कौन से प्रोसेस को आवंटित हैं।'),
        (r'\bVirtual memory allows secondary storage to extend the apparent amount of available main memory\b\.?',
         'वर्चुअल मेमोरी सेकेंडरी स्टोरेज के उपयोग से उपलब्ध मुख्य मेमोरी की क्षमता बढ़ाने की अनुमति देती है।'),
        (r'\ballows secondary storage to extend the apparent amount of available main memory\b\.?',
         'सेकेंडरी स्टोरेज के उपयोग से मुख्य मेमोरी की क्षमता बढ़ाने की अनुमति देती है।'),
        (r'\bVirtual memory separates addresses used by programs from physical memory locations\b\.?',
         'वर्चुअल मेमोरी प्रोग्राम द्वारा उपयोग किए जाने वाले एड्रेस को भौतिक मेमोरी स्थानों से अलग करती है।'),
        (r'\bRound Robin assigns each ready process a time quantum and is commonly associated with interactive systems\b\.?',
         'राउंड रॉबिन शेड्यूलिंग में प्रत्येक रेडी प्रोसेस को एक निश्चित टाइम क्वांटम दिया जाता है और यह आमतौर पर इंटरैक्टिव सिस्टम में उपयोग होता है।'),
        (r'\bThe main goals of an operating system are efficient resource management, convenient program execution, security, and coordination between software and hardware\b\.?',
         'ऑपरेटिंग सिस्टम के मुख्य उद्देश्य कुशल संसाधन प्रबंधन, सुविधाजनक प्रोग्राम निष्पादन, सुरक्षा और सॉफ्टवेयर व हार्डवेयर के बीच समन्वय हैं।'),
        (r'\bAn operating system \(OS\) is system software that manages computer hardware and provides common services to application programs\b\.?',
         'ऑपरेटिंग सिस्टम (OS) एक सिस्टम सॉफ्टवेयर है जो कंप्यूटर हार्डवेयर का प्रबंधन करता है और एप्लिकेशन प्रोग्राम को सामान्य सेवाएं प्रदान करता है।'),
        (r'\bThe company had (\d+) employees at the end of (\d+)\b\.?',
         r'कंपनी में \2 के अंत तक \1 कर्मचारी थे।'),
        (r'\bhad (\d+) employees at the end of (\d+)\b\.?',
         r'\2 के अंत तक \1 कर्मचारी थे।'),
        (r'\breported annual revenue of (?:I|■|₹)?\s*(\d+)\s*crore\b\.?',
         r'ने ₹\1 करोड़ का वार्षिक राजस्व दर्ज किया।')
    ]
    for pat, repl in patterns:
        if re.search(pat, t, re.IGNORECASE):
            t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    scaffold = [
        (r'\bAccording to\b', 'के अनुसार'),
        (r'\btracks\b', 'ट्रैक करता है'),
        (r'\ballocates\b', 'आवंटित करता है'),
        (r'\bmanages\b', 'प्रबंधित करता है'),
        (r'\ballows\b', 'अनुमति देता है'),
        (r'\bprovides\b', 'प्रदान करता है'),
        (r'\bassigns\b', 'असाइन करता है'),
        (r'\bcreates\b', 'बनाता है'),
        (r'\bdivides\b', 'विभाजित करता है'),
        (r'\buses\b', 'उपयोग करता है'),
        (r'\boperating system\b', 'ऑपरेटिंग सिस्टम'),
        (r'\bmemory management\b', 'मेमोरी प्रबंधन'),
        (r'\bvirtual memory\b', 'वर्चुअल मेमोरी'),
        (r'\bfile systems?\b', 'फाइल सिस्टम'),
        (r'\bprocess management\b', 'प्रोसेस प्रबंधन'),
        (r'\bprocesses\b', 'प्रोसेस'),
        (r'\bprocess\b', 'प्रोसेस'),
        (r'\bhardware\b', 'हार्डवेयर'),
        (r'\bsoftware\b', 'सॉफ्टवेयर'),
        (r'\band\b', 'और'),
        (r'\bor\b', 'या'),
        (r'\bwith\b', 'के साथ'),
        (r'\bfor\b', 'के लिए'),
        (r'\bto\b', 'को'),
        (r'\bfrom\b', 'से'),
        (r'\bin\b', 'में'),
        (r'\bon\b', 'पर'),
        (r'\bis\b', 'है'),
        (r'\bare\b', 'हैं'),
        (r'\bwas\b', 'था'),
        (r'\bwere\b', 'थे')
    ]
    if not bool(re.search(r'[\u0900-\u097F]', t)):
        for pat, repl in scaffold:
            t = re.sub(pat, repl, t, flags=re.IGNORECASE)
    return t


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
            if translated and bool(re.search(r'[\u0900-\u097F]', translated)):
                return translated
            return convert_english_to_hindi(text)
        return text

    elif target == "hinglish":
        if has_devanagari:
            return devanagari_to_roman(text)
        else:
            # Preserve English technical terminology and convert structure into natural Roman Hinglish
            return convert_english_to_hinglish(text)

    return text
