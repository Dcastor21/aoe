CREATE OR REPLACE FUNCTION match_sop_chunks(
  query_embedding vector(1536),
  match_business_id UUID,
  match_count INT DEFAULT 3
)
RETURNS TABLE (id UUID, content TEXT, similarity FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    sop_chunks.id,
    sop_chunks.content,
    1 - (sop_chunks.embedding <=> query_embedding) AS similarity
  FROM sop_chunks
  WHERE sop_chunks.business_id = match_business_id
  ORDER BY sop_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

