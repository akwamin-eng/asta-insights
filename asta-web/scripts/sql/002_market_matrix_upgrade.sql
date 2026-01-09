-- ARCHIVED SCHEMA CHANGE: RSS SENTINEL & SEED DATA LOGIC

-- 1. Create the robust Market News table for RSS Ingestion
CREATE TABLE IF NOT EXISTS public.market_news (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    title text NOT NULL,
    url text NOT NULL UNIQUE,
    summary text,
    source text,
    category text, -- 'economy', 'real_estate', 'general'
    published_at timestamp with time zone,
    
    -- AI Workflow Columns
    status text DEFAULT 'pending_enrichment', -- 'pending_enrichment', 'enriched', 'failed'
    sentiment_score numeric DEFAULT 0,
    ai_summary text,
    
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT market_news_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_market_news_url ON public.market_news(url);
CREATE INDEX IF NOT EXISTS idx_market_news_status ON public.market_news(status);

-- 2. Add 'is_seed' flag to properties for accurate counting
ALTER TABLE public.properties 
ADD COLUMN IF NOT EXISTS is_seed boolean DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_properties_is_seed ON public.properties(is_seed);

-- 3. Backfill seed data (Adjust ID range as needed)
UPDATE public.properties 
SET is_seed = true 
WHERE id <= 750 AND is_seed = false;
