'use client';

import React, { useState } from 'react';
import { Citation } from '@/types';
import { ChevronRight, ChevronDown, FileText } from 'lucide-react';

interface CitationsListProps {
  citations: Citation[];
}

export const CitationsList: React.FC<CitationsListProps> = ({ citations }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!citations || citations.length === 0) return null;

  // 1. Calculate dynamic reference count and page range
  const validPages = citations
    .map((c) => c.page_number)
    .filter((p): p is number => typeof p === 'number' && p > 0);
  const uniquePages = Array.from(new Set(validPages)).sort((a, b) => a - b);

  let pageRangeText = '';
  if (uniquePages.length === 1) {
    pageRangeText = `Page ${uniquePages[0]}`;
  } else if (uniquePages.length > 1) {
    const minPage = uniquePages[0];
    const maxPage = uniquePages[uniquePages.length - 1];
    if (maxPage - minPage + 1 === uniquePages.length) {
      pageRangeText = `Pages ${minPage}–${maxPage}`;
    } else {
      pageRangeText = `Pages ${uniquePages.join(', ')}`;
    }
  }

  // Header summary:
  // If 1 source: "Source · Page 2"
  // If multiple: "Sources · 2 references · Pages 2–3"
  let headerSummary = '';
  if (citations.length === 1) {
    headerSummary = `Source · Page ${citations[0].page_number}`;
  } else {
    headerSummary = [
      'Sources',
      `${citations.length} references`,
      pageRangeText
    ].filter(Boolean).join(' · ');
  }

  // 2. Group citations by document (filename) so filename is displayed ONLY ONCE
  const groupedByDoc = citations.reduce<
    Record<string, { filename: string; items: Citation[] }>
  >((acc, cite) => {
    const key = cite.filename || cite.document_id;
    if (!acc[key]) {
      acc[key] = {
        filename: cite.filename,
        items: [],
      };
    }
    acc[key].items.push(cite);
    return acc;
  }, {});

  const docGroups = Object.values(groupedByDoc);

  return (
    <div className="mt-2 text-xs">
      {/* Clickable compact row (Collapsed by default) */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 py-1 px-1.5 -ml-1.5 rounded text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors cursor-pointer select-none group"
      >
        {isOpen ? (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200 transition-transform" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200 transition-transform" />
        )}
        <span className="font-medium text-[11px] tracking-tight">
          {headerSummary}
        </span>
      </button>

      {/* Expanded Sources Panel */}
      {isOpen && (
        <div className="mt-2.5 space-y-4 pl-1 animate-in fade-in slide-in-from-top-1 duration-200">
          {docGroups.map((group, groupIdx) => (
            <div key={groupIdx} className="space-y-2">
              {/* Document Filename - Displayed ONLY ONCE per document */}
              <div className="flex items-center gap-1.5 text-xs font-semibold text-stone-800 dark:text-stone-200">
                <FileText className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400 shrink-0" />
                <span className="truncate">{group.filename}</span>
              </div>

              {/* List of citations under this document */}
              <div className="space-y-3 pl-3.5 border-l-2 border-amber-300/80 dark:border-amber-700/60">
                {group.items.map((cite, citeIdx) => (
                  <div key={citeIdx} className="space-y-1">
                    {/* Page number */}
                    <div className="text-[11px] font-semibold text-amber-900 dark:text-amber-300">
                      Page {cite.page_number}
                    </div>

                    {/* Excerpt text */}
                    <div className="text-[11px] leading-relaxed text-stone-700 dark:text-stone-300 bg-amber-50/50 dark:bg-stone-900/80 p-2.5 rounded-xl border border-amber-200/60 dark:border-stone-800 whitespace-pre-wrap font-normal">
                      &quot;{cite.text_snippet.trim()}&quot;
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
