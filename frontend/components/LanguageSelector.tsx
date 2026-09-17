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
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
        <Globe className="w-3.5 h-3.5 text-slate-400" />
        <span>Answer Language:</span>
      </div>
      <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50/80 p-0.5 text-xs">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
              value === opt.value
                ? 'bg-white text-blue-600 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
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
