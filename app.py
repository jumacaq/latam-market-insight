import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import Counter
import re

# ========================================
# 1. CONFIGURACIÓN INICIAL
# ========================================
st.set_page_config(
    page_title="Tech Job Market Analyzer", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)
load_dotenv()

# ========================================
# 2. CONEXIÓN A SUPABASE
# ========================================
@st.cache_resource
def init_connection():
    try:
        # Streamlit Cloud: usa st.secrets
        # Local: usa .env
        if "SUPABASE_URL" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_SERVICE_KEY"]
        else:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_SERVICE_KEY")
        
        # Validaciones
        if not url or not key:
            st.error("❌ Credenciales no configuradas")
            st.info("📌 Streamlit Cloud: Settings → Secrets")
            st.info("📌 Local: crear archivo .env")
            st.stop()
        
        if not url.startswith("https://"):
            st.error(f"❌ URL debe empezar con https://")
            st.stop()
        
        if len(key) < 100:
            st.error(f"❌ SERVICE_KEY inválida (muy corta: {len(key)} chars)")
            st.stop()
        
        # IMPORTANTE: Crear cliente SIN parámetros opcionales problemáticos
        return create_client(
            supabase_url=url,
            supabase_key=key
        )
        
    except Exception as e:
        st.error(f"❌ Error: {type(e).__name__}")
        st.code(str(e))
        st.stop()

supabase = init_connection()

# ========================================
# 3. CARGA DE DATOS
# ========================================
@st.cache_data(ttl=600)
def load_data():
    res = supabase.table("jobs").select("*, skills(skill_name)").execute()
    df = pd.DataFrame(res.data)
    
    if df.empty:
        return df

    # Convertir fechas
    df['scraped_at'] = pd.to_datetime(df['scraped_at']).dt.tz_localize(None)
    
    # Limpiar y normalizar datos
    df['country'] = df['country'].fillna('Latam/Remote').astype(str).str.strip()
    df['seniority_level'] = df['seniority_level'].fillna('Mid').astype(str).str.strip()
    df['source_platform'] = df['source_platform'].fillna('Web').astype(str).str.strip()
    df['sector'] = df['sector'].fillna('Other').astype(str).str.strip()
    
    # Crear columna de salario disponible
    df['has_salary'] = df['salary_range'].notna() & (df['salary_range'] != 'A convenir')
    
    return df

# ========================================
# 4. FUNCIONES DE ANÁLISIS
# ========================================
def extract_keywords_from_descriptions(df):
    """Extrae keywords técnicas de descripciones"""
    tech_keywords = [
        'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node',
        'django', 'flask', 'fastapi', 'sql', 'postgresql', 'mysql', 'mongodb',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'ci/cd',
        'machine learning', 'ai', 'data science', 'typescript', 'golang',
        'ruby', 'php', 'laravel', 'symfony', '.net', 'c#', 'c++',
        'tensorflow', 'pytorch', 'pandas', 'numpy', 'spark', 'kafka',
        'redis', 'elasticsearch', 'nginx', 'apache', 'linux', 'terraform',
        'ansible', 'jenkins', 'grafana', 'prometheus'
    ]
    
    keyword_counter = Counter()
    
    # Solo para plataformas con descripciones
    df_with_desc = df[
        (df['description'].notna()) & 
        (df['description'] != 'Descripción no disponible.')
    ]
    
    for desc in df_with_desc['description']:
        desc_lower = str(desc).lower()
        for keyword in tech_keywords:
            if keyword in desc_lower:
                keyword_counter[keyword] += 1
    
    return keyword_counter

def get_platform_quality_score(df):
    """Calcula score de calidad por plataforma"""
    quality_metrics = []
    
    for platform in df['source_platform'].unique():
        df_platform = df[df['source_platform'] == platform]
        
        desc_available = (
            (df_platform['description'].notna()) & 
            (df_platform['description'] != 'Descripción no disponible.')
        ).sum()
        
        salary_available = df_platform['has_salary'].sum()
        
        quality_score = (
            (desc_available / len(df_platform) * 50) +
            (salary_available / len(df_platform) * 50)
        )
        
        quality_metrics.append({
            'platform': platform,
            'jobs': len(df_platform),
            'desc_rate': desc_available / len(df_platform) * 100,
            'salary_rate': salary_available / len(df_platform) * 100,
            'quality_score': quality_score
        })
    
    return pd.DataFrame(quality_metrics)

# ========================================
# 5. CARGA DE DATOS
# ========================================
df_raw = load_data()

# ========================================
# 6. SIDEBAR - FILTROS
# ========================================
st.sidebar.header("🔍 Panel de Filtros")

if not df_raw.empty:
    # Filtro de Fecha
    dias = st.sidebar.slider("Días atrás:", 1, 30, 15, key='dias_slider')
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    # Filtro de Países
    opciones_paises = sorted(df_raw['country'].unique().tolist())
    paises_sel = st.sidebar.multiselect(
        "Países", 
        options=opciones_paises,
        default=opciones_paises
    )
    
    # Filtro de Seniority
    opciones_niveles = sorted(df_raw['seniority_level'].unique().tolist())
    niveles_sel = st.sidebar.multiselect(
        "Seniority", 
        options=opciones_niveles,
        default=opciones_niveles
    )
    
    # Filtro de Plataforma
    opciones_plataformas = sorted(df_raw['source_platform'].unique().tolist())
    plataformas_sel = st.sidebar.multiselect(
        "Plataformas",
        options=opciones_plataformas,
        default=opciones_plataformas
    )
    
    # Botón para resetear filtros
    if st.sidebar.button("🔄 Resetear Todo"):
        st.cache_data.clear()
        st.rerun()
    
    # ========================================
    # 7. APLICAR FILTROS
    # ========================================
    df_filtered = df_raw[
        (df_raw['scraped_at'] >= fecha_limite) &
        (df_raw['country'].isin(paises_sel)) &
        (df_raw['seniority_level'].isin(niveles_sel)) &
        (df_raw['source_platform'].isin(plataformas_sel))
    ].copy()
    
    # ========================================
    # 8. PÁGINA PRINCIPAL
    # ========================================
    st.title("🚀 Tech Job Market Intelligence")
    st.caption(f"📅 Viendo ofertas desde: **{fecha_limite.strftime('%d/%m/%Y')}** | Última actualización: {df_raw['scraped_at'].max().strftime('%d/%m/%Y %H:%M')}")
    
    # ========================================
    # 9. MÉTRICAS PRINCIPALES
    # ========================================
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Vacantes", len(df_filtered))
    with col2:
        st.metric("🌎 Países", df_filtered['country'].nunique())
    with col3:
        st.metric("🏢 Empresas", df_filtered['company_name'].nunique())
    with col4:
        with_desc = (
            (df_filtered['description'].notna()) & 
            (df_filtered['description'] != 'Descripción no disponible.')
        ).sum()
        st.metric("📝 Con Descripción", f"{with_desc} ({with_desc/len(df_filtered)*100:.0f}%)")
    with col5:
        with_salary = df_filtered['has_salary'].sum()
        st.metric("💰 Con Salario", f"{with_salary} ({with_salary/len(df_filtered)*100:.0f}%)")
    
    if df_filtered.empty:
        st.warning("⚠️ No hay registros con los filtros seleccionados.")
    else:
        # ========================================
        # 10. TABS CON VISUALIZACIONES
        # ========================================
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🌍 Geografía", 
            "🛠️ Skills & Tech", 
            "💼 Empresas",
            "📈 Calidad de Datos"
        ])
        
        # ========================================
        # TAB 1: OVERVIEW
        # ========================================
        with tab1:
            col_a, col_b = st.columns(2)
            
            with col_a:
                # Distribución por Seniority
                st.subheader("📊 Distribución por Seniority")
                seniority_counts = df_filtered['seniority_level'].value_counts()
                fig_seniority = px.pie(
                    values=seniority_counts.values,
                    names=seniority_counts.index,
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_seniority, use_container_width=True)
            
            with col_b:
                # Distribución por Plataforma
                st.subheader("🌐 Vacantes por Plataforma")
                platform_counts = df_filtered['source_platform'].value_counts()
                fig_platform = px.bar(
                    x=platform_counts.index,
                    y=platform_counts.values,
                    labels={'x': 'Plataforma', 'y': 'Cantidad'},
                    color=platform_counts.values,
                    color_continuous_scale='Viridis'
                )
                fig_platform.update_traces(
                    marker_line_color='rgb(8,48,107)', # Borde azul oscuro
                    marker_line_width=1.5,             # Grosor del borde
                    opacity=0.85                       # Un poco de transparencia para elegancia
                )
                fig_platform.update_layout(showlegend=False)
                st.plotly_chart(fig_platform, use_container_width=True)
            
            # Timeline de publicaciones
            st.subheader("📅 Timeline de Scraping")
            df_timeline = df_filtered.copy()
            df_timeline['fecha'] = df_timeline['scraped_at'].dt.date
            timeline_counts = df_timeline.groupby('fecha').size().reset_index(name='count')
            
            fig_timeline = px.line(
                timeline_counts,
                x='fecha',
                y='count',
                markers=True,
                labels={'fecha': 'Fecha', 'count': 'Vacantes Scrapeadas'}
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            st.subheader("🏭 Distribución por Sector Económico")
            sector_counts = df_filtered['sector'].value_counts()
            fig_sector_total = px.bar(
                sector_counts,
                orientation='h',
                labels={'value': 'Vacantes', 'index': 'Sector'},
                color=sector_counts.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_sector_total, use_container_width=True)
        
        # ========================================
        # TAB 2: GEOGRAFÍA
        # ========================================
        with tab2:
            col_geo1, col_geo2 = st.columns([2, 1])
            
            with col_geo1:
                # Mapa de vacantes por país
                st.subheader("🗺️ Distribución Global")
                country_counts = df_filtered['country'].value_counts().reset_index()
                country_counts.columns = ['country', 'count']
                
                fig_map = px.choropleth(
                    country_counts,
                    locations='country',
                    locationmode='country names',
                    color='count',
                    hover_name='country',
                    color_continuous_scale='Viridis',
                    labels={'count': 'Vacantes'}
                )
                fig_map.update_geos(showcountries=True, showcoastlines=True)
                st.plotly_chart(fig_map, use_container_width=True)
            
            with col_geo2:
                # Top países
                st.subheader("🏆 Top Países")
                st.dataframe(
                    country_counts.head(10),
                    column_config={
                        'country': 'País',
                        'count': st.column_config.ProgressColumn(
                            'Vacantes',
                            format='%d',
                            min_value=0,
                            max_value=int(country_counts['count'].max())
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
            
            # Distribución por sector y país
            st.subheader("🏭 Sectores por País (Top 5)")
            sector_country = df_filtered.groupby(['country', 'sector']).size().reset_index(name='count')
            top_countries = df_filtered['country'].value_counts().head(5).index
            sector_country_top = sector_country[sector_country['country'].isin(top_countries)]
            
            fig_sector = px.bar(
                sector_country_top,
                x='country',
                y='count',
                color='sector',
                barmode='stack',
                labels={'count': 'Vacantes', 'country': 'País', 'sector': 'Sector'}
            )
            st.plotly_chart(fig_sector, use_container_width=True)
        
        # ========================================
        # TAB 3: SKILLS & TECH
        # ========================================
        with tab3:
            col_skills1, col_skills2 = st.columns(2)
            
            with col_skills1:
                # Top Skills (de la relación skills)
                st.subheader("🛠️ Top 15 Skills (Base de Datos)")
                listado_skills = []
                for row in df_filtered['skills']:
                    if isinstance(row, list):
                        for s in row:
                            if 'skill_name' in s:
                                listado_skills.append(s['skill_name'])
                
                if listado_skills:
                    skill_counts = pd.Series(listado_skills).value_counts().head(15)
                    fig_skills = px.bar(
                        x=skill_counts.values,
                        y=skill_counts.index,
                        orientation='h',
                        labels={'x': 'Frecuencia', 'y': 'Skill'},
                        color=skill_counts.values,
                        color_continuous_scale='Teal'
                    )
                    fig_skills.update_layout(showlegend=False, height=500)
                    st.plotly_chart(fig_skills, use_container_width=True)
                else:
                    st.info("No hay skills registradas en la base de datos.")
            
            with col_skills2:
                # Keywords extraídas de descripciones
                st.subheader("🔍 Keywords en Descripciones")
                keyword_counter = extract_keywords_from_descriptions(df_filtered)
                
                if keyword_counter:
                    top_keywords = dict(keyword_counter.most_common(15))
                    fig_keywords = px.bar(
                        x=list(top_keywords.values()),
                        y=list(top_keywords.keys()),
                        orientation='h',
                        labels={'x': 'Menciones', 'y': 'Tecnología'},
                        color=list(top_keywords.values()),
                        color_continuous_scale='Oranges'
                    )
                    fig_keywords.update_layout(showlegend=False, height=500)
                    st.plotly_chart(fig_keywords, use_container_width=True)
                else:
                    st.info("No se encontraron keywords técnicas.")
            
            # Skills por Seniority
            st.subheader("📊 Skills más demandadas por Seniority")
            if listado_skills:
                # Crear dataset expandido
                skills_seniority = []
                for idx, row in df_filtered.iterrows():
                    if isinstance(row['skills'], list):
                        for skill in row['skills']:
                            if 'skill_name' in skill:
                                skills_seniority.append({
                                    'skill': skill['skill_name'],
                                    'seniority': row['seniority_level']
                                })
                
                if skills_seniority:
                    df_skills_sen = pd.DataFrame(skills_seniority)
                    skill_sen_counts = df_skills_sen.groupby(['seniority', 'skill']).size().reset_index(name='count')
                    
                    # Top 5 skills por nivel
                    top_skills_per_level = skill_sen_counts.groupby('seniority').apply(
                        lambda x: x.nlargest(5, 'count')
                    ).reset_index(drop=True)
                    
                    fig_skills_sen = px.bar(
                        top_skills_per_level,
                        x='seniority',
                        y='count',
                        color='skill',
                        barmode='group',
                        labels={'count': 'Frecuencia', 'seniority': 'Nivel', 'skill': 'Skill'}
                    )
                    st.plotly_chart(fig_skills_sen, use_container_width=True)
        
        # ========================================
        # TAB 4: EMPRESAS
        # ========================================
        with tab4:
            col_comp1, col_comp2 = st.columns([2, 1])
            
            with col_comp1:
                # Top 20 empresas
                st.subheader("🏢 Top 20 Empresas Contratando")
                company_counts = df_filtered['company_name'].value_counts().head(20)
                fig_companies = px.bar(
                    x=company_counts.values,
                    y=company_counts.index,
                    orientation='h',
                    labels={'x': 'Vacantes', 'y': 'Empresa'},
                    color=company_counts.values,
                    color_continuous_scale='Sunset'
                )
                fig_companies.update_layout(showlegend=False, height=600)
                st.plotly_chart(fig_companies, use_container_width=True)
            
            with col_comp2:
                # Empresas por seniority
                st.subheader("📊 Perfil de Contratación")
                company_seniority = df_filtered.groupby(
                    ['company_name', 'seniority_level']
                ).size().reset_index(name='count')
                
                top_10_companies = df_filtered['company_name'].value_counts().head(10).index
                company_sen_top = company_seniority[
                    company_seniority['company_name'].isin(top_10_companies)
                ]
                
                fig_comp_sen = px.bar(
                    company_sen_top,
                    x='company_name',
                    y='count',
                    color='seniority_level',
                    barmode='stack',
                    labels={'count': 'Vacantes', 'company_name': 'Empresa'}
                )
                fig_comp_sen.update_xaxes(tickangle=45)
                st.plotly_chart(fig_comp_sen, use_container_width=True)
            
            # Salarios por empresa (solo Computrabajo)
            df_with_salary = df_filtered[df_filtered['has_salary']]
            if not df_with_salary.empty:
                st.subheader("💰 Empresas con Información Salarial")
                st.dataframe(
                    df_with_salary[['company_name', 'title', 'salary_range', 'country']].head(20),
                    use_container_width=True,
                    hide_index=True
                )
        
        # ========================================
        # TAB 5: CALIDAD DE DATOS
        # ========================================
        with tab5:
            st.subheader("📈 Calidad de Datos por Plataforma")
            
            quality_df = get_platform_quality_score(df_filtered)
            
            col_q1, col_q2 = st.columns(2)
            
            with col_q1:
                # Score de calidad
                fig_quality = px.bar(
                    quality_df,
                    x='platform',
                    y='quality_score',
                    text='quality_score',
                    labels={'platform': 'Plataforma', 'quality_score': 'Score de Calidad'},
                    color='quality_score',
                    color_continuous_scale='RdYlGn'
                )
                fig_quality.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                st.plotly_chart(fig_quality, use_container_width=True)
            
            with col_q2:
                # Métricas detalladas
                st.dataframe(
                    quality_df.style.format({
                        'desc_rate': '{:.1f}%',
                        'salary_rate': '{:.1f}%',
                        'quality_score': '{:.1f}%'
                    }),
                    column_config={
                        'platform': 'Plataforma',
                        'jobs': 'Vacantes',
                        'desc_rate': 'Tasa Descripción',
                        'salary_rate': 'Tasa Salario',
                        'quality_score': 'Score Final'
                    },
                    hide_index=True,
                    use_container_width=True
                )
            
            # Comparativa de completitud
            st.subheader("📊 Completitud de Campos por Plataforma")
            completeness_data = []
            for platform in df_filtered['source_platform'].unique():
                df_plat = df_filtered[df_filtered['source_platform'] == platform]
                completeness_data.append({
                    'Plataforma': platform,
                    'Descripción': ((df_plat['description'].notna()) & 
                                   (df_plat['description'] != 'Descripción no disponible.')).sum() / len(df_plat) * 100,
                    'Salario': df_plat['has_salary'].sum() / len(df_plat) * 100,
                    'Requisitos': df_plat['requirements'].notna().sum() / len(df_plat) * 100,
                    'Ubicación': df_plat['location'].notna().sum() / len(df_plat) * 100
                })
            
            df_completeness = pd.DataFrame(completeness_data)
            df_completeness_melted = df_completeness.melt(
                id_vars='Plataforma',
                var_name='Campo',
                value_name='Completitud'
            )
            
            fig_completeness = px.bar(
                df_completeness_melted,
                x='Campo',
                y='Completitud',
                color='Plataforma',
                barmode='group',
                labels={'Completitud': 'Completitud (%)'}
            )
            st.plotly_chart(fig_completeness, use_container_width=True)
        
        # ========================================
        # 11. TABLA DE DATOS
        # ========================================
        st.subheader("📋 Tabla de Vacantes Filtradas")
        
        # Selector de columnas a mostrar
        all_columns = ['title', 'company_name', 'country', 'seniority_level', 
                      'source_platform', 'sector', 'salary_range', 'scraped_at']
        selected_columns = st.multiselect(
            "Selecciona columnas a mostrar:",
            options=all_columns,
            default=['title', 'company_name', 'country', 'seniority_level', 'scraped_at']
        )
        
        if selected_columns:
            st.dataframe(
                df_filtered[selected_columns],
                use_container_width=True,
                hide_index=True,
                height=400
            )
        
        # Botón de descarga
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos filtrados (CSV)",
            data=csv,
            file_name=f'jobs_filtered_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )

else:
    st.error("❌ No se pudo cargar la base de datos. Verifica tu conexión a Supabase.")
    st.stop()

# ========================================
# 12. FOOTER
# ========================================
st.markdown("---")
st.caption("🤖 Dashboard creado con Streamlit | Datos de LinkedIn, Computrabajo y GetonBoard")