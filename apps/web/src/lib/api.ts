const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(`HTTP ${res.status}: ${(detail as { detail?: string }).detail || res.statusText}`);
  }
  return res.json();
}

async function upload<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(`HTTP ${res.status}: ${(detail as { detail?: string }).detail || res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Resumes
  createResume: (data: { name: string; raw_text: string }) =>
    request<{ id: string; name: string }>("/resumes", { method: "POST", body: JSON.stringify(data) }),

  listResumes: () => request<{ id: string; name: string }[]>("/resumes"),

  getResume: (id: string) => request<{
    id: string; name: string; raw_text: string; markdown_path: string;
    summary_json: { summary?: string }; skills_json: Record<string, string[]>;
    project_highlights: string[]; potential_questions_json: string[];
  }>(`/resumes/${id}`),

  // Jobs
  createJob: (data: { name: string; company?: string; raw_text: string }) =>
    request<{ id: string; name: string }>("/jobs", { method: "POST", body: JSON.stringify(data) }),

  listJobs: () => request<{ id: string; name: string }[]>("/jobs"),

  getJob: (id: string) => request<{
    id: string; name: string; raw_text: string; company: string; markdown_path: string;
    summary_json: { summary?: string }; must_have_skills_json: string[];
    domain: string; level: string;
  }>(`/jobs/${id}`),

  // Materials
  createMaterial: (data: { name: string; type?: string; raw_text: string }) =>
    request<{ id: string; name: string }>("/materials", { method: "POST", body: JSON.stringify(data) }),

  uploadMaterialPdf: (data: { name: string; file: File }) => {
    const formData = new FormData();
    formData.append("name", data.name);
    formData.append("file", data.file);
    return upload<{ id: string; name: string; embedding_status: string }>("/materials/upload", formData);
  },

  listMaterials: () => request<{
    id: string; name: string; enabled: boolean; chunk_count: number; embedding_status: string;
    processing_error?: string;
  }[]>("/materials"),

  getMaterial: (id: string) => request<{
    id: string; name: string; raw_text: string; chunk_count: number;
    embedding_status: string; markdown_path: string; processing_error?: string; source_file_path?: string;
  }>(`/materials/${id}`),

  reprocessMaterial: (id: string) => request<{
    id: string; name: string; raw_text: string; chunk_count: number;
    embedding_status: string; markdown_path: string; processing_error?: string; source_file_path?: string;
  }>(`/materials/${id}/reprocess`, { method: "POST" }),

  // Interviews
  createInterview: (data: {
    resume_profile_id?: string | null;
    job_profile_id?: string | null;
    material_ids?: string[];
    use_all_materials?: boolean;
    max_rounds?: number;
  }) =>
    request<{ session_id: string; status: string; first_question: string }>("/interviews", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listInterviews: () => request<{
    id: string; status: string; current_round: number; max_rounds: number;
    total_score: number | null; created_at: string;
    assessment_status: "pending" | "success" | "failed";
    assessment_error: string;
    memory_update_count: number;
  }[]>("/interviews"),

  getInterview: (id: string) => request<{
    id: string; status: string; messages: { role: string; content: string }[];
    current_round: number; max_rounds: number; assessment: unknown | null;
    assessment_status: "pending" | "success" | "failed";
    assessment_error: string;
    created_at: string;
  }>(`/interviews/${id}`),

  submitAnswer: (sessionId: string, answer: string) =>
    request<{ event: string; data: string | { total_score: number } }>(
      `/interviews/${sessionId}/answer`,
      { method: "POST", body: JSON.stringify({ answer }) }
    ),

  submitAnswerStream: (sessionId: string): EventSource => {
    const es = new EventSource(
      `${API_BASE}/interviews/${sessionId}/answer/stream`
    );
    // EventSource only supports GET, so we fall back to non-streaming for now
    // The SSE endpoint uses POST; we'll use fetch with ReadableStream instead
    return es;
  },

  finishInterview: (sessionId: string) =>
    request<{ event: string; data: { total_score: number } }>(
      `/interviews/${sessionId}/finish`,
      { method: "POST" }
    ),

  assessInterview: (sessionId: string) =>
    request<{ event: string; data: { total_score: number } }>(
      `/interviews/${sessionId}/assess`,
      { method: "POST" }
    ),

  // Memory
  listMemories: (sortBy = "mastery_score") =>
    request<{
      id: string; topic: string; mastery_score: number; exposure_count: number;
      weakness_count: number; last_tested_at: string | null;
      next_review_at: string | null; source_interview_ids: string[];
    }[]>(`/memory?sort_by=${sortBy}`),

  rebuildMemories: () =>
    request<{
      interview_count: number; success_count: number; failure_count: number;
      memory_update_count: number; memory_count: number;
    }>("/memory/rebuild", { method: "POST" }),
};
