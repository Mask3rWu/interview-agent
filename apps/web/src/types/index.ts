export interface ResumeProfile {
  id: string;
  name: string;
  raw_text: string;
  markdown_path: string;
  summary_json: { summary?: string };
  skills_json: Record<string, string[]>;
  project_highlights: string[];
  potential_questions_json: string[];
  created_at: string;
  updated_at: string;
}

export interface JobProfile {
  id: string;
  name: string;
  company: string;
  raw_text: string;
  markdown_path: string;
  summary_json: { summary?: string };
  must_have_skills_json: string[];
  domain: string;
  level: string;
  created_at: string;
  updated_at: string;
}

export interface Material {
  id: string;
  name: string;
  type: string;
  raw_text: string;
  markdown_path: string;
  enabled: boolean;
  chunk_count: number;
  embedding_status: string;
  created_at: string;
}

export interface InterviewSession {
  id: string;
  resume_profile_id: string | null;
  job_profile_id: string | null;
  selected_material_ids: string[];
  status: "active" | "ended";
  messages: ChatMessage[];
  current_topic: string | null;
  covered_topics: string[];
  follow_up_count: number;
  unclear_count: number;
  current_round: number;
  max_rounds: number;
  assessment: AssessmentResult | null;
  memory_updates: MemoryUpdate[];
  transcript_path: string;
  report_path: string;
  router_source: string;
  created_at: string;
}

export interface ChatMessage {
  role: "interviewer" | "user";
  content: string;
}

export interface AssessmentResult {
  total_score: number;
  tech_score: number;
  communication_score: number;
  highlights: string[];
  weaknesses: string[];
  suggested_review: string[];
  memory_updates: MemoryUpdate[];
}

export interface MemoryUpdate {
  topic: string;
  category: string;
  performance: "excellent" | "adequate" | "vague" | "wrong" | "unknown";
  evidence: string;
}

export interface InterviewEvent {
  event: "token" | "message_end" | "assessment" | "error" | "first_question";
  data: string | AssessmentResult | { token: string } | { full_text: string };
}

export interface KnowledgeMemory {
  id: string;
  topic: string;
  category: string;
  mastery_score: number;
  exposure_count: number;
  weakness_count: number;
  last_tested_at: string | null;
  next_review_at: string | null;
  evidence_json: { interview_id: string; performance: string; timestamp: string }[];
  source_interview_ids: string[];
  updated_at: string;
}
