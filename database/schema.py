SCHEMA_SQL = """
-- Tabla de Vacantes (Basada en estructura actual de Supabase)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    company_name VARCHAR(255),
    location VARCHAR(255),
    country VARCHAR(100),
    job_type VARCHAR(100),
    seniority_level VARCHAR(100),
    sector VARCHAR(100),
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR(255),
    salary_min NUMERIC, 
    salary_max NUMERIC, 
    posted_date DATE,
    source_url TEXT,
    source_platform VARCHAR(100),
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT jobs_job_id_source_platform_key UNIQUE (job_id, source_platform)
);

-- Tabla de Habilidades (Corregida relación según tus constraints)
CREATE TABLE IF NOT EXISTS skills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id VARCHAR(255), -- VARCHAR para coincidir con jobs.job_id
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT skills_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    CONSTRAINT unique_job_skill UNIQUE (job_id, skill_name)
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_jobs_sector ON jobs(sector);
CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs(country);
CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(skill_name);
"""