DELETE FROM material_chunks;

ALTER TABLE material_chunks
    ALTER COLUMN embedding TYPE VECTOR(1024)
    USING NULL;

CREATE OR REPLACE FUNCTION match_material_chunks(
    query_embedding VECTOR(1024),
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
    WHERE material_chunks.embedding IS NOT NULL
      AND (
          filter_material_ids IS NULL
          OR material_chunks.material_id = ANY(filter_material_ids)
      )
    ORDER BY material_chunks.embedding <=> query_embedding
    LIMIT match_count;
$$;

UPDATE materials
SET embedding_status = 'pending',
    processing_error = 'Embedding model changed to BAAI/bge-m3; reprocess this material to rebuild vectors.',
    chunk_count = 0;
