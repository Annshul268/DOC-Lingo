'use client';

import React from 'react';
import { Language } from '@/types';
import { Globe } from 'lucide-react';

interface LanguageSelectorProps {
  value: Language;
  onChange: (val: Language) => void;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ value, onChange }) => {
  const options: { label: string; value: Language; hint: string }[] = [
    { label: 'Auto Detect', value: 'auto', hint: 'Infers query language' },
    { label: 'English', value: 'en', hint: 'Natural English' },
    { label: 'Hindi (हिन्दी)', value: 'hi', hint: 'Devanagari script' },
    { label: 'Hinglish', value: 'hinglish', hint: 'Hindi in Roman script' },
  ];

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center gap-1 text-[11px] font-medium text-stone-500 dark:text-stone-400">
        <Globe className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        <span className="hidden sm:inline">Answer:</span>
      </div>
      <div className="inline-flex rounded-full border border-stone-200/80 dark:border-stone-800 bg-stone-100/70 dark:bg-stone-900 p-0.5 text-xs">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium transition-all ${
              value === opt.value
                ? 'bg-white dark:bg-stone-800 text-emerald-700 dark:text-emerald-300 shadow-xs font-semibold'
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
