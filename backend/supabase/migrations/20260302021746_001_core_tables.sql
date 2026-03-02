CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;


-- BUSINESSES: one row = one cleaning company (tenant)
CREATE TABLE businesses (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                 TEXT NOT NULL,
  pricing_config       JSONB NOT NULL DEFAULT '{}',
  sop_vector_namespace TEXT UNIQUE,
  stripe_account_id    TEXT,
  jobber_access_token  TEXT,
  vapi_assistant_id    TEXT,
  created_at           TIMESTAMPTZ DEFAULT now()
);


-- CLIENTS: customers of a cleaning business
CREATE TABLE clients (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id      UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  full_name        TEXT NOT NULL,
  phone            TEXT,
  email            TEXT,
  address          TEXT,
  property_details JSONB DEFAULT '{}',
  jobber_client_id TEXT,
  created_at       TIMESTAMPTZ DEFAULT now()
);


-- TECHNICIANS: cleaning staff
CREATE TABLE technicians (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  full_name   TEXT NOT NULL,
  phone       TEXT NOT NULL,
  home_lat    FLOAT,
  home_lng    FLOAT,
  skills      TEXT[] DEFAULT '{}',
  availability JSONB DEFAULT '{}',
  is_active   BOOLEAN DEFAULT true,
  created_at  TIMESTAMPTZ DEFAULT now()
);


-- JOBS: the core entity — one cleaning appointment
CREATE TYPE job_status AS ENUM
  ('pending','confirmed','in_progress','completed','cancelled');


CREATE TABLE jobs (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id              UUID NOT NULL REFERENCES businesses(id),
  client_id                UUID REFERENCES clients(id),
  technician_id            UUID REFERENCES technicians(id),
  status                   job_status NOT NULL DEFAULT 'pending',
  service_type             TEXT NOT NULL,
  scheduled_at             TIMESTAMPTZ NOT NULL,
  quoted_price             NUMERIC(10,2) NOT NULL,
  deposit_amount           NUMERIC(10,2),
  deposit_captured         BOOLEAN DEFAULT false,
  stripe_payment_intent_id TEXT,
  cleanliness_score        SMALLINT CHECK (cleanliness_score BETWEEN 1 AND 5),
  qa_report_url            TEXT,
  jobber_job_id            TEXT,
  created_at               TIMESTAMPTZ DEFAULT now()
);


-- JOB_PHOTOS: before/after images for a job
CREATE TYPE photo_type AS ENUM ('before','after');


CREATE TABLE job_photos (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id            UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  photo_type        photo_type NOT NULL,
  storage_path      TEXT NOT NULL,
  cv_audit_result   JSONB DEFAULT '{}',
  cleanliness_score SMALLINT,
  uploaded_at       TIMESTAMPTZ DEFAULT now()
);


-- SOP_CHUNKS: text chunks from SOPs/FAQs stored as vectors
CREATE TABLE sop_chunks (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  content     TEXT NOT NULL,
  embedding   vector(1536),
  created_at  TIMESTAMPTZ DEFAULT now()
);


-- HNSW index for fast cosine similarity search at scale
CREATE INDEX ON sop_chunks USING hnsw (embedding vector_cosine_ops);

