'use client';

import React, { useState } from 'react';
import { Citation } from '@/types';
import { BookOpen, ChevronDown, ChevronUp, FileText } from 'lucide-react';

interface CitationsListProps {
  citations: Citation[];
}

export const CitationsList: React.FC<CitationsListProps> = ({ citations }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-100">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-2">
        <BookOpen className="w-3.5 h-3.5 text-blue-600" />
        <span>Retrieved Sources ({citations.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {citations.map((cite, idx) => {
          const isExpanded = expandedIndex === idx;
          const pct = Math.round(cite.similarity_score * 100);

          return (
            <div
              key={`${cite.document_id}_${cite.chunk_index}_${idx}`}
              className="border border-slate-200/80 rounded-lg p-2.5 bg-slate-50/50 hover:bg-slate-50 transition-all text-xs"
            >
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
              >
                <div className="flex items-center gap-2 min-w-0 pr-1">
                  <FileText className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                  <span className="font-medium text-slate-800 truncate" title={cite.filename}>
                    {cite.filename}
                  </span>
                  <span className="text-[10px] bg-blue-100/80 text-blue-700 px-1.5 py-0.5 rounded font-medium shrink-0">
                    Page {cite.page_number}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="text-[10px] font-mono text-slate-400" title="Cosine Similarity Score">
                    {pct}% match
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <div className="mt-2 pt-2 border-t border-slate-200/60 text-slate-600 text-[11px] leading-relaxed font-normal bg-white p-2 rounded border border-slate-100">
                  <div className="text-[10px] uppercase font-semibold text-slate-400 mb-1">
                    Retrieved Text Chunk (Index #{cite.chunk_index})
                  </div>
                  <p className="whitespace-pre-wrap">{cite.text_snippet}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
