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
    <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
        <BookOpen className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
        <span>Retrieved Sources ({citations.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {citations.map((cite, idx) => {
          const isExpanded = expandedIndex === idx;
          const pct = Math.round(cite.similarity_score * 100);

          return (
            <div
              key={`${cite.document_id}_${cite.chunk_index}_${idx}`}
              className="border border-slate-200/80 dark:border-slate-800 rounded-lg p-2.5 bg-slate-50/50 dark:bg-slate-900/60 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all text-xs"
            >
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
              >
                <div className="flex items-center gap-2 min-w-0 pr-1">
                  <FileText className="w-3.5 h-3.5 text-blue-500 dark:text-blue-400 shrink-0" />
                  <span className="font-medium text-slate-800 dark:text-slate-200 truncate" title={cite.filename}>
                    {cite.filename}
                  </span>
                  <span className="text-[10px] bg-blue-100/80 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded font-medium shrink-0">
                    Page {cite.page_number}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500" title="Cosine Similarity Score">
                    {pct}% match
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                  )}
                </div>
              </div>

              {isExpanded && (
                <div className="mt-2 pt-2 border-t border-slate-200/60 dark:border-slate-800 text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed font-normal bg-white dark:bg-slate-950 p-2 rounded border border-slate-100 dark:border-slate-800/80">
                  <div className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 mb-1">
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
