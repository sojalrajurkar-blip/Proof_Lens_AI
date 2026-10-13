"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  FileText,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  Loader2,
  ExternalLink,
  Percent,
} from "lucide-react";
import { PassageDetail, ValidatedCitation } from "../lib/types";
import { api } from "../lib/api";

interface PassageModalProps {
  isOpen: boolean;
  onClose: () => void;
  workspaceId: string;
  citation: ValidatedCitation | null;
}

export const PassageModal: React.FC<PassageModalProps> = ({
  isOpen,
  onClose,
  workspaceId,
  citation,
}) => {
  const [passage, setPassage] = useState<PassageDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [currentChunkId, setCurrentChunkId] = useState<string | null>(null);
  const [currentDocId, setCurrentDocId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && citation) {
      setCurrentChunkId(citation.chunk_id);
      setCurrentDocId(citation.document_id);
      fetchPassage(citation.document_id, citation.chunk_id);
    } else {
      setPassage(null);
      setError(null);
    }
  }, [isOpen, citation]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const fetchPassage = async (docId: string, chunkId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPassage(workspaceId, docId, chunkId);
      setPassage(data);
      setCurrentChunkId(chunkId);
      setCurrentDocId(docId);
    } catch (err: any) {
      setError(err?.message || "Failed to load verbatim passage.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!passage) return;
    try {
      await navigator.clipboard.writeText(passage.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="passage-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl rounded-2xl bg-[#0c1222] border border-white/15 shadow-2xl overflow-hidden flex flex-col max-h-[88vh] animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-5 border-b border-white/10 bg-slate-900/60 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="passage-modal-title" className="font-semibold text-slate-100 text-base">
                  Passage Provenance Inspector
                </h3>
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Verbatim Source
                </span>
              </div>
              <p className="text-xs text-slate-400 truncate max-w-md">
                {passage?.filename || citation?.filename || "Loading passage..."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              disabled={!passage || loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-white/10 transition-colors disabled:opacity-40"
              title="Copy Verbatim Passage"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  <span>Copy</span>
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Close passage modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Metadata Ribbon */}
        {passage && (
          <div className="px-5 py-2.5 bg-slate-900/40 border-b border-white/5 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
                Page {passage.page_number}
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-white/5 font-mono text-[11px]">
                Chunk #{passage.chunk_index}
              </span>
              <span className="text-slate-500">
                {passage.word_count} words • {passage.char_count} chars
              </span>
            </div>

            {citation && citation.similarity_score !== undefined && (
              <div className="flex items-center gap-2">
                <span className="text-slate-400 text-[11px]">Retrieval Similarity:</span>
                <span className="font-mono text-emerald-400 text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                  {(citation.similarity_score * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 font-sans text-sm text-slate-200 leading-relaxed space-y-4">
          {loading && (
            <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
              <p className="text-sm">Fetching verbatim chunk from database...</p>
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
              <p className="font-medium">Error loading passage:</p>
              <p className="text-xs text-rose-400 mt-1">{error}</p>
            </div>
          )}

          {!loading && !error && passage && (
            <div>
              <div className="text-[11px] font-semibold tracking-wider uppercase text-slate-400 mb-2">
                VERBATIM DOCUMENT TEXT
              </div>
              <div className="p-4 rounded-xl bg-[#080d1a] border border-white/10 font-mono text-xs text-slate-200 leading-6 whitespace-pre-wrap selection:bg-indigo-500/30 shadow-inner">
                {passage.content}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer / Adjacent Navigation */}
        <div className="p-4 border-t border-white/10 bg-slate-900/60 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (passage?.prev_chunk_id && currentDocId) {
                  fetchPassage(currentDocId, passage.prev_chunk_id);
                }
              }}
              disabled={!passage?.prev_chunk_id || loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous Chunk</span>
            </button>

            <button
              onClick={() => {
                if (passage?.next_chunk_id && currentDocId) {
                  fetchPassage(currentDocId, passage.next_chunk_id);
                }
              }}
              disabled={!passage?.next_chunk_id || loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <span>Next Chunk</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-white/10 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
