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

    CROSS_LINGUAL_SYNONYMS = {
        'कर्मचारी': ['employee', 'employees', 'staff', 'workforce'],
        'कर्मचारियों': ['employee', 'employees', 'staff', 'workforce'],
        'राजस्व': ['revenue', 'turnover', 'income', 'earnings'],
        'आय': ['revenue', 'income', 'earnings'],
        'स्थापना': ['established', 'founded'],
        'शुरुआत': ['started', 'introduced', 'began'],
        'ग्राहक': ['customer', 'client'],
        'ग्राहकों': ['customers', 'clients'],
        'उद्देश्य': ['objective', 'purpose', 'goal'],
        'पायलट': ['pilot'],
        'कंपनी': ['company', 'organization'],
        'नौकरी': ['job', 'employment'],
        'डेडलॉक': ['deadlock'],
        'डेडलाक': ['deadlock'],
        'कारण': ['cause', 'causes', 'reason', 'conditions'],
        'कारणों': ['cause', 'causes', 'reason', 'conditions']
    }

    def rerank(self, query: str, citations: List[Citation], top_k: int = 4) -> List[Citation]:
        if not citations:
            return []

        # 1. Extract query temporal & numerical constraints
        query_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', query))
        query_numbers = set(re.findall(r'\b\d+(?:[.,]\d+)?\b', query)) - query_years

        # 2. Extract content keywords from query
        raw_words = re.findall(r'[a-zA-Z0-9\u0900-\u097F]+', query.lower())
        query_keywords = [w for w in raw_words if len(w) > 2 and w not in self.STOPWORDS]

        scored_citations = []
        for c in citations:
            text = c.text_snippet
            score = float(c.similarity_score)
            text_lower = text.lower()

            # --- Signal 1: Question vs. Factual Evidence Analysis ---
            q_marks = text.count('?')
            sentences = [s.strip() for s in re.split(r'[.?!।\n]+', text) if s.strip()]
            num_sentences = max(1, len(sentences))

            if q_marks > 0:
                q_ratio = q_marks / num_sentences
                if q_ratio >= 0.4 or text.strip().endswith('?'):
                    # Strongly penalize chunks that are primarily question lists or questions
                    score -= 0.30
                else:
                    score -= 0.12 * q_ratio
            else:
                # Factual assertion bonus: contains numbers/quantities and no question marks
                if re.search(r'\b\d+\b', text):
                    score += 0.06

            # --- Signal 2: Temporal / Year Disambiguation ---
            chunk_years = set(re.findall(r'\b(19\d\d|20\d\d)\b', text))
            if query_years:
                matching_years = query_years.intersection(chunk_years)
                conflicting_years = chunk_years - query_years
                if matching_years:
                    score += 0.20 * len(matching_years)
                elif conflicting_years and not matching_years:
                    score -= 0.25

            # --- Signal 3: Lexical & Entity Overlap with Cross-Lingual Synonyms ---
            expanded_keywords = set(query_keywords)
            topic_concept_matches = 0
            for kw in query_keywords:
                if kw in self.CROSS_LINGUAL_SYNONYMS:
                    for syn in self.CROSS_LINGUAL_SYNONYMS[kw]:
                        expanded_keywords.add(syn)
                        if syn in text_lower:
                            topic_concept_matches += 1

            if expanded_keywords:
                matched_kw = sum(1 for kw in expanded_keywords if kw in text_lower)
                kw_ratio = matched_kw / len(expanded_keywords)
                score += 0.15 * kw_ratio
            if topic_concept_matches > 0:
                score += 0.20

            # Bound score to [0.0, 1.0] for clean reporting
            normalized_score = round(max(0.0, min(1.0, score)), 4)
            
            # Create a clone citation with updated score
            reranked_citation = Citation(
                document_id=c.document_id,
                filename=c.filename,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                text_snippet=c.text_snippet,
                similarity_score=normalized_score
            )
            scored_citations.append((score, reranked_citation))

        # Sort descending by calculated score
        scored_citations.sort(key=lambda x: x[0], reverse=True)

        # Return top_k citations
        result = [c for _, c in scored_citations[:top_k]]
        return result
