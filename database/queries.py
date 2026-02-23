"""
Consultas SQL predefinidas para el análisis del mercado laboral.
"""

# 1. Consulta para el Dashboard de Streamlit (Distribución de Sectores)
GET_SECTOR_DISTRIBUTION = """
SELECT 
    sector, 
    COUNT(*) as total_vacantes 
FROM jobs 
WHERE is_active = TRUE 
GROUP BY sector 
ORDER BY total_vacantes DESC;
"""

# 2. Consulta para identificar las Top Skills más demandadas
GET_TOP_SKILLS = """
SELECT 
    skill_name, 
    COUNT(*) as frecuencia 
FROM skills 
GROUP BY skill_name 
ORDER BY frecuencia DESC 
LIMIT 20;
"""

# 3. Consulta de Auditoría de Calidad de Datos
GET_DATA_QUALITY_METRICS = """
SELECT 
    source_platform,
    AVG(data_quality_score) as promedio_calidad,
    COUNT(*) as total_procesados
FROM jobs 
GROUP BY source_platform;
"""

# 4. Consulta para el mapa de calor (Distribución por país)
GET_JOBS_BY_COUNTRY = """
SELECT 
    country, 
    COUNT(*) as total 
FROM jobs 
GROUP BY country 
ORDER BY total DESC;
"""