import re
import logging
from typing import List, Set
from backend.app.schemas.chat import Citation
from backend.app.services.retrieval.query_intent import analyze_query, IntentType

logger = logging.getLogger(__name__)

class GenericRAGReranker:
    """
    Production-grade, generic reranker and evidence filter for multilingual RAG.
    
    Dynamically aligns:
    1. Query Intent: Distinguishes between types/lists, definitions, functions, processes, and comparisons.
    2. Subject Entity Match: Boosts chunks containing the subject keywords and their cross-lingual synonyms.
    3. Structural Quality: Preserves complete headings, lists, and explanations while filtering out question banks.
    4. Temporal Consistency: Disambiguates specific years and penalizes conflicting dates.
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
        'kaun', 'kaunsa', 'kaunsi', 'kaunse', 'diya', 'diye', 'gaya', 'gayi', 'gaye',
        'hua', 'hue', 'hui'
    }

    COMMON_ACRONYMS = {
        'os': ['operating', 'system', 'systems'],
        'ai': ['artificial', 'intelligence'],
        'ui': ['user', 'interface'],
        'db': ['database', 'databases'],
        'dbms': ['database', 'management', 'system'],
        'sql': ['structured', 'query', 'language'],
        'fs': ['file', 'system', 'systems'],
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
        'शुरुआत': ['start', 'started', 'starts', 'introduced', 'introduce', 'began', 'launch', 'launched', 'shuru', 'shuruat'],
        'start': ['started', 'starts', 'introduced', 'introduce', 'began', 'launch', 'launched', 'shuru', 'shuruat', 'शुरुआत'],
        'shuru': ['start', 'started', 'starts', 'introduced', 'introduce', 'began', 'launch', 'launched', 'shuruat', 'शुरुआत'],
        'ग्राहक': ['customer', 'client'],
        'ग्राहकों': ['customers', 'clients'],
        'उद्देश्य': ['objective', 'purpose', 'goal'],
        'पायलट': ['pilot'],
        'नौकरी': ['job', 'employment'],
        'डेडलॉक': ['deadlock'],
        'कारण': ['cause', 'causes', 'reason', 'conditions'],
        'प्राथमिक': ['primary'],
        'कुंजी': ['key', 'keys'],
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
        'कर्नेल': ['kernel'],
        'प्रकार': ['type', 'types', 'kinds', 'categories', 'classification'],
        'वर्गीकरण': ['classification', 'types', 'categories'],
        'कार्य': ['function', 'functions', 'role', 'roles', 'responsibilities']
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
        'tell', 'show', 'give', 'explain', 'describe', 'about', 'this', 'that', 'with'
    }

    EXPLANATORY_PREDICATES = {
        'tracks', 'track', 'allocates', 'allocate', 'manages', 'manage', 'allows', 'allow',
        'provides', 'provide', 'creates', 'create', 'divides', 'divide', 'operates', 'operate',
        'controls', 'control', 'uses', 'use', 'performs', 'perform', 'works', 'work',
        'assigns', 'assign', 'defined', 'refers', 'acts', 'is', 'are', 'was', 'were',
        'had', 'has', 'have', 'stores', 'store', 'organizes', 'organize',
        'karta', 'karti', 'karte', 'hota', 'hoti', 'hote', 'diya', 'kiya'
    }

    LIST_MARKERS = [
        'include', 'includes', 'examples include', 'approaches include', 'types include', 'such as'
    ]

    def rerank(self, query: str, citations: List[Citation], top_k: int = 4) -> List[Citation]:
        if not citations:
            return []

        from backend.app.services.language.translator import devanagari_to_roman

        # 1. Structural query analysis
        analysis = analyze_query(query, stopwords=self.STOPWORDS)
        intent = analysis.intent
        query_years = analysis.query_years
        raw_subject_words = analysis.subject_words

        # 2. Expand subject words cross-lingually
        expanded_subject_words = set()
        for w in raw_subject_words:
            if w not in self.GENERIC_WORDS and len(w) > 1:
                expanded_subject_words.add(w)
                if w in self.COMMON_ACRONYMS:
                    expanded_subject_words.update(self.COMMON_ACRONYMS[w])
                roman = devanagari_to_roman(w).lower()
                if roman and (len(roman) > 2 or roman in self.COMMON_ACRONYMS):
                    expanded_subject_words.add(roman)
                    if roman in self.COMMON_ACRONYMS:
                        expanded_subject_words.update(self.COMMON_ACRONYMS[roman])
                if w in self.CROSS_LINGUAL_SYNONYMS:
                    expanded_subject_words.update(self.CROSS_LINGUAL_SYNONYMS[w])
                if roman in self.CROSS_LINGUAL_SYNONYMS:
                    expanded_subject_words.update(self.CROSS_LINGUAL_SYNONYMS[roman])

        scored_citations = []
        for c in citations:
            text = c.text_snippet
            # Normalize currency font artifacts (e.g. 'I84 crore' -> '₹84 crore')
            text = re.sub(r'(?<=\s)[I■](?=\d+\s*(?:crore|lakh|thousand|million|billion|\b))', '₹', text)
            # Normalize font glyph artifacts (e.g. 'Systems ? Test' -> 'Systems - Test')
            text = re.sub(r'(?<=[a-zA-Z0-9])\s+\?\s+(?=[a-zA-Z0-9])', ' - ', text)
            text_lower = text.lower()
            sec_heading = (c.section_heading or "").lower()
            score = float(c.similarity_score)

            # --- Signal 1: Filter out test prompt / question-only chunks ---
            if any(h in sec_heading for h in ['suggested test questions', 'test questions', 'suggested questions', 'questions for testing', 'sample questions', 'practice questions', 'exercises']):
                continue
            if any(k in text_lower for k in ['suggested questions', 'questions for testing', 'test questions', 'practice questions']) and text.count('?') >= 2:
                continue

            # Detect chunks that are exclusively lists of questions (no explanatory paragraphs)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            has_substantive_body = any(len(p) > 140 and not p.endswith('?') for p in paragraphs)
            if not has_substantive_body:
                q_lines = [l for l in lines if l.endswith('?') or re.match(r'^(?:\d+[\.\)]|[-*•])\s+.*\?', l)]
                if len(q_lines) >= 3 and len(q_lines) / max(1, len(lines)) >= 0.5:
                    continue

            # --- Signal 2: Temporal alignment & conflict ---
            chunk_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', text))
            if query_years:
                matching_years = query_years.intersection(chunk_years)
                conflicting_years = chunk_years - query_years
                if conflicting_years and not matching_years:
                    continue  # Incompatible year (e.g. asking for 2026 when chunk only has 2025)
                if not chunk_years and not matching_years:
                    score -= 0.35
                if matching_years:
                    score += 0.35

            # --- Signal 3: Subject entity coverage ---
            # Calculate what fraction of query subject terms are covered by this chunk
            query_terms = [w for w in analysis.subject_words if len(w) > 2]
            matched_terms_count = 0
            for term in query_terms:
                term_variants = {term}
                if term in self.COMMON_ACRONYMS:
                    term_variants.update(self.COMMON_ACRONYMS[term])
                if term in self.CROSS_LINGUAL_SYNONYMS:
                    term_variants.update(self.CROSS_LINGUAL_SYNONYMS[term])
                roman = devanagari_to_roman(term).lower()
                if roman:
                    term_variants.add(roman)
                    if roman in self.CROSS_LINGUAL_SYNONYMS:
                        term_variants.update(self.CROSS_LINGUAL_SYNONYMS[roman])
                if any(re.search(r'\b' + re.escape(v) + r'\b', text_lower) or re.search(r'\b' + re.escape(v) + r'\b', sec_heading) for v in term_variants):
                    matched_terms_count += 1

            term_coverage = matched_terms_count / max(1, len(query_terms)) if query_terms else 1.0
            has_subject_match = (matched_terms_count > 0) or (len(query_terms) == 0)

            if query_terms and not has_subject_match:
                score -= 0.40
            elif query_terms:
                if term_coverage >= 0.70:
                    score += 0.35
                elif term_coverage < 0.35 and len(query_terms) >= 3:
                    score -= 0.30

            if sec_heading and query_terms:
                heading_overlap = sum(1 for w in query_terms if w in sec_heading)
                if heading_overlap > 0:
                    score += (heading_overlap / len(query_terms)) * 0.30
            elif sec_heading and any(w in sec_heading for w in expanded_subject_words):
                score += 0.15

            # Quantitative query boost (e.g. asking "how many" or "kitne")
            is_quant_query = any(q_w in query.lower() for q_w in ['kitne', 'kitna', 'kitni', 'how many', 'how much', 'amount', 'count'])
            if is_quant_query and re.search(r'\b\d+\b', text):
                score += 0.25

            # --- Signal 4: Intent Alignment ---
            if intent == IntentType.TYPES_LIST:
                is_type_sec = any(w in sec_heading for w in ['type', 'types', 'kind', 'kinds', 'category', 'categories', 'classification', 'prakar', 'vargikaran'])
                has_type_heading = bool(re.search(r'(?i)\b(?:types?|kinds?|categories|classification|classes)\s+of\b', text))
                has_structured_list = bool(re.search(r'(?m)^(?:[-*•]|\d+[\.\)]|[A-Z][a-zA-Z\s]{2,35}:)\s+', text))
                is_pure_definition = bool(re.search(r'(?i)^[A-Za-z\s]+\s+is\s+(?:system\s+software|software|software\s+used|a\s+controlled)', text.strip()))

                if is_type_sec or has_type_heading:
                    score += 0.40
                if has_structured_list:
                    score += 0.20
                if is_pure_definition and not is_type_sec and not has_type_heading:
                    score -= 0.25

            elif intent == IntentType.EXAMPLES:
                has_examples = any(w in text_lower or w in sec_heading for w in [
                    'example', 'examples', 'common', 'popular', 'instance', 'instances',
                    'such as', 'for example', 'widely used', 'उदाहरण', 'misaal'
                ])
                if has_examples:
                    score += 0.35

            elif intent == IntentType.DEFINITION:
                has_def_structure = bool(re.search(r'(?i)\b(?:is\s+(?:a|an|the|system\s+software|software)|acts\s+as|refers\s+to|defined\s+as)\b', text))
                is_type_sec = bool(re.search(r'(?i)\b(?:types?\s+of|kinds?\s+of|categories\s+of)\b', text))
                if has_def_structure:
                    score += 0.30
                if is_type_sec and not has_def_structure:
                    score -= 0.20

            elif intent == IntentType.FUNCTION_ROLE:
                has_func = any(w in text_lower or w in sec_heading for w in [
                    'responsibility', 'responsibilities', 'function', 'functions', 'role', 'roles',
                    'manages', 'coordinates', 'provides', 'tracks', 'allocates', 'purpose', 'karya', 'kaam'
                ])
                if has_func:
                    score += 0.35

            elif intent == IntentType.PROCESS_HOW:
                has_process = any(w in text_lower or w in sec_heading for w in [
                    'scheduling', 'quantum', 'algorithm', 'approach', 'steps', 'process',
                    'works', 'assigns', 'switching', 'kaise', 'prakriya'
                ])
                if has_process:
                    score += 0.35

            elif intent == IntentType.ADVANTAGES:
                if any(w in text_lower for w in ['advantage', 'advantages', 'benefit', 'benefits', 'merits', 'reduce', 'efficient', 'fayde', 'labh']):
                    score += 0.35

            elif intent == IntentType.DISADVANTAGES:
                if any(w in text_lower for w in ['disadvantage', 'disadvantages', 'limitation', 'limitations', 'drawback', 'drawbacks', 'demerits', 'nuksan']):
                    score += 0.35

            # Clean inline glyph artifacts without destructive paragraph truncation
            cleaned_text = re.sub(r'(?<=\w)\s+[?•—–-]\s+(?=\w)', ' - ', text)
            cleaned_text = re.sub(r'(?m)^[A-Za-z0-9\s—–•?]+\s*[—–•?]\s*Page\s*\d+\s*$', '', cleaned_text).strip()
            cleaned_text = re.sub(r'(?m)^Page\s*\d+\s*[—–•?].*$', '', cleaned_text).strip()

            normalized_score = round(max(0.0, min(1.0, score)), 4)
            scored_citations.append((
                score,
                has_subject_match,
                Citation(
                    document_id=c.document_id,
                    filename=c.filename,
                    page_number=c.page_number,
                    chunk_index=c.chunk_index,
                    text_snippet=cleaned_text,
                    similarity_score=normalized_score,
                    section_heading=c.section_heading
                )
            ))

        # Sort descending by calculated score
        scored_citations.sort(key=lambda x: x[0], reverse=True)

        if not scored_citations:
            return []

        top_score, top_has_subject, top_cite = scored_citations[0]

        # Answerability check: if top score is very weak and query had subjects with zero matches
        if top_score < 0.25 and not top_has_subject:
            return []

        # Deduplicate and filter final candidates
        deduped = []
        seen_keys = set()
        for s, has_subj, cite in scored_citations:
            norm_key = (cite.filename, cite.page_number, cite.chunk_index)
            if norm_key not in seen_keys:
                seen_keys.add(norm_key)
                deduped.append((s, has_subj, cite))

        # Select evidence within adaptive range of top candidate
        filtered_results = []
        for s, has_subj, cite in deduped[:top_k]:
            if not filtered_results:
                if s >= 0.25 or top_has_subject:
                    filtered_results.append(cite)
                continue

            # Keep secondary chunks if they are strongly related to top evidence
            if top_score >= 0.60:
                if s >= max(0.35, top_score - 0.25):
                    filtered_results.append(cite)
            else:
                if s >= max(0.28, top_score - 0.15):
                    filtered_results.append(cite)

        return filtered_results
