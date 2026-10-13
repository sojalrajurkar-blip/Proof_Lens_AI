"use client";

import React, { useState } from "react";
import {
  GitCompare,
  Loader2,
  FileText,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  Split,
  Equal,
  AlertTriangle,
} from "lucide-react";
import {
  DocumentItem,
  ComparisonResponse,
  ValidatedCitation,
} from "../lib/types";

interface ComparisonViewProps {
  documents: DocumentItem[];
  selectedDocIds: string[];
  onToggleDocSelection: (docId: string) => void;
  onCompareDocuments: (topic: string, docIds: string[]) => Promise<void>;
  comparisonResponse: ComparisonResponse | null;
  isLoading: boolean;
  error: string | null;
  onInspectCitation: (citation: ValidatedCitation) => void;
}

const SAMPLE_TOPICS = [
  "How does client-server communication and requests work across these documents?",
  "What are the diagnostic tools, terms, or practical tasks described?",
  "Compare how the documents describe medieval European history", // Abstention
];

export const ComparisonView: React.FC<ComparisonViewProps> = ({
  documents,
  selectedDocIds,
  onToggleDocSelection,
  onCompareDocuments,
  comparisonResponse,
  isLoading,
  error,
  onInspectCitation,
}) => {
  const [topic, setTopic] = useState("");

  const effectiveDocIds =
    selectedDocIds.length >= 2
      ? selectedDocIds
      : documents.slice(0, 2).map((d) => d.id);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || isLoading) return;
    if (effectiveDocIds.length < 2) return;
    await onCompareDocuments(topic, effectiveDocIds);
  };

  const getRelationshipBadge = (rel: string) => {
    switch (rel) {
      case "AGREEMENT":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <Equal className="w-3.5 h-3.5" />
            AGREEMENT (ALIGNED EVIDENCE)
          </span>
        );
      case "DIFFERENCE":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
            <Split className="w-3.5 h-3.5" />
            DIFFERENCE (DISTINCT SCOPES)
          </span>
        );
      case "CONTRADICTION":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <AlertCircle className="w-3.5 h-3.5" />
            CONTRADICTION DETECTED
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" />
            INSUFFICIENT EVIDENCE
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto w-full">
      {/* Comparison Input Card */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/10 shadow-xl backdrop-blur-md">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-slate-300 font-semibold">
              <GitCompare className="w-4 h-4 text-indigo-400" />
              <span>Cross-Document Comparison Matrix</span>
            </div>
            <span className="text-[11px] text-slate-400">
              Select at least 2 documents to compare
            </span>
          </div>

          {/* Document selection chips */}
          <div className="flex items-center gap-2 flex-wrap">
            {documents.map((doc) => {
              const isChecked = effectiveDocIds.includes(doc.id);
              return (
                <button
                  key={doc.id}
                  type="button"
                  onClick={() => onToggleDocSelection(doc.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    isChecked
                      ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40 shadow-sm"
                      : "bg-slate-950/60 text-slate-400 border-white/5 hover:border-white/15"
                  }`}
                >
                  <FileText className="w-3 h-3 flex-shrink-0" />
                  <span className="truncate max-w-[150px]">{doc.filename}</span>
                </button>
              );
            })}
          </div>

          {effectiveDocIds.length < 2 && (
            <p className="text-[11px] text-amber-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Please check at least 2 documents in the library to enable comparison.
            </p>
          )}

          {/* Topic Input */}
          <div className="relative flex items-center">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. How does client-server communication and requests work across these documents?"
              className="w-full pl-4 pr-12 py-3 rounded-xl bg-slate-950/80 border border-white/10 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            />
            <button
              type="submit"
              disabled={!topic.trim() || isLoading || effectiveDocIds.length < 2}
              className="absolute right-2 p-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 transition-all shadow-md shadow-indigo-600/20"
              title="Compare Documents"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <GitCompare className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* Quick Topics */}
          <div className="flex items-center gap-2 flex-wrap pt-1">
            <span className="text-[11px] text-slate-500 flex items-center gap-1">
              <HelpCircle className="w-3 h-3" /> Sample Topics:
            </span>
            {SAMPLE_TOPICS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setTopic(sample)}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-white/5 hover:border-indigo-500/30 transition-all text-left"
              >
                {sample}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
          <div>
            <p className="font-semibold">Comparison failed</p>
            <p className="text-xs text-rose-300/80 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="p-6 rounded-2xl bg-slate-900/40 border border-white/5 animate-pulse flex flex-col gap-4">
          <div className="w-36 h-6 rounded-full bg-slate-800" />
          <div className="w-full h-16 rounded-xl bg-slate-800" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="h-40 rounded-xl bg-slate-800" />
            <div className="h-40 rounded-xl bg-slate-800" />
          </div>
        </div>
      )}

      {/* Comparison Results */}
      {comparisonResponse && !isLoading && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 shadow-2xl backdrop-blur-md flex flex-col gap-6 animate-fade-in">
          {/* Top Status & Relationship Badge */}
          <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-white/5">
            <div className="flex items-center gap-3">
              {getRelationshipBadge(comparisonResponse.synthesis.relationship)}
              <span className="text-xs text-slate-400">
                via {comparisonResponse.model_used}
              </span>
            </div>

            <span className="text-xs text-slate-400">
              Status: {comparisonResponse.status}
            </span>
          </div>

          {/* Topic */}
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Compared Topic
            </span>
            <p className="text-sm font-medium text-slate-200 mt-0.5">
              "{comparisonResponse.topic}"
            </p>
          </div>

          {/* Comparative Synthesis Summary */}
          <div className="bg-slate-950/50 p-4 rounded-xl border border-white/5 flex flex-col gap-2">
            <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">
              Comparative Synthesis
            </span>
            <p className="text-sm text-slate-100 leading-relaxed">
              {comparisonResponse.synthesis.summary}
            </p>
          </div>

          {/* Scope Warnings Box if present */}
          {comparisonResponse.synthesis.scope_warnings.length > 0 && (
            <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 text-xs text-indigo-200/90 flex items-start gap-3">
              <AlertCircle className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
              <div className="flex flex-col gap-1">
                <p className="font-semibold text-indigo-300">
                  Scope & Definition Context:
                </p>
                {comparisonResponse.synthesis.scope_warnings.map((w, idx) => (
                  <p key={idx} className="text-[11px] text-indigo-200/80">
                    • {w}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Per-Document Findings Grid */}
          <div className="flex flex-col gap-3 pt-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Per-Document Findings & Verified Evidence
            </span>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {comparisonResponse.findings.map((f, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-950/40 border border-white/5 flex flex-col gap-3"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-white/5">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200 truncate">
                      <FileText className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                      <span className="truncate">{f.filename}</span>
                    </div>

                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        f.status === "FINDING_EXTRACTED"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      {f.status === "FINDING_EXTRACTED"
                        ? "EVIDENCE FOUND"
                        : "NO EVIDENCE"}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {f.finding}
                  </p>

                  {/* Document Citations */}
                  {f.citations.length > 0 && (
                    <div className="flex flex-col gap-1.5 pt-1">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                        Citations ({f.citations.length})
                      </span>
                      <div className="flex flex-col gap-1.5">
                        {f.citations.map((cit, cIdx) => (
                          <button
                            key={cIdx}
                            type="button"
                            onClick={() => onInspectCitation(cit)}
                            className="p-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/80 border border-white/5 text-left text-xs text-slate-300 transition-all flex items-center justify-between group"
                          >
                            <span className="truncate pr-2 italic">
                              "{cit.excerpt.slice(0, 75)}..."
                            </span>
                            <span className="text-[11px] font-medium text-indigo-400 flex items-center gap-1 flex-shrink-0">
                              Page {cit.page_number}
                              <ExternalLink className="w-3 h-3" />
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
