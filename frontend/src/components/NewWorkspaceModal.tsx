"use client";

import React, { useState, useEffect } from "react";
import { X, Layers, Plus, Loader2 } from "lucide-react";

interface NewWorkspaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateWorkspace: (name: string) => Promise<void>;
}

export const NewWorkspaceModal: React.FC<NewWorkspaceModalProps> = ({
  isOpen,
  onClose,
  onCreateWorkspace,
}) => {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setName("");
      setError(null);
      setLoading(false);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    try {
      await onCreateWorkspace(trimmed);
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to create workspace.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="new-workspace-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-[#0c1222] border border-white/15 shadow-2xl overflow-hidden flex flex-col animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 border-b border-white/10 bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 id="new-workspace-title" className="font-semibold text-slate-100 text-base">
                Create Workspace
              </h3>
              <p className="text-xs text-slate-400">
                Organize documents into dedicated collections
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label
              htmlFor="workspace-name-input"
              className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2"
            >
              Workspace Name
            </label>
            <input
              id="workspace-name-input"
              type="text"
              required
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Computer Networks Lab, Q3 Reports..."
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900/90 border border-white/10 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
            />
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-white/5 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || loading}
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Workspace</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
