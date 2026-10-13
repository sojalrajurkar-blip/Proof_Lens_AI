"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  MessageSquare,
  GitCompare,
  Sparkles,
  BookOpen,
  Layers,
  AlertTriangle,
  RefreshCw,
  Search,
} from "lucide-react";
import { Header } from "../components/Header";
import { Sidebar } from "../components/Sidebar";
import { QAView } from "../components/QAView";
import { ComparisonView } from "../components/ComparisonView";
import { PassageModal } from "../components/PassageModal";
import { NewWorkspaceModal } from "../components/NewWorkspaceModal";
import {
  Workspace,
  DocumentItem,
  GroundedAnswerResponse,
  ComparisonResponse,
  ValidatedCitation,
} from "../lib/types";
import { api } from "../lib/api";

export default function Home() {
  // Workspaces state
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [isNewWsModalOpen, setIsNewWsModalOpen] = useState(false);

  // Documents state
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Active View Tab
  const [activeTab, setActiveTab] = useState<"qa" | "compare">("qa");

  // Q&A State
  const [qaLoading, setQaLoading] = useState(false);
  const [qaError, setQaError] = useState<string | null>(null);
  const [answerResponse, setAnswerResponse] = useState<GroundedAnswerResponse | null>(null);

  // Comparison State
  const [compLoading, setCompLoading] = useState(false);
  const [compError, setCompError] = useState<string | null>(null);
  const [comparisonResponse, setComparisonResponse] = useState<ComparisonResponse | null>(null);

  // Evidence Passage Modal State
  const [inspectingCitation, setInspectingCitation] = useState<ValidatedCitation | null>(null);
  const [isPassageModalOpen, setIsPassageModalOpen] = useState(false);

  // Backend Health
  const [backendOnline, setBackendOnline] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  // Health check & workspace initialization
  const initialize = useCallback(async () => {
    try {
      // Check health
      try {
        await api.checkHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }

      // Fetch or create workspaces
      let wsList = await api.getWorkspaces();
      if (!wsList || wsList.length === 0) {
        const defaultWs = await api.createWorkspace("Default Workspace");
        wsList = [defaultWs];
      }
      setWorkspaces(wsList);
      setActiveWorkspace(wsList[0]);
    } catch (err: any) {
      console.error("Initialization error:", err);
    } finally {
      setInitialLoading(false);
    }
  }, []);

  useEffect(() => {
    initialize();
  }, [initialize]);

  // Load documents when active workspace changes
  const loadDocuments = useCallback(async (wsId: string) => {
    try {
      const docs = await api.getDocuments(wsId);
      setDocuments(docs);
      // Select all ready documents by default
      const readyDocIds = docs
        .filter((d) => d.status === "COMPLETED")
        .map((d) => d.id);
      setSelectedDocIds(readyDocIds);
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  }, []);

  useEffect(() => {
    if (activeWorkspace) {
      loadDocuments(activeWorkspace.id);
      // Reset responses when workspace changes
      setAnswerResponse(null);
      setComparisonResponse(null);
      setQaError(null);
      setCompError(null);
    }
  }, [activeWorkspace, loadDocuments]);

  // Workspace handlers
  const handleSelectWorkspace = (ws: Workspace) => {
    setActiveWorkspace(ws);
  };

  const handleCreateWorkspace = async (name: string) => {
    const newWs = await api.createWorkspace(name);
    setWorkspaces((prev) => [newWs, ...prev]);
    setActiveWorkspace(newWs);
  };

  // Document upload handler
  const handleUploadFile = async (file: File) => {
    if (!activeWorkspace) return;
    setIsUploading(true);
    setUploadError(null);
    try {
      const uploadedDoc = await api.uploadDocument(activeWorkspace.id, file);
      // Refetch documents
      await loadDocuments(activeWorkspace.id);
      if (uploadedDoc.status === "COMPLETED") {
        setSelectedDocIds((prev) => Array.from(new Set([...prev, uploadedDoc.id])));
      }
    } catch (err: any) {
      setUploadError(err?.message || "Failed to upload document.");
    } finally {
      setIsUploading(false);
    }
  };

  // Document delete handler
  const handleDeleteDocument = async (docId: string) => {
    if (!activeWorkspace) return;
    try {
      await api.deleteDocument(activeWorkspace.id, docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      setSelectedDocIds((prev) => prev.filter((id) => id !== docId));
    } catch (err: any) {
      console.error("Failed to delete document:", err);
    }
  };

  // Selection handlers
  const handleToggleDocSelection = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleSelectAllDocs = (selectAll: boolean) => {
    if (selectAll) {
      const readyIds = documents
        .filter((d) => d.status === "COMPLETED")
        .map((d) => d.id);
      setSelectedDocIds(readyIds);
    } else {
      setSelectedDocIds([]);
    }
  };

  // Q&A handler
  const handleAskQuestion = async (question: string) => {
    if (!activeWorkspace) return;
    setQaLoading(true);
    setQaError(null);
    try {
      const res = await api.askQuestion(
        activeWorkspace.id,
        question,
        5,
        selectedDocIds.length > 0 ? selectedDocIds : undefined
      );
      setAnswerResponse(res);
    } catch (err: any) {
      setQaError(err?.message || "Failed to obtain grounded answer.");
    } finally {
      setQaLoading(false);
    }
  };

  // Comparison handler
  const handleCompareDocuments = async (topic: string, docIds: string[]) => {
    if (!activeWorkspace) return;
    setCompLoading(true);
    setCompError(null);
    try {
      const res = await api.compareDocuments(activeWorkspace.id, topic, docIds, 3);
      setComparisonResponse(res);
    } catch (err: any) {
      setCompError(err?.message || "Failed to compare documents.");
    } finally {
      setCompLoading(false);
    }
  };

  // Passage Modal handler
  const handleInspectCitation = (citation: ValidatedCitation) => {
    setInspectingCitation(citation);
    setIsPassageModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <Header
        workspaces={workspaces}
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={handleSelectWorkspace}
        onOpenNewWorkspaceModal={() => setIsNewWsModalOpen(true)}
        backendOnline={backendOnline}
      />

      {/* Main Body */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 flex flex-col lg:flex-row gap-6">
        {/* Left Sidebar (Document Management & Provenance Scope) */}
        <aside className="w-full lg:w-80 shrink-0">
          <Sidebar
            documents={documents}
            selectedDocIds={selectedDocIds}
            onToggleDocSelection={handleToggleDocSelection}
            onSelectAllDocs={handleSelectAllDocs}
            onUploadFile={handleUploadFile}
            onDeleteDocument={handleDeleteDocument}
            isUploading={isUploading}
            uploadError={uploadError}
          />
        </aside>

        {/* Right / Main Analysis Area */}
        <main className="flex-1 min-w-0 flex flex-col gap-6">
          {/* Navigation Tabs */}
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-900/80 border border-white/10 shadow-inner">
              <button
                onClick={() => setActiveTab("qa")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === "qa"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Grounded Q&A</span>
              </button>

              <button
                onClick={() => setActiveTab("compare")}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === "compare"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                }`}
              >
                <GitCompare className="w-3.5 h-3.5" />
                <span>Cross-Document Compare</span>
                {selectedDocIds.length >= 2 && (
                  <span className="ml-1 px-1.5 py-0.2 rounded-full bg-indigo-500/30 text-[10px] text-indigo-200">
                    {selectedDocIds.length}
                  </span>
                )}
              </button>
            </div>

            <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Zero-Hallucination Guard Active</span>
            </div>
          </div>

          {/* Active Tab View */}
          {activeTab === "qa" ? (
            <QAView
              onAskQuestion={handleAskQuestion}
              answerResponse={answerResponse}
              isLoading={qaLoading}
              error={qaError}
              onInspectCitation={handleInspectCitation}
              selectedDocCount={selectedDocIds.length}
            />
          ) : (
            <ComparisonView
              documents={documents}
              selectedDocIds={selectedDocIds}
              onToggleDocSelection={handleToggleDocSelection}
              onCompareDocuments={handleCompareDocuments}
              comparisonResponse={comparisonResponse}
              isLoading={compLoading}
              error={compError}
              onInspectCitation={handleInspectCitation}
            />
          )}
        </main>
      </div>

      {/* Modals */}
      {activeWorkspace && (
        <PassageModal
          isOpen={isPassageModalOpen}
          onClose={() => {
            setIsPassageModalOpen(false);
            setInspectingCitation(null);
          }}
          workspaceId={activeWorkspace.id}
          citation={inspectingCitation}
        />
      )}

      <NewWorkspaceModal
        isOpen={isNewWsModalOpen}
        onClose={() => setIsNewWsModalOpen(false)}
        onCreateWorkspace={handleCreateWorkspace}
      />
    </div>
  );
}
