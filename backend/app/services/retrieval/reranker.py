import re
import logging
from typing import List
from backend.app.schemas.chat import Citation

logger = logging.getLogger(__name__)

class GenericRAGReranker:
    """
    Production-grade, generic reranker and relevance filter for multilingual RAG.
    
    Distinguishes between:
    1. Actual factual evidence passages vs. interrogative lists / example questions.
    2. Temporal alignment (e.g. matching queries for year Y with chunks containing year Y,
       while penalizing chunks with conflicting years).
    3. Lexical and entity alignment across multilingual and cross-lingual queries.
    """

    STOPWORDS = {
        'what', 'was', 'is', 'are', 'were', 'the', 'in', 'on', 'at', 'of', 'for', 'to',
        'a', 'an', 'and', 'or', 'how', 'many', 'much', 'did', 'does', 'do', 'which',
        'who', 'whom', 'where', 'when', 'why', 'about', 'from', 'with', 'by', 'its',
        'has', 'have', 'had', 'been', 'will', 'would', 'could', 'should',
        'kya', 'hai', 'hain', 'ha', 'h', 'tha', 'thi', 'the', 'ka', 'ki', 'ke', 'ko', 'me', 'mein',
        'se', 'par', 'aur', 'ya', 'kitna', 'kitne', 'kitni', 'kab', 'kahan', 'kaise',
        'tak', 'ek', 'bhi', 'kisi', 'kisko', 'iska', 'iski', 'iske',
        'karta', 'karti', 'karte', 'kare', 'karna', 'karke', 'hota', 'hoti', 'hote',
        'kaam', 'kis', 'tarah', 'waqt', 'baare', 'kuch', 'hoga', 'hogi',
        'kaun', 'kaunsa', 'kaunsi', 'kaunse', 'diya', 'diye', 'gaya', 'gayi', 'gaye'
    }

    COMMON_ACRONYMS = {
        'os': ['operating', 'system'],
        'ai': ['artificial', 'intelligence'],
        'ui': ['user', 'interface'],
        'db': ['database'],
        'fs': ['file', 'system'],
        'ip': ['internet', 'protocol'],
        'io': ['input', 'output'],
        'cpu': ['processor', 'central', 'processing', 'unit'],
        'ram': ['memory', 'random', 'access', 'memory']
    }

    _BASE_SYNONYMS = {
        'कर्मचारी': ['employee', 'employees', 'staff', 'workforce', 'headcount'],
        'कर्मचारियों': ['employee', 'employees', 'staff', 'workforce', 'headcount'],
        'राजस्व': ['revenue', 'turnover', 'income', 'earnings'],
        'आय': ['revenue', 'income', 'earnings'],
        'स्थापना': ['established', 'founded'],
        'शुरुआत': ['started', 'introduced', 'began'],
        'ग्राहक': ['customer', 'client'],
        'ग्राहकों': ['customers', 'clients'],
        'उद्देश्य': ['objective', 'purpose', 'goal'],
        'पायलट': ['pilot'],
        'नौकरी': ['job', 'employment'],
        'डेडलॉक': ['deadlock'],
        'डेडलाक': ['deadlock'],
        'कारण': ['cause', 'causes', 'reason', 'conditions'],
        'कारणों': ['cause', 'causes', 'reason', 'conditions'],
        'प्राथमिक': ['primary'],
        'कुंजी': ['key'],
        'प्रक्रिया': ['process', 'processes'],
        'प्रोसेस': ['process', 'processes'],
        'शेड्यूलिंग': ['scheduling', 'scheduler'],
        'सिस्टम': ['system', 'systems'],
        'मैनेजमेंट': ['management', 'manager'],
        'प्रबंधन': ['management', 'manage', 'manager'],
        'सुरक्षा': ['security', 'protection', 'secure'],
        'मेमोरी': ['memory', 'ram', 'storage'],
        'स्मृति': ['memory', 'ram'],
        'फ़ाइल': ['file', 'files', 'filesystem'],
        'फाइल': ['file', 'files', 'filesystem'],
        'नेटवर्क': ['network', 'networking'],
        'कर्नेल': ['kernel']
    }

    CROSS_LINGUAL_SYNONYMS = {}
    for _k, _vals in _BASE_SYNONYMS.items():
        _cluster = [_k] + _vals
        for _term in _cluster:
            _t_lower = _term.lower()
            if _t_lower not in CROSS_LINGUAL_SYNONYMS:
                CROSS_LINGUAL_SYNONYMS[_t_lower] = []
            for _other in _cluster:
                if _other.lower() != _t_lower and _other.lower() not in CROSS_LINGUAL_SYNONYMS[_t_lower]:
                    CROSS_LINGUAL_SYNONYMS[_t_lower].append(_other.lower())

    GENERIC_WORDS = {
        'document', 'documents', 'file', 'page', 'information', 'detail', 'details',
        'tell', 'show', 'give', 'explain', 'describe', 'about', 'this', 'that', 'with',
        'company', 'organization', 'firm', 'business', 'system', 'systems',
        'end', 'start', 'beginning', 'middle', 'total', 'all'
    }

    EXPLANATORY_PREDICATES = {
        'tracks', 'track', 'allocates', 'allocate', 'manages', 'manage', 'allows', 'allow',
        'provides', 'provide', 'creates', 'create', 'divides', 'divide', 'operates', 'operate',
        'controls', 'control', 'uses', 'use', 'performs', 'perform', 'works', 'work',
        'assigns', 'assign', 'defined', 'refers', 'acts', 'is', 'are', 'was', 'were',
        'had', 'has', 'have',
        'karta', 'karti', 'karte', 'hota', 'hoti', 'hote', 'diya', 'kiya'
    }

    LIST_MARKERS = [
        'include', 'includes', 'examples include', 'approaches include', 'types include', 'such as'
    ]

    def _extract_focused_excerpt(self, text: str, content_words: set, query_years: set) -> str:
        """Extracts the specific paragraph or section that actually contains the factual evidence."""
        # Generic cleaning of page headers/footers and unmapped glyph artifacts
        cleaned_text = re.sub(r'(?i)\b(?:page\s*\d+(?:\s*(?:of|—|-)\s*\d+)?|\d+\s*\|\s*page)\b', '', text)
        cleaned_text = re.sub(r'(?i)^[A-Za-z0-9\s—–•?]+\s*[—–•?]\s*(?:Page\s*\d+|\d+)\s*$', '', cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'(?i)\b[A-Za-z0-9\s—–•]+\s*[?•—–-]\s*Page\s*\d+\s*$', '', cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'[ \t]+\?[ \t]*$', '', cleaned_text, flags=re.MULTILINE)

        # Split text into paragraphs preserving structure
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\n(?=[A-Z][a-zA-Z\s]{2,35}:)', cleaned_text) if p.strip()]
        if not paragraphs:
            return text.strip()

        scored_paragraphs = []
        for p in paragraphs:
            p_lower = p.lower()
            score = 0.0
            for w in content_words:
                if re.search(r'\b' + re.escape(w) + r'\b', p_lower):
                    score += 2.0
                    if w in self.CROSS_LINGUAL_SYNONYMS:
                        score += 2.5
            for y in query_years:
                if y in p:
                    score += 3.0
            if re.search(r'\b\d+\b', p):
                score += 0.5
            # Penalize question lines heavily - evidence must be declarative facts
            if p.strip().endswith('?') or '?' in p:
                score -= 15.0

            # Predicate vs bare heading scoring
            has_pred = any(re.search(r'\b' + re.escape(pred) + r'\b', p_lower) for pred in self.EXPLANATORY_PREDICATES)
            if len(p) < 60 and not p.endswith(('.', '!', '?', '।', ':')) and not has_pred:
                score -= 3.0
            elif has_pred:
                score += 1.5

            scored_paragraphs.append((score, p))

        scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
        if scored_paragraphs and scored_paragraphs[0][0] > 0:
            return scored_paragraphs[0][1].strip()

        return text.strip()

    def rerank(self, query: str, citations: List[Citation], top_k: int = 4) -> List[Citation]:
        if not citations:
            return []

        from backend.app.services.language.translator import devanagari_to_roman

        # 1. Extract query temporal constraints
        query_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', query))

        # 2. Extract content keywords and expand cross-lingually (excluding query years)
        raw_words = re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', query.lower())
        query_keywords = [
            w for w in raw_words 
            if (len(w) > 2 or w in self.COMMON_ACRONYMS)
            and w not in self.STOPWORDS 
            and w not in query_years
        ]

        expanded_keywords = set()
        for kw in query_keywords:
            expanded_keywords.add(kw)
            if kw in self.COMMON_ACRONYMS:
                expanded_keywords.update(self.COMMON_ACRONYMS[kw])
            roman = devanagari_to_roman(kw).lower()
            if roman and (len(roman) > 2 or roman in self.COMMON_ACRONYMS):
                expanded_keywords.add(roman)
                if roman in self.COMMON_ACRONYMS:
                    expanded_keywords.update(self.COMMON_ACRONYMS[roman])
            if kw in self.CROSS_LINGUAL_SYNONYMS:
                expanded_keywords.update(self.CROSS_LINGUAL_SYNONYMS[kw])
            if roman in self.CROSS_LINGUAL_SYNONYMS:
                expanded_keywords.update(self.CROSS_LINGUAL_SYNONYMS[roman])

        content_query_words = {
            w for w in expanded_keywords 
            if w not in self.GENERIC_WORDS and (len(w) > 2 or w in self.COMMON_ACRONYMS)
        }

        # Construct key bigram phrases from adjacent query keywords
        phrase_patterns = []
        for i in range(len(query_keywords) - 1):
            w1, w2 = query_keywords[i], query_keywords[i+1]
            syn1 = [w1] + self.CROSS_LINGUAL_SYNONYMS.get(w1, []) + [devanagari_to_roman(w1).lower()]
            syn2 = [w2] + self.CROSS_LINGUAL_SYNONYMS.get(w2, []) + [devanagari_to_roman(w2).lower()]
            for s1 in syn1:
                for s2 in syn2:
                    if len(s1) > 2 and len(s2) > 2:
                        phrase_patterns.append(f"{s1} {s2}")
        phrase_set = set(phrase_patterns)

        # Check if query is explanatory/functional ("what does X do", "what is X", "how does X work", "kaise kaam karta hai", "kya hota hai")
        is_explanatory_query = any(q_word in query.lower() for q_word in [
            'what does', 'what do', 'what is', 'what are', 'how does', 'how do', 'explain', 'kaise',
            'kya karta', 'kya karti', 'kya karte', 'kya hota', 'kya h', 'role', 'function', 'purpose', 'work', 'works'
        ])

        scored_citations = []
        for c in citations:
            text = c.text_snippet
            # Normalize currency font artifacts (e.g. 'I84 crore' -> '₹84 crore')
            text = re.sub(r'(?<=\s)[I■](?=\d+\s*(?:crore|lakh|thousand|million|billion|\b))', '₹', text)
            text_lower = text.lower()
            score = float(c.similarity_score)

            # --- Signal 1: Question vs. Factual Evidence Analysis ---
            # Clean inline font artifacts (e.g. unmapped bullet/em-dash glyphs extracted as '?')
            text_cleaned = re.sub(r'(?<=\w)\s+[?•—–-]\s+(?=\w)', ' - ', text)
            text_cleaned = re.sub(r'[ \t]+\?[ \t]*$', '', text_cleaned, flags=re.MULTILINE)
            has_pred = any(re.search(r'\b' + re.escape(pred) + r'\b', text_lower) for pred in self.EXPLANATORY_PREDICATES)

            # If the chunk consists of sample/exercise questions without declarative facts, skip it
            lines = [l.strip() for l in text_cleaned.split('\n') if l.strip()]
            q_lines = [l for l in lines if '?' in l]
            fact_lines = [l for l in lines if '?' not in l and len(l) > 30 and not 'page ' in l.lower()]
            if len(q_lines) >= 2 and len(fact_lines) == 0:
                continue

            interrogatives = re.findall(r'(?i)\b(?:what|how|why|when|where|which|who|kya|kaise|kitna|kab|kahan|kis)\b[^.?!।\n]*\?', text_cleaned)
            # If the chunk consists of sample/exercise questions without explanatory predicates, skip it
            if (len(interrogatives) >= 2 or text_cleaned.count('?') >= 2) and not has_pred:
                continue
            if text_cleaned.strip().endswith('?') and len(text_cleaned) < 150 and not has_pred:
                continue

            if re.search(r'\b\d+\b', text):
                score += 0.06

            # --- Signal 2: Temporal / Year Disambiguation ---
            chunk_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', text))
            if query_years:
                matching_years = query_years.intersection(chunk_years)
                conflicting_years = chunk_years - query_years
                if conflicting_years and not matching_years:
                    continue
                if not chunk_years and not matching_years:
                    score -= 0.30
                if matching_years:
                    score += 0.30

            # --- Signal 3: Lexical, Entity & Phrase Overlap ---
            matched_content_words = {w for w in content_query_words if w in text_lower}
            topic_concept_matches = sum(
                1 for kw in content_query_words if any(syn in text_lower for syn in self.CROSS_LINGUAL_SYNONYMS.get(kw, []))
            )
            has_phrase_match = any(p in text_lower for p in phrase_set)

            # If query has specific content keywords, chunk MUST match at least one to be supporting evidence
            if content_query_words and not matched_content_words:
                continue

            if content_query_words:
                kw_ratio = len(matched_content_words) / len(content_query_words)
                score += 0.25 * kw_ratio
            if topic_concept_matches > 0:
                score += 0.25
            if has_phrase_match:
                score += 0.30

            # --- Signal 4: Explanatory Predicate vs. Mere List vs. Heading Only ---
            has_pred = any(re.search(r'\b' + re.escape(pred) + r'\b', text_lower) for pred in self.EXPLANATORY_PREDICATES)
            is_mere_list = any(re.search(r'\b' + re.escape(m) + r'\b', text_lower) for m in self.LIST_MARKERS)
            
            if is_explanatory_query:
                if has_pred:
                    score += 0.20
                if is_mere_list and not has_pred:
                    score -= 0.20

            # Penalize chunks that are just solitary headings without explanatory predicates
            if len(text.strip()) < 60 and not has_pred and not text.strip().endswith(('.', '!', '?', '।')):
                score -= 0.35

            # Extract the focused supporting excerpt
            focused_snippet = self._extract_focused_excerpt(text, content_query_words, query_years)
            if focused_snippet.strip().endswith('?'):
                continue
            is_interrogative = bool(re.search(
                r'(?i)\b(?:what|how|why|when|where|which|who|kya|kaise|kitna|kab|kahan|kis)\b.*\?',
                focused_snippet.strip()
            ))
            if is_interrogative and len(focused_snippet) < 180 and not has_pred:
                continue

            # Bound score to [0.0, 1.0] for clean reporting
            normalized_score = round(max(0.0, min(1.0, score)), 4)

            reranked_citation = Citation(
                document_id=c.document_id,
                filename=c.filename,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                text_snippet=focused_snippet,
                similarity_score=normalized_score
            )
            scored_citations.append((score, topic_concept_matches, reranked_citation))

        # Sort descending by calculated score
        scored_citations.sort(key=lambda x: x[0], reverse=True)

        # Deduplicate citations by filename, page number, and text snippet prefix
        seen_keys = set()
        deduped = []
        for s, concept_matches, cite in scored_citations:
            norm_prefix = re.sub(r'\s+', ' ', cite.text_snippet.lower()[:80])
            key = (cite.filename, cite.page_number, norm_prefix)
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append((s, concept_matches, cite))

        if not deduped:
            return []

        top_score = deduped[0][0]
        top_has_concept = deduped[0][1] > 0

        # Relative adaptive evidence selection:
        # Answerability check: if top_score is extremely weak and no content words matched, return empty
        if top_score < 0.25 and not top_has_concept:
            return []

        filtered_results = []
        for s, concept_matches, cite in deduped[:top_k]:
            if top_has_concept and concept_matches == 0:
                continue
            # Keep top candidate if it meets the baseline answerability
            if not filtered_results:
                if s >= 0.25 or top_has_concept:
                    filtered_results.append(cite)
                continue
            # Keep secondary candidates only if they genuinely support the topic and are close to top_score
            if top_score >= 0.65:
                if s >= max(0.40, top_score - 0.15):
                    filtered_results.append(cite)
            else:
                if s >= max(0.28, top_score - 0.10):
                    filtered_results.append(cite)

        return filtered_results
