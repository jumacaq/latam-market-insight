# etl/update_data.py
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

# Importamos la nueva función maestra desde cleaning.py
from cleaning import clean_job_data

load_dotenv()

# ---------------------------------------------------
# CONFIGURACIÓN SUPABASE
# ---------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") 

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Error: SUPABASE_URL o SUPABASE_SERVICE_KEY no encontrados en .env")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------
# 📥 CARGA DE DATOS
# ---------------------------------------------------
def load_raw_data():
    """Descarga los datos crudos de las tablas jobs y skills"""
    print("📥 Descargando datos desde Supabase...")
    
    # Descargar Jobs
    jobs_res = client.table("jobs").select("*").execute()
    df_jobs = pd.DataFrame(jobs_res.data)
    
    # Descargar Skills
    skills_res = client.table("skills").select("*").execute()
    df_skills = pd.DataFrame(skills_res.data)

    print(f"📊 Registros recuperados: {len(df_jobs)} jobs y {len(df_skills)} skills.")
    return df_jobs, df_skills

# ---------------------------------------------------
# 🔼 ACTUALIZACIÓN (UPSERT)
# ---------------------------------------------------
def upload_data(df_jobs_clean, df_skills_clean):
    """Sube los datos limpios a Supabase usando UPSERT"""
    
    # 1. Actualizar Jobs
    if not df_jobs_clean.empty:
        print(f"⬆️ Actualizando {len(df_jobs_clean)} jobs...")
        records = df_jobs_clean.to_dict(orient="records")
        # El on_conflict='job_id' es vital para no duplicar entradas
        client.table("jobs").upsert(records, on_conflict="job_id").execute()
        print("✅ Jobs actualizados correctamente.")

    # 2. Actualizar Skills (vinculadas a los jobs existentes)
    if not df_skills_clean.empty:
        print(f"⬆️ Actualizando {len(df_skills_clean)} skills...")
        # Filtrar solo skills cuyos job_id existen en nuestra lista limpia de jobs
        valid_ids = set(df_jobs_clean['job_id'])
        df_skills_filtered = df_skills_clean[df_skills_clean['job_id'].isin(valid_ids)]
        
        records_skills = df_skills_filtered.to_dict(orient="records")
        # Requiere un constraint único en Supabase para (job_id, skill_name)
        client.table("skills").upsert(records_skills, on_conflict="job_id,skill_name").execute()
        print(f"✅ {len(df_skills_filtered)} skills actualizadas.")
        
# ---------------------------------------------------
# 🚀 LIMPIEZA DE REGISTROS ANTIGUOS
# ---------------------------------------------------
        
def delete_old_jobs(days=30):
    """
    Borra registros más antiguos que N días para ahorrar espacio en Supabase.
    """
    from datetime import datetime, timedelta
    
    # Calculamos la fecha límite
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    print(f"🧹 Buscando vacantes publicadas antes de: {cutoff_date}")
    
    try:
        # Filtramos por scraped_at menor a la fecha de corte
        response = client.table("jobs").delete().lt("scraped_at", cutoff_date).execute()
        
        # En la respuesta viene la lista de lo que se borró
        num_deleted = len(response.data) if response.data else 0
        print(f"✅ Se han eliminado {num_deleted} registros antiguos.")
    except Exception as e:
        print(f"❌ Error al intentar purgar datos antiguos: {e}")

# ---------------------------------------------------
# 🚀 PROCESO PRINCIPAL (MAIN)
# ---------------------------------------------------
def run_etl():
    delete_old_jobs(days=30)  # Opcional: borrar datos más viejos a 30 días
    # 1. Cargar
    df_jobs, df_skills = load_raw_data()
    
    if df_jobs.empty:
        print("⚠️ No hay datos en la tabla 'jobs' para procesar.")
        return

    # 2. Limpiar (Usando la lógica de cleaning.py)
    print("\n🧹 Iniciando limpieza de datos...")
    df_jobs_clean = clean_job_data(df_jobs)
    
    # 3. Subir
    upload_data(df_jobs_clean, df_skills)
    
    print("\n🎯 Proceso ETL finalizado con éxito.")

if __name__ == "__main__":
    run_etl()