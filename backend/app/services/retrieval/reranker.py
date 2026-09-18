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
        'kya', 'hai', 'hain', 'tha', 'thi', 'the', 'ka', 'ki', 'ke', 'ko', 'me', 'mein',
        'se', 'par', 'aur', 'ya', 'kitna', 'kitne', 'kitni', 'kab', 'kahan', 'kaise',
        'tak', 'ek', 'bhi', 'kisi', 'kisko', 'iska', 'iski', 'iske'
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
        'कुंजी': ['key']
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

    def _extract_focused_excerpt(self, text: str, content_words: set, query_years: set) -> str:
        """Extracts the specific paragraph or sentence that actually contains the factual evidence."""
        # Split text into paragraphs or distinct bullet/field lines
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\n(?=[A-Z][a-zA-Z\s]+:)', text) if p.strip()]
        if not paragraphs or len(paragraphs) == 1:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

        if not paragraphs:
            return text.strip()

        scored_paragraphs = []
        for p in paragraphs:
            p_lower = p.lower()
            score = 0
            for w in content_words:
                if re.search(r'\b' + re.escape(w) + r'\b', p_lower):
                    score += 2.0
            for y in query_years:
                if y in p:
                    score += 3.0
            if re.search(r'\b\d+\b', p):
                score += 0.5
            # Penalize question sentences
            if p.strip().endswith('?') or p.count('?') > 0:
                score -= 4.0
            scored_paragraphs.append((score, p))

        scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
        if scored_paragraphs and scored_paragraphs[0][0] > 0:
            best_p = scored_paragraphs[0][1]
            # Strip footer artifacts e.g. "DOC-Lingo Test Document • Page 2"
            best_p = re.sub(r'\s*DOC-Lingo Test Document\s*•\s*Page\s*\d+', '', best_p, flags=re.IGNORECASE)
            return best_p.strip()

        return text.strip()

    def rerank(self, query: str, citations: List[Citation], top_k: int = 4) -> List[Citation]:
        if not citations:
            return []

        from backend.app.services.language.translator import devanagari_to_roman

        # 1. Extract query temporal constraints
        query_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', query))

        # 2. Extract content keywords and expand cross-lingually (excluding query years)
        raw_words = re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', query.lower())
        query_keywords = [w for w in raw_words if len(w) > 2 and w not in self.STOPWORDS and w not in query_years]

        expanded_keywords = set()
        for kw in query_keywords:
            expanded_keywords.add(kw)
            roman = devanagari_to_roman(kw).lower()
            if roman and len(roman) > 2:
                expanded_keywords.add(roman)
            if kw in self.CROSS_LINGUAL_SYNONYMS:
                expanded_keywords.update(self.CROSS_LINGUAL_SYNONYMS[kw])
            if roman in self.CROSS_LINGUAL_SYNONYMS:
                expanded_keywords.update(self.CROSS_LINGUAL_SYNONYMS[roman])

        content_query_words = {w for w in expanded_keywords if w not in self.GENERIC_WORDS and len(w) > 2}

        scored_citations = []
        for c in citations:
            text = c.text_snippet
            # Normalize currency font artifacts (e.g. 'I84 crore' -> '₹84 crore')
            text = re.sub(r'(?<=\s)[I■](?=\d+\s*(?:crore|lakh|thousand|million|billion|\b))', '₹', text)
            text_lower = text.lower()
            score = float(c.similarity_score)

            # --- Signal 1: Question vs. Factual Evidence Analysis ---
            q_marks = text.count('?')
            sentences = [s.strip() for s in re.split(r'[.?!।\n]+', text) if s.strip()]
            num_sentences = max(1, len(sentences))

            # If the chunk is primarily questions or an exercise/sample question list, it cannot be supporting evidence
            if q_marks > 0 and (q_marks / num_sentences >= 0.35 or text.strip().endswith('?')):
                continue

            if re.search(r'\b\d+\b', text):
                score += 0.06

            # --- Signal 2: Temporal / Year Disambiguation ---
            chunk_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', text))
            if query_years:
                matching_years = query_years.intersection(chunk_years)
                conflicting_years = chunk_years - query_years
                if conflicting_years and not matching_years:
                    # Conflicting year (e.g. query asks for 2026, chunk has only 2025) -> Reject as evidence
                    continue
                if matching_years:
                    score += 0.25

            # --- Signal 3: Lexical & Entity Overlap with Cross-Lingual Synonyms ---
            matched_content_words = {w for w in content_query_words if w in text_lower}
            topic_concept_matches = sum(
                1 for kw in content_query_words if any(syn in text_lower for syn in self.CROSS_LINGUAL_SYNONYMS.get(kw, []))
            )

            # If query has specific content keywords, chunk MUST match at least one to be supporting evidence
            if content_query_words and not matched_content_words:
                continue

            if content_query_words:
                kw_ratio = len(matched_content_words) / len(content_query_words)
                score += 0.25 * kw_ratio
            if topic_concept_matches > 0:
                score += 0.25

            # Extract the focused supporting excerpt
            focused_snippet = self._extract_focused_excerpt(text, content_query_words, query_years)

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

        # Adaptive evidence selection:
        # If top chunk has a specific topic concept match (e.g. employee or revenue),
        # only retain chunks that ALSO match that concept!
        filtered_results = []
        for s, concept_matches, cite in deduped[:top_k]:
            if top_has_concept and concept_matches == 0:
                continue
            if top_score >= 0.70:
                if s >= max(0.45, top_score - 0.15):
                    filtered_results.append(cite)
            else:
                if s >= 0.35:
                    filtered_results.append(cite)

        return filtered_results
