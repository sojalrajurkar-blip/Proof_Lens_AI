export interface Workspace {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  workspace_id: string;
  filename: string;
  file_size_bytes: number;
  page_count: number;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "UNSUPPORTED_SCANNED_PDF";
  error_message?: string | null;
  created_at: string;
}

export interface ValidatedCitation {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number: number;
  chunk_index: number;
  excerpt: string;
  similarity_score: number;
}

export interface GroundedAnswerResponse {
  question: string;
  workspace_id: string;
  status: "ANSWERED" | "INSUFFICIENT_EVIDENCE" | "ERROR";
  answer: string;
  citations: ValidatedCitation[];
  total_retrieved: number;
  validated_citations_count: number;
  model_used: string;
  abstention_reason?: string | null;
}

export interface DocumentFinding {
  document_id: string;
  filename: string;
  status: "FINDING_EXTRACTED" | "INSUFFICIENT_EVIDENCE";
  finding: string;
  citations: ValidatedCitation[];
}

export interface ComparisonSynthesis {
  relationship: "AGREEMENT" | "DIFFERENCE" | "CONTRADICTION" | "INSUFFICIENT_EVIDENCE";
  summary: string;
  scope_warnings: string[];
}

export interface ComparisonResponse {
  workspace_id: string;
  topic: string;
  status: "COMPLETED" | "PARTIAL" | "INSUFFICIENT_EVIDENCE";
  findings: DocumentFinding[];
  synthesis: ComparisonSynthesis;
  model_used: string;
}

export interface PassageDetail {
  chunk_id: string;
  document_id: string;
  workspace_id: string;
  filename: string;
  page_number: number;
  chunk_index: number;
  content: string;
  char_count: number;
  word_count: number;
  prev_chunk_id?: string | null;
  next_chunk_id?: string | null;
}
