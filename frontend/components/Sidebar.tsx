'use client';

import React, { useRef, useState } from 'react';
import { DocumentMetadata } from '@/types';
import { formatFileSize } from '@/lib/utils';
import { 
  FileText, 
  UploadCloud, 
  Trash2, 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  Layers,
  Sparkles
} from 'lucide-react';

interface SidebarProps {
  documents: DocumentMetadata[];
  selectedDocId: string | null;
  onSelectDoc: (id: string | null) => void;
  onUpload: (file: File) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  isUploading: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onUpload,
  onDelete,
  isUploading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <aside className="w-80 border-r border-slate-200/80 bg-slate-50/50 flex flex-col h-screen shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200/80 bg-white">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-900 leading-tight">DOC-Lingo</h1>
            <p className="text-xs text-slate-500 font-medium">Multilingual Document RAG</p>
          </div>
        </div>
      </div>

      {/* Upload Dropzone */}
      <div className="p-4">
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all ${
            isDragging 
              ? 'border-blue-500 bg-blue-50/50 scale-[0.99]' 
              : 'border-slate-200 bg-white hover:border-blue-400 hover:bg-slate-50/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          {isUploading ? (
            <div className="flex flex-col items-center gap-2 py-2">
              <Loader2 className="w-7 h-7 text-blue-600 animate-spin" />
              <div className="text-xs font-semibold text-slate-700">Processing & Indexing...</div>
              <div className="text-[11px] text-slate-400">Embedding multilingual vectors</div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1.5 py-1">
              <div className="w-9 h-9 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
                <UploadCloud className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-slate-700">Drop PDF or DOCX here</p>
              <p className="text-[11px] text-slate-400">or click to browse from device</p>
            </div>
          )}
        </div>
      </div>

      {/* Document Filter Options */}
      <div className="px-4 pb-2 flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
        <span>Knowledge Base</span>
        <span>{documents.length} files</span>
      </div>

      {/* All Documents Button */}
      <div className="px-3 pb-2">
        <button
          onClick={() => onSelectDoc(null)}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            selectedDocId === null
              ? 'bg-blue-50 text-blue-700 font-semibold shadow-xs'
              : 'text-slate-600 hover:bg-slate-100/80'
          }`}
        >
          <Layers className="w-4 h-4 text-blue-500" />
          <span>All Documents (Cross-Doc Search)</span>
        </button>
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto px-3 space-y-1">
        {documents.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">
            No documents uploaded yet.<br/>Upload an English or Hindi document to test cross-lingual retrieval.
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocId === doc.document_id;
            return (
              <div
                key={doc.document_id}
                onClick={() => onSelectDoc(doc.document_id)}
                className={`group flex items-start justify-between p-2.5 rounded-lg text-xs cursor-pointer border transition-all ${
                  isSelected
                    ? 'border-blue-200 bg-white shadow-xs'
                    : 'border-transparent hover:border-slate-200/60 hover:bg-white'
                }`}
              >
                <div className="flex items-start gap-2.5 min-w-0 pr-1">
                  <FileText className={`w-4 h-4 mt-0.5 shrink-0 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                  <div className="min-w-0">
                    <p className={`truncate font-medium ${isSelected ? 'text-blue-950 font-semibold' : 'text-slate-700'}`}>
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400 mt-0.5">
                      <span>{doc.page_count} pg{doc.page_count > 1 ? 's' : ''}</span>
                      <span>•</span>
                      <span>{doc.chunk_count} chunks</span>
                      <span>•</span>
                      <span className="uppercase text-[10px] bg-slate-100 text-slate-600 px-1 py-0.2 rounded">
                        {doc.language || doc.file_type}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  {doc.status === 'indexed' && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  )}
                  {doc.status === 'error' && (
                    <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(doc.document_id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-opacity"
                    title="Delete document"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-200/80 bg-white text-[11px] text-slate-500 flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Vector Store Active
        </span>
        <span className="text-slate-400 font-mono text-[10px]">ChromaDB</span>
      </div>
    </aside>
  );
};
