import re
from enum import Enum
from typing import Set, List, Dict
from pydantic import BaseModel

class IntentType(str, Enum):
    TYPES_LIST = "types_list"          # types, categories, classification, components, list
    DEFINITION = "definition"          # what is, define, meaning, concept
    FUNCTION_ROLE = "function_role"    # functions, responsibilities, role, purpose, what does X do
    PROCESS_HOW = "process_how"        # how, how does it work, mechanism, steps
    ADVANTAGES = "advantages"          # advantages, benefits, pros, merits
    DISADVANTAGES = "disadvantages"    # disadvantages, limitations, drawbacks, cons
    COMPARISON = "comparison"          # compare, difference between, vs
    EXAMPLES = "examples"              # examples of, instances
    GENERAL = "general"

class QueryAnalysis(BaseModel):
    raw_query: str
    intent: IntentType
    subject_words: Set[str]
    intent_keywords: Set[str]
    query_years: Set[str]

# Language-agnostic intent detection keyword patterns
_INTENT_PATTERNS: Dict[IntentType, List[str]] = {
    IntentType.TYPES_LIST: [
        r'\btypes?\b', r'\bkinds?\b', r'\bcategor(?:y|ies)\b', r'\bclassifications?\b',
        r'\bclasses\b', r'\bcomponents?\b', r'\bforms?\b', r'\bvarieties\b', r'\blists?\b',
        r'\bapproaches\b', r'\bkis\s+type\b', r'\bkitne\s+types?\b', r'\btypes?\s+kya\b',
        r'\btype\s+batao\b', r'\bप्रकार\b', r'\bवर्गीकरण\b', r'\bश्रेणियां?\b', r'\bभेद\b'
    ],
    IntentType.ADVANTAGES: [
        r'\badvantages?\b', r'\bbenefits?\b', r'\bmerits?\b', r'\bpros\b',
        r'\bfayde\b', r'\bfayda\b', r'\bलाभ\b', r'\bफ़ायदे\b'
    ],
    IntentType.DISADVANTAGES: [
        r'\bdisadvantages?\b', r'\blimitations?\b', r'\bdrawbacks?\b', r'\bdemerits?\b', r'\bcons\b',
        r'\bnuksan\b', r'\bkamiyan\b', r'\bहानि\b', r'\bनुकसान\b', r'\bसीमाएं\b'
    ],
    IntentType.COMPARISON: [
        r'\bcompare\b', r'\bcomparison\b', r'\bdifference\s+between\b', r'\bdiffer\b', r'\bvs\b', r'\bversus\b',
        r'\bantar\b', r'\btulna\b', r'\bअंतर\b', r'\bतुलना\b'
    ],
    IntentType.EXAMPLES: [
        r'\bexamples?\b', r'\binstances?\b', r'\bcommon\b', r'\bpopular\b', r'\bउदाहरण\b', r'\bmisaal\b'
    ],
    IntentType.FUNCTION_ROLE: [
        r'\bfunctions?\b', r'\bresponsibilit(?:y|ies)\b', r'\broles?\b', r'\bpurposes?\b',
        r'\bobjectives?\b', r'\bgoals?\b', r'\bwhat\s+does\b.*\bdo\b', r'\bwhat\s+do\b.*\bdo\b',
        r'\bkya\s+karta\b', r'\bkya\s+karti\b', r'\bkya\s+karte\b', r'\bkaam\s+kya\b',
        r'\bकार्य\b', r'\bभूमिका\b', r'\bउद्देश्य\b'
    ],
    IntentType.PROCESS_HOW: [
        r'\bhow\s+does\b', r'\bhow\s+do\b', r'\bhow\s+is\b', r'\bhow\s+to\b',
        r'\bmechanism\b', r'\bsteps\b', r'\bworking\b', r'\bkaise\s+kaam\b',
        r'\bkaise\s+karta\b', r'\bkaise\s+hoti\b', r'\bप्रक्रिया\b', r'\bकार्यप्रणाली\b'
    ],
    IntentType.DEFINITION: [
        r'\bwhat\s+is\b', r'\bwhat\s+are\b', r'\bdefine\b', r'\bdefinition\b',
        r'\bmeaning\s+of\b', r'\bconcept\s+of\b', r'\bkya\s+hai\b', r'\bkya\s+hota\b',
        r'\bkya\s+h\b', r'\bपरिभाषा\b', r'\bअर्थ\b'
    ]
}

def analyze_query(query: str, stopwords: Set[str] = None) -> QueryAnalysis:
    """
    Analyzes user query to extract grammatical intent, subject keywords, and temporal constraints.
    Completely generic and domain-independent.
    """
    stopwords = stopwords or set()
    q_lower = query.lower()

    # 1. Temporal constraints (years)
    years = set(re.findall(r'\b(19\d\d|20\d\d)\b', query))

    # 2. Determine primary query intent
    detected_intent = IntentType.GENERAL
    matched_intent_words = set()

    for intent, patterns in _INTENT_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, q_lower)
            if m:
                detected_intent = intent
                matched_intent_words.add(m.group(0))
                break
        if detected_intent != IntentType.GENERAL:
            break

    # 3. Extract subject keywords (excluding stopwords, intent keywords, and years)
    raw_words = set(re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', q_lower))
    
    # Expand matched intent words into tokens
    intent_tokens = set()
    for iw in matched_intent_words:
        intent_tokens.update(re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', iw))

    # Also add standard intent words to exclude from subject keywords
    generic_intent_tokens = {
        'what', 'why', 'how', 'when', 'where', 'who', 'which',
        'type', 'types', 'kind', 'kinds', 'category', 'categories', 'classification',
        'function', 'functions', 'role', 'roles', 'responsibility', 'responsibilities',
        'advantage', 'advantages', 'benefit', 'benefits', 'disadvantage', 'disadvantages',
        'difference', 'compare', 'define', 'definition', 'meaning', 'example', 'examples',
        'explain', 'describe', 'tell', 'show', 'give', 'list',
        'kya', 'kaise', 'kab', 'kahan', 'kis', 'kitna', 'kitne',
        'prakar', 'vargikaran', 'karya', 'fayde', 'nuksan', 'antar'
    }

    subject_words = {
        w for w in raw_words
        if len(w) > 2
        and w not in stopwords
        and w not in years
        and w not in intent_tokens
        and w not in generic_intent_tokens
    }

    return QueryAnalysis(
        raw_query=query,
        intent=detected_intent,
        subject_words=subject_words,
        intent_keywords=matched_intent_words,
        query_years=years
    )
