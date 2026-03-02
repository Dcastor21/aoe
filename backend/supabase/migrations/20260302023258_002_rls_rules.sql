ALTER TABLE businesses  ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients     ENABLE ROW LEVEL SECURITY;
ALTER TABLE technicians ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs        ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_photos  ENABLE ROW LEVEL SECURITY;
ALTER TABLE sop_chunks  ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION current_business_id()
RETURNS UUID AS $$
  SELECT (auth.jwt() -> 'user_metadata' ->> 'business_id')::UUID;
$$ LANGUAGE sql STABLE;


-- Each table gets a policy: you can only access your own business's rows
CREATE POLICY "clients_isolation" ON clients
  FOR ALL USING (business_id = current_business_id());


CREATE POLICY "technicians_isolation" ON technicians
  FOR ALL USING (business_id = current_business_id());


CREATE POLICY "jobs_isolation" ON jobs
  FOR ALL USING (business_id = current_business_id());


-- Photos are scoped via their parent job's business_id
CREATE POLICY "photos_isolation" ON job_photos FOR ALL
  USING (EXISTS (
    SELECT 1 FROM jobs
    WHERE id = job_photos.job_id
    AND business_id = current_business_id()
  ));


CREATE POLICY "sop_isolation" ON sop_chunks
  FOR ALL USING (business_id = current_business_id());

