import {
  Workspace,
  DocumentItem,
  GroundedAnswerResponse,
  ComparisonResponse,
  PassageDetail,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMsg = `API Error (${res.status})`;
      try {
        const errorJson = await res.json();
        errorMsg = errorJson.detail || errorJson.message || errorMsg;
      } catch {
        // Fallback to text or status
      }
      throw new ApiError(errorMsg, res.status);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      err?.message || "Failed to communicate with ProofLens backend.",
      500
    );
  }
}

export const api = {
  // Health
  checkHealth: async () => {
    return request<{ status: string; app: string }>("/health");
  },

  // Workspaces
  getWorkspaces: async (): Promise<Workspace[]> => {
    return request<Workspace[]>("/workspaces");
  },

  createWorkspace: async (name: string): Promise<Workspace> => {
    return request<Workspace>("/workspaces", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },

  // Documents
  getDocuments: async (workspaceId: string): Promise<DocumentItem[]> => {
    return request<DocumentItem[]>(`/workspaces/${workspaceId}/documents`);
  },

  uploadDocument: async (
    workspaceId: string,
    file: File
  ): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      let errorMsg = `Upload failed (${res.status})`;
      try {
        const errJson = await res.json();
        errorMsg = errJson.detail || errJson.message || errorMsg;
      } catch {}
      throw new ApiError(errorMsg, res.status);
    }

    return await res.json();
  },

  deleteDocument: async (workspaceId: string, documentId: string): Promise<void> => {
    return request<void>(`/workspaces/${workspaceId}/documents/${documentId}`, {
      method: "DELETE",
    });
  },

  // Evidence Passage Inspection
  getPassage: async (
    workspaceId: string,
    documentId: string,
    chunkId: string
  ): Promise<PassageDetail> => {
    return request<PassageDetail>(
      `/workspaces/${workspaceId}/documents/${documentId}/passages/${chunkId}`
    );
  },

  // Q&A
  askQuestion: async (
    workspaceId: string,
    question: string,
    topK: number = 5,
    documentIds?: string[]
  ): Promise<GroundedAnswerResponse> => {
    return request<GroundedAnswerResponse>(`/workspaces/${workspaceId}/ask`, {
      method: "POST",
      body: JSON.stringify({
        question,
        top_k: topK,
        document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined,
      }),
    });
  },

  // Cross-Document Comparison
  compareDocuments: async (
    workspaceId: string,
    topic: string,
    documentIds: string[],
    topKPerDoc: number = 3
  ): Promise<ComparisonResponse> => {
    return request<ComparisonResponse>(`/workspaces/${workspaceId}/compare`, {
      method: "POST",
      body: JSON.stringify({
        topic,
        document_ids: documentIds,
        top_k_per_document: topKPerDoc,
      }),
    });
  },
};
