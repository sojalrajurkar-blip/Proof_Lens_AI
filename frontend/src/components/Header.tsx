"use client";

import React from "react";
import { ShieldCheck, Plus, Layers, Sparkles } from "lucide-react";
import { Workspace } from "../lib/types";

interface HeaderProps {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  onSelectWorkspace: (ws: Workspace) => void;
  onOpenNewWorkspaceModal: () => void;
  backendOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  workspaces,
  activeWorkspace,
  onSelectWorkspace,
  onOpenNewWorkspaceModal,
  backendOnline,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-[#090d16]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-indigo-400/30">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-white">
                ProofLens <span className="text-indigo-400">AI</span>
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                PROV-RAG
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              From Documents to Verifiable Answers
            </p>
          </div>
        </div>

        {/* Center: Workspace Selector */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-white/10 shadow-inner">
            <Layers className="w-4 h-4 text-slate-400" />
            <select
              aria-label="Select Workspace"
              value={activeWorkspace?.id || ""}
              onChange={(e) => {
                const found = workspaces.find((w) => w.id === e.target.value);
                if (found) onSelectWorkspace(found);
              }}
              className="bg-transparent text-sm text-slate-200 font-medium focus:outline-none cursor-pointer pr-2"
            >
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.id} className="bg-slate-900 text-slate-200">
                  {ws.name}
                </option>
              ))}
              {workspaces.length === 0 && (
                <option value="" disabled className="bg-slate-900 text-slate-400">
                  No Workspaces Available
                </option>
              )}
            </select>
          </div>

          <button
            onClick={onOpenNewWorkspaceModal}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
            title="Create New Workspace"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden md:inline">New Workspace</span>
          </button>
        </div>

        {/* Right: Status Indicators */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900/80 border border-white/10 text-[11px]">
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline ? "bg-emerald-400 animate-pulse" : "bg-rose-500"
              }`}
            />
            <span className="text-slate-300">
              {backendOnline ? "Backend Live" : "Connecting..."}
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-950/40 border border-indigo-500/20 text-[11px] text-indigo-300">
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>gemini-3.5-flash-lite</span>
          </div>
        </div>
      </div>
    </header>
  );
};
