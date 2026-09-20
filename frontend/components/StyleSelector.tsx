'use client';

import React from 'react';
import { ResponseStyle } from '@/types';
import { SlidersHorizontal } from 'lucide-react';

interface StyleSelectorProps {
  value: ResponseStyle;
  onChange: (val: ResponseStyle) => void;
}

export const StyleSelector: React.FC<StyleSelectorProps> = ({ value, onChange }) => {
  const options: { label: string; value: ResponseStyle; hint: string }[] = [
    { label: 'Explain', value: 'explain', hint: 'Clear, well-structured explanation with full context' },
    { label: 'Briefly', value: 'briefly', hint: 'Concise, essential facts only (1-2 sentences)' },
    { label: 'Give Me Points', value: 'points', hint: 'Clean bullet points, one idea per point' },
  ];

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center gap-1 text-[11px] font-medium text-stone-500 dark:text-stone-400">
        <SlidersHorizontal className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
        <span className="hidden sm:inline">Style:</span>
      </div>
      <div className="inline-flex rounded-full border border-stone-200/80 dark:border-stone-800 bg-stone-100/80 dark:bg-stone-900 p-0.5 text-xs">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium transition-all ${
              value === opt.value
                ? 'bg-amber-400 dark:bg-amber-500 text-stone-950 font-bold shadow-xs'
                : 'text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200'
            }`}
            title={opt.hint}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
};
