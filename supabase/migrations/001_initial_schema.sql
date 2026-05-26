CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS resume_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    source_file_path TEXT,
    markdown_path TEXT NOT NULL DEFAULT '',
    raw_text TEXT NOT NULL DEFAULT '',
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    skills_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    project_highlights JSONB NOT NULL DEFAULT '[]'::jsonb,
    potential_questions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS job_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    company TEXT NOT NULL DEFAULT '',
    raw_text TEXT NOT NULL DEFAULT '',
    markdown_path TEXT NOT NULL DEFAULT '',
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    must_have_skills_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    domain TEXT NOT NULL DEFAULT '',
    level TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'markdown',
    raw_text TEXT NOT NULL DEFAULT '',
    source_file_path TEXT,
    markdown_path TEXT NOT NULL DEFAULT '',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    embedding_status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS material_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(material_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_profile_id UUID REFERENCES resume_profiles(id) ON DELETE SET NULL,
    job_profile_id UUID REFERENCES job_profiles(id) ON DELETE SET NULL,
    selected_material_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'active',
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_topic TEXT,
    covered_topics JSONB NOT NULL DEFAULT '[]'::jsonb,
    follow_up_count INTEGER NOT NULL DEFAULT 0,
    unclear_count INTEGER NOT NULL DEFAULT 0,
    current_round INTEGER NOT NULL DEFAULT 0,
    max_rounds INTEGER NOT NULL DEFAULT 8,
    assessment JSONB,
    assessment_status TEXT NOT NULL DEFAULT 'pending',
    assessment_error TEXT NOT NULL DEFAULT '',
    memory_updates JSONB NOT NULL DEFAULT '[]'::jsonb,
    transcript_path TEXT NOT NULL DEFAULT '',
    report_path TEXT NOT NULL DEFAULT '',
    router_source TEXT NOT NULL DEFAULT '',
    retrieved_context JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS knowledge_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL DEFAULT '',
    mastery_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    exposure_count INTEGER NOT NULL DEFAULT 0,
    weakness_count INTEGER NOT NULL DEFAULT 0,
    last_tested_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,
    evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_interview_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_material_chunks_material_id ON material_chunks(material_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_memories_mastery ON knowledge_memories(mastery_score);
CREATE INDEX IF NOT EXISTS idx_knowledge_memories_next_review ON knowledge_memories(next_review_at);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_created_at ON interview_sessions(created_at DESC);

CREATE OR REPLACE FUNCTION match_material_chunks(
    query_embedding VECTOR(1536),
    match_count INTEGER DEFAULT 2,
    filter_material_ids UUID[] DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    material_id UUID,
    chunk_index INTEGER,
    content TEXT,
    metadata_json JSONB,
    similarity DOUBLE PRECISION
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        material_chunks.id,
        material_chunks.material_id,
        material_chunks.chunk_index,
        material_chunks.content,
        material_chunks.metadata_json,
        1 - (material_chunks.embedding <=> query_embedding) AS similarity
    FROM material_chunks
    WHERE filter_material_ids IS NULL
       OR material_chunks.material_id = ANY(filter_material_ids)
    ORDER BY material_chunks.embedding <=> query_embedding
    LIMIT match_count;
$$;
