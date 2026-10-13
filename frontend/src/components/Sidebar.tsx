"use client";

import React, { useRef, useState } from "react";
import {
  FileText,
  UploadCloud,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileUp,
} from "lucide-react";
import { DocumentItem } from "../lib/types";

interface SidebarProps {
  documents: DocumentItem[];
  selectedDocIds: string[];
  onToggleDocSelection: (docId: string) => void;
  onSelectAllDocs: (selectAll: boolean) => void;
  onUploadFile: (file: File) => Promise<void>;
  onDeleteDocument: (docId: string) => Promise<void>;
  isUploading: boolean;
  uploadError: string | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocIds,
  onToggleDocSelection,
  onSelectAllDocs,
  onUploadFile,
  onDeleteDocument,
  isUploading,
  uploadError,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      await onUploadFile(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      await onUploadFile(file);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const allSelected = documents.length > 0 && selectedDocIds.length === documents.length;

  return (
    <aside className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-4 border-r border-white/10 bg-[#0c1220]/60 p-4">
      {/* Upload Box */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold tracking-wider uppercase text-slate-400">
            Document Ingestion
          </span>
          <span className="text-[11px] text-slate-400">Max 20MB (PDF)</span>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-xl p-4 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
            isDragOver
              ? "border-indigo-400 bg-indigo-500/10 scale-[1.01]"
              : "border-slate-700 hover:border-slate-500 bg-slate-900/40 hover:bg-slate-900/60"
          } ${isUploading ? "pointer-events-none opacity-60" : ""}`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf,application/pdf"
            className="hidden"
          />

          {isUploading ? (
            <div className="flex flex-col items-center gap-2 py-2">
              <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
              <p className="text-xs font-medium text-slate-300">
                Parsing pages & generating embeddings...
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1.5 py-1">
              <div className="w-10 h-10 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 mb-1">
                <UploadCloud className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-slate-200">
                Click or drag PDF here
              </p>
              <p className="text-[11px] text-slate-400">
                Extracts strict page-level provenance
              </p>
            </div>
          )}
        </div>

        {uploadError && (
          <div className="flex items-center gap-1.5 p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Documents Library Header */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <div className="flex items-center gap-2">
          <FileUp className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Workspace Library ({documents.length})
          </span>
        </div>

        {documents.length > 0 && (
          <button
            onClick={() => onSelectAllDocs(!allSelected)}
            className="text-[11px] text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            {allSelected ? "Deselect All" : "Select All"}
          </button>
        )}
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
        {documents.length === 0 ? (
          <div className="p-6 text-center rounded-xl bg-slate-900/30 border border-white/5 my-auto">
            <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs font-medium text-slate-400">No documents yet</p>
            <p className="text-[11px] text-slate-400 mt-1">
              Upload Assignment1.pdf or Assignment2.pdf to begin investigation.
            </p>
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                className={`p-3 rounded-xl border transition-all flex items-start gap-2.5 ${
                  isSelected
                    ? "bg-indigo-950/30 border-indigo-500/40 shadow-sm"
                    : "bg-slate-900/50 border-white/5 hover:border-white/15"
                }`}
              >
                <input
                  type="checkbox"
                  aria-label={`Select document ${doc.filename}`}
                  checked={isSelected}
                  onChange={() => onToggleDocSelection(doc.id)}
                  className="mt-1 w-3.5 h-3.5 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0 cursor-pointer"
                />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <p
                      className="text-xs font-semibold text-slate-200 truncate"
                      title={doc.filename}
                    >
                      {doc.filename}
                    </p>
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();
                        setDeletingId(doc.id);
                        await onDeleteDocument(doc.id);
                        setDeletingId(null);
                      }}
                      disabled={deletingId === doc.id}
                      className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                      title="Delete document"
                    >
                      {deletingId === doc.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      {doc.page_count} {doc.page_count === 1 ? "page" : "pages"}
                    </span>
                    <span>•</span>
                    <span>{formatBytes(doc.file_size_bytes)}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
