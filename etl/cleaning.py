import re
import pandas as pd

# ----------------------------------------------
# 1. FUNCIONES DE APOYO (MANTENER)
# ----------------------------------------------
def clean_text(t):
    if not t:
        return None
    # Elimina espacios múltiples y caracteres invisibles
    t = re.sub(r"\s+", " ", str(t))
    t = t.replace("\u200b", "")
    return t.strip()

# 1. Diccionario expandido con ciudades clave para mejorar la detección
COUNTRY_MAP = {
    "méxico": "Mexico", "mexico": "Mexico", "cdmx": "Mexico", "guadalajara": "Mexico", "monterrey": "Mexico",
    "perú": "Peru", "peru": "Peru", "lima": "Peru", "ate": "Peru",
    "chile": "Chile", "santiago": "Chile", "concepción": "Chile", "viña del mar": "Chile", "rancagua": "Chile",
    "argentina": "Argentina", "buenos aires": "Argentina", "caba": "Argentina", "córdoba": "Argentina", "rosario": "Argentina",
    "colombia": "Colombia", "bogotá": "Colombia", "bogota": "Colombia", "medellín": "Colombia", "medellin": "Colombia",
    "ecuador": "Ecuador", "quito": "Ecuador", "guayaquil": "Ecuador",
    "venezuela": "Venezuela", "caracas": "Venezuela",
    "uruguay": "Uruguay", "montevideo": "Uruguay",
    "costa rica": "Costa Rica", "san josé": "Costa Rica",
    "dominicana": "Dominican Republic", "santo domingo": "Dominican Republic",
    "latam": "Latam/Remote", "remote": "Latam/Remote", "remoto": "Latam/Remote"
}

def normalize_location(row):
    url = str(row.get('source_url', '')).lower()
    loc = str(row.get('location', '')).lower()
    desc = str(row.get('description', '')).lower()

    # PRIORIDAD 1: Prefijos de URL (Efectivo para Computrabajo y LinkedIn)
    if 'ar.computrabajo' in url or 'ar.linkedin' in url: return 'Argentina'
    if 'mx.computrabajo' in url or 'mx.linkedin' in url: return 'Mexico'
    if 'co.computrabajo' in url or 'co.linkedin' in url: return 'Colombia'
    if 'pe.computrabajo' in url or 'pe.linkedin' in url: return 'Peru'
    if 'cl.computrabajo' in url or 'cl.linkedin' in url: return 'Chile'
    if 'ec.computrabajo' in url or 'uy.linkedin' in url: return 'Ecuador'

    # PRIORIDAD 2: Buscar en el campo Location (Si el spider capturó algo)
    #if loc and loc != 'none' and loc != '':
        #for keyword, country in COUNTRY_MAP.items():
            #if keyword in loc:
                #return country
    combined_text = f"{loc} {desc}"
    # PRIORIDAD 3: Buscar en la Descripción (Efectivo para GetOnBoard)
    # Buscamos primero ciudades (que son más específicas) y luego países
    #if desc and desc != 'none':
    for keyword, country in COUNTRY_MAP.items():
         # Usamos regex para buscar la palabra exacta y evitar que "peru" matchee con "operaciones"
        if re.search(rf'\b{keyword}\b', combined_text,re.IGNORECASE):
            return country

    return 'Latam/Remote'

# ----------------------------------------------
# 2. LÓGICA DE TRANSFORMACIÓN (CONSOLIDADA)
# ----------------------------------------------
def clean_job_data(df):
    """
    Función maestra que aplica toda la lógica de transformación.
    Reemplaza a cualquier intento manual previo.
    """
    # A. Separar Título y Empresa (Caso GetOnBoard: "Cargo in Empresa")
    def split_title_company(row):
        title = str(row['title'])
        if ' in ' in title:
            parts = title.split(' in ')
            return parts[0].strip(), parts[1].strip()
        return title, row['company_name']

    df[['title', 'company_name']] = df.apply(
        lambda r: pd.Series(split_title_company(r)), axis=1
    )

    # B. Normalizar Seniority desde el Título
    def get_seniority(title):
        title = title.lower()
        if any(x in title for x in ['sr', 'senior', 'lead', 'experto', 'lider']): return 'Senior'
        if any(x in title for x in ['jr', 'junior', 'practicante', 'egresado', 'intern']): return 'Junior'
        return 'Mid'

    df['seniority_level'] = df['title'].apply(get_seniority)

    # C. Limpiar Emojis y caracteres extraños en Títulos (🚀, ✅, etc)
    df['title'] = df['title'].apply(lambda x: re.sub(r'[^\w\s\-]', '', str(x)).strip())

    # D. Limpieza general de textos y normalización de país
    df["title"] = df["title"].apply(clean_text)
    df["company_name"] = df["company_name"].apply(clean_text)
    df["location"] = df["location"].apply(clean_text)
    df["description"] = df["description"].apply(clean_text)
    
    # Inferencia de país basada en la ubicación
    df["country"] = df.apply(normalize_location, axis=1)

    # E. Deduplicación y limpieza final
    df = df.drop_duplicates(subset=["job_id"], keep="last")
    df = df[df["title"].notna() & (df["title"] != "")]
    
    return df