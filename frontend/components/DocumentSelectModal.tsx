'use client';

import React, { useRef, useState } from 'react';
import { DocumentMetadata } from '@/types';
import { 
  FileText, 
  Layers, 
  UploadCloud, 
  Loader2, 
  X, 
  Check, 
  ArrowRight,
  BookOpen
} from 'lucide-react';

interface DocumentSelectModalProps {
  isOpen: boolean;
  onClose: () => void;
  documents: DocumentMetadata[];
  onSelectDocument: (docId: string | null) => void;
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

export const DocumentSelectModal: React.FC<DocumentSelectModalProps> = ({
  isOpen,
  onClose,
  documents,
  onSelectDocument,
  onUpload,
  isUploading,
}) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await onUpload(e.target.files[0]);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await onUpload(e.dataTransfer.files[0]);
    }
  };

  const handleConfirm = (docId: string | null) => {
    onSelectDocument(docId);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg rounded-2xl bg-[#fffdfa] dark:bg-[#191614] border border-amber-200/80 dark:border-stone-800 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-5 border-b border-stone-200/70 dark:border-stone-800 flex items-start justify-between bg-white/70 dark:bg-stone-900/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 flex items-center justify-center shrink-0">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-stone-900 dark:text-stone-100 leading-snug">
                Select a document to start chatting
              </h2>
              <p className="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                Choose a document from your workspace to focus this conversation.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
            title="Cancel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {documents.length === 0 ? (
            /* Empty State: No Documents Uploaded */
            <div className="text-center py-6 px-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto mb-3 border border-amber-200/60 dark:border-amber-800/40">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-stone-800 dark:text-stone-200">
                No documents available
              </h3>
              <p className="text-xs text-stone-500 dark:text-stone-400 mt-1 max-w-xs mx-auto mb-5 leading-relaxed">
                Upload a PDF or DOCX to start chatting with DOC-Lingo.
              </p>

              {/* Upload Dropzone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                  isDragging 
                    ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/30 scale-[0.99]' 
                    : 'border-amber-300/80 dark:border-stone-700 bg-white dark:bg-stone-900 hover:border-amber-500 hover:bg-amber-50/40'
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
                  <div className="flex flex-col items-center gap-2">
                    <Loader2 className="w-6 h-6 text-amber-500 animate-spin" />
                    <span className="text-xs font-semibold text-stone-700 dark:text-stone-200">
                      Indexing Document...
                    </span>
                    <span className="text-[11px] text-stone-400">Embedding vectors into your isolated workspace</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-10 h-10 rounded-full bg-amber-100/70 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                      <UploadCloud className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-stone-800 dark:text-stone-200">
                        Click or drag document to upload
                      </p>
                      <p className="text-[11px] text-stone-400 mt-0.5">Supports PDF and DOCX files</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Document List Available for Selection */
            <div className="space-y-2">
              <div className="text-[11px] font-semibold text-stone-400 dark:text-stone-500 uppercase tracking-wider px-1">
                Your Workspace Documents ({documents.length})
              </div>

              {/* Option: All Documents */}
              <div
                onClick={() => handleConfirm(null)}
                className="group p-3 rounded-xl border border-stone-200/80 dark:border-stone-800 hover:border-amber-400 hover:bg-amber-50/50 dark:hover:bg-amber-950/20 bg-white dark:bg-stone-900 cursor-pointer transition-all flex items-center justify-between"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="w-8 h-8 rounded-lg bg-amber-100/80 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 flex items-center justify-center shrink-0">
                    <Layers className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-xs font-semibold text-stone-900 dark:text-stone-100 truncate">
                      All Documents
                    </h4>
                    <p className="text-[11px] text-stone-400 mt-0.5 truncate">
                      Search across all {documents.length} indexed files in your library
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  className="px-3 py-1 rounded-full text-xs font-semibold bg-stone-100 group-hover:bg-amber-400 group-hover:text-stone-950 text-stone-700 dark:bg-stone-800 dark:text-stone-200 dark:group-hover:bg-amber-400 dark:group-hover:text-stone-950 transition-colors shrink-0 flex items-center gap-1"
                >
                  <span>Select</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              {/* Individual Document Items */}
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  onClick={() => handleConfirm(doc.document_id)}
                  className="group p-3 rounded-xl border border-stone-200/80 dark:border-stone-800 hover:border-amber-400 hover:bg-amber-50/50 dark:hover:bg-amber-950/20 bg-white dark:bg-stone-900 cursor-pointer transition-all flex items-center justify-between"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1 pr-3">
                    <div className="w-8 h-8 rounded-lg bg-stone-100 dark:bg-stone-800 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 group-hover:bg-amber-100/80 dark:group-hover:bg-amber-950/60 transition-colors">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h4 className="text-xs font-semibold text-stone-900 dark:text-stone-100 truncate">
                        {doc.filename}
                      </h4>
                      <p className="text-[11px] text-stone-400 mt-0.5 flex items-center gap-1.5">
                        <span>{doc.page_count} page{doc.page_count > 1 ? 's' : ''}</span>
                        <span>•</span>
                        <span>{doc.chunk_count} chunks indexed</span>
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="px-3 py-1 rounded-full text-xs font-semibold bg-stone-100 group-hover:bg-amber-400 group-hover:text-stone-950 text-stone-700 dark:bg-stone-800 dark:text-stone-200 dark:group-hover:bg-amber-400 dark:group-hover:text-stone-950 transition-colors shrink-0 flex items-center gap-1"
                  >
                    <span>Start Chat</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-stone-200/70 dark:border-stone-800 bg-white/50 dark:bg-stone-900/50 flex items-center justify-between text-xs">
          <span className="text-[11px] text-stone-400 dark:text-stone-500">
            {documents.length > 0
              ? 'Click any document above to begin chatting.'
              : 'Uploaded files remain completely isolated to your account.'}
          </span>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded-full text-xs text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
