"use client";

import React, { useState } from "react";
import {
  Send,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Search,
  HelpCircle,
  ExternalLink,
} from "lucide-react";
import { GroundedAnswerResponse, ValidatedCitation } from "../lib/types";

interface QAViewProps {
  onAskQuestion: (question: string) => Promise<void>;
  answerResponse: GroundedAnswerResponse | null;
  isLoading: boolean;
  error: string | null;
  onInspectCitation: (citation: ValidatedCitation) => void;
  selectedDocCount: number;
}

const SAMPLE_QUESTIONS = [
  "Why did different students see different IP addresses for Google?",
  "What does an API do and what is an Endpoint?",
  "What is the orbital speed of Saturn and its rings?", // Demonstrates Abstention
];

export const QAView: React.FC<QAViewProps> = ({
  onAskQuestion,
  answerResponse,
  isLoading,
  error,
  onInspectCitation,
  selectedDocCount,
}) => {
  const [question, setQuestion] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    await onAskQuestion(question);
  };

  const handleSelectSample = (sample: string) => {
    setQuestion(sample);
  };

  return (
    <div className="flex flex-col gap-6 max-w-4xl mx-auto w-full">
      {/* Search / Question Input Card */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/10 shadow-xl backdrop-blur-md">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Search className="w-4 h-4 text-indigo-400" />
            <span className="font-semibold text-slate-300">
              Ask Evidence-Grounded Question
            </span>
            {selectedDocCount > 0 && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-white/5">
                Restricted to {selectedDocCount} selected doc(s)
              </span>
            )}
          </div>

          <div className="relative flex items-center">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Why did different students see different IP addresses for Google?"
              className="w-full pl-4 pr-12 py-3 rounded-xl bg-slate-950/80 border border-white/10 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
            />
            <button
              type="submit"
              disabled={!question.trim() || isLoading}
              className="absolute right-2 p-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 transition-all shadow-md shadow-indigo-600/20"
              title="Submit Question"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* Quick Prompts */}
          <div className="flex items-center gap-2 flex-wrap pt-1">
            <span className="text-[11px] text-slate-500 flex items-center gap-1">
              <HelpCircle className="w-3 h-3" /> Try:
            </span>
            {SAMPLE_QUESTIONS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectSample(sample)}
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
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
          <div>
            <p className="font-semibold">Unable to process question</p>
            <p className="text-xs text-rose-300/80 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="p-6 rounded-2xl bg-slate-900/40 border border-white/5 animate-pulse flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="w-24 h-6 rounded-full bg-slate-800" />
            <div className="w-32 h-4 rounded bg-slate-800" />
          </div>
          <div className="space-y-2">
            <div className="w-full h-4 rounded bg-slate-800" />
            <div className="w-5/6 h-4 rounded bg-slate-800" />
            <div className="w-4/6 h-4 rounded bg-slate-800" />
          </div>
          <div className="flex gap-2 pt-2">
            <div className="w-32 h-8 rounded-lg bg-slate-800" />
            <div className="w-32 h-8 rounded-lg bg-slate-800" />
          </div>
        </div>
      )}

      {/* Answer Response Display */}
      {answerResponse && !isLoading && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-white/10 shadow-2xl backdrop-blur-md flex flex-col gap-5 animate-fade-in">
          {/* Header Status Bar */}
          <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-white/5">
            <div className="flex items-center gap-2.5">
              {answerResponse.status === "ANSWERED" ? (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  VERIFIED GROUNDED ANSWER
                </span>
              ) : (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  INSUFFICIENT EVIDENCE (ABSTAINED)
                </span>
              )}

              <span className="text-xs text-slate-400">
                via {answerResponse.model_used}
              </span>
            </div>

            <span className="text-xs text-slate-400">
              {answerResponse.validated_citations_count} verified source citation(s)
            </span>
          </div>

          {/* Question Recap */}
          <div>
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Question
            </span>
            <p className="text-sm font-medium text-slate-200 mt-0.5">
              "{answerResponse.question}"
            </p>
          </div>

          {/* Answer Text */}
          <div className="bg-slate-950/40 p-4 rounded-xl border border-white/5">
            <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider block mb-1">
              Synthesized Evidence Answer
            </span>
            <p className="text-sm text-slate-100 leading-relaxed whitespace-pre-wrap">
              {answerResponse.answer}
            </p>
          </div>

          {/* Abstention Explanation Callout if any */}
          {answerResponse.status === "INSUFFICIENT_EVIDENCE" && (
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/20 text-xs text-amber-200/90 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-amber-300">
                  Zero Hallucination Guarantee:
                </p>
                <p className="text-[11px] text-amber-200/80 mt-0.5">
                  The model detected that the documents do not contain explicit facts to answer this question with certainty, and refrained from fabricating unverified claims.
                </p>
              </div>
            </div>
          )}

          {/* Verified Citations List */}
          {answerResponse.citations.length > 0 && (
            <div className="flex flex-col gap-2 pt-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Supporting Source Passages (Click to Inspect)
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {answerResponse.citations.map((citation, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onInspectCitation(citation)}
                    className="group p-3 rounded-xl bg-slate-800/40 hover:bg-slate-800/80 border border-white/5 hover:border-indigo-500/40 transition-all text-left flex flex-col gap-1.5 shadow-sm"
                  >
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-300 group-hover:text-indigo-200 truncate">
                        <FileText className="w-3.5 h-3.5 flex-shrink-0" />
                        <span className="truncate">{citation.filename}</span>
                      </div>
                      <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 flex-shrink-0" />
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span className="px-1.5 py-0.5 rounded bg-slate-700/60 font-medium text-slate-200">
                        Page {citation.page_number}
                      </span>
                      <span>•</span>
                      <span className="text-emerald-400">
                        {(citation.similarity_score * 100).toFixed(0)}% relevance
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 line-clamp-2 italic text-left mt-0.5">
                      "{citation.excerpt}"
                    </p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
