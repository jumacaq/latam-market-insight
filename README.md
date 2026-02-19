# 📊 LatAm Tech Market Intelligence MVP
Pipeline automatizado de Scraping y Análisis de Datos en tiempo real para el mercado laboral tecnológico en Latinoamérica.

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automatización-blue?logo=githubactions)](https://github.com/tu-usuario/tu-repo/actions)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)](https://latam-marketscraper-dashboard.streamlit.app/)
[![Supabase](https://img.shields.io/badge/Supabase-Base_de_Datos-green?logo=supabase)](https://supabase.com)

---

## 📋 Tabla de Contenidos
1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Pipeline de Datos e Inteligencia](#pipeline-de-datos-e-inteligencia)
5. [Funcionalidades del Dashboard](#funcionalidades-del-dashboard)
6. [Requisitos Previos](#requisitos-previos)
7. [Instalación y Configuración](#instalación-y-configuración)
8. [Ejecución del Sistema](#ejecución-del-sistema)
9. [Despliegue](#despliegue)
10. [Flujo de Trabajo del Equipo](#flujo-de-trabajo-del-equipo)
11. [Solución de Problemas](#solución-de-problemas)
12. [Métricas de Éxito](#métricas-de-éxito)
13. [Recursos de Aprendizaje](#recursos-de-aprendizaje)
14. [Próximos Pasos](#próximos-pasos)

---

## Descripción del Proyecto

Este MVP proporciona una visión analítica del mercado laboral tech en LATAM. No solo recolecta vacantes, sino que analiza la transparencia salarial y la demanda por sectores específicos, ayudando a profesionales a tomar decisiones basadas en datos reales.

**Objetivo:** Procesar 500+ registros diarios con foco en México, Colombia, Argentina, Chile, Perú y Ecuador.

**Propuesta de Valor:** Ayudar a entender la demanda del mercado, roles emergentes y habilidades requeridas en el sector tecnológico latinoamericano.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────┐
│     GitHub Actions (Diario 6 AM UTC)        │
│          Automatización Programada          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         Scrapy Spiders (3 fuentes)          │
│  • GetonBoard  • Torre API  • Computrabajo  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          Pipeline ETL (4 etapas)            │
│  Limpiar → Extraer Skills → Clasificar → Guardar │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│        Supabase (PostgreSQL)                │
│   Tablas: jobs, companies, skills, trends   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│    Streamlit Dashboard (Tiempo Real)        │
│  Visualizaciones, Reportes, Exportación     │
└─────────────────────────────────────────────┘
```

---

## Estructura del Proyecto

```
latam-job-intelligence/
├── .github/
│   └── workflows/
│       └── scrape_daily.yml          # Programador GitHub Actions
├── scrapers/
│   ├── __init__.py
│   ├── scrapy.cfg
│   └── jobscraper/
│       ├── __init__.py
│       ├── settings.py               # Configuración de Scrapy
│       ├── items.py                  # Modelos de datos
│       ├── pipelines.py              # ETL e inserción en BD
│       └── spiders/
│           ├── __init__.py
│           ├── getonboard_spider.py  # Scraper GetonBoard
│           ├── computrabajo_spider.py # Scraper Computrabajo
│           └── linkedin_spider.py    # Scraper LinkedIn
├── etl/
│   ├── __init__.py
│   ├── cleaning.py                   # Funciones de limpieza
│   └── update_data.py                # Estandarización
├── database/
│   ├── __init__.py
│   ├── schema.sql                    # Esquema de base de datos
│   └── queries.py                    # Consultas frecuentes
├── config/
│   └── config.yaml                   # Configuración general
├── app.py                            # App principal de Streamlit
├── .env.example                      # Plantilla de variables de entorno
├── .gitignore
├── README.md
├── requirements.txt
└── requirements_scraper.txt
```

---

## Pipeline de Datos e Inteligencia

El sistema procesa cada vacante a través de un pipeline de limpieza y clasificación de 4 etapas:

- **Limpieza (ETL):** Normalización de salarios, eliminación de HTML y manejo de duplicados.
- **Clasificación por Sector:** Motor de reglas basado en keywords para categorizar vacantes en *Fintech, EdTech, AI & Machine Learning*, entre otros.
- **Extracción de Skills:** Identificación automática de tecnologías y habilidades requeridas por vacante.
- **Auditoría de Calidad:** Cálculo de un *Data Quality Score* basado en la completitud de la información (descripción, salario, requisitos).

---

## Funcionalidades del Dashboard

- **Distribución por Sector:** Identificación inteligente de industrias (Fintech, EdTech, IA).
- **Quality Score:** Análisis de completitud de datos por plataforma.
- **Geolocalización:** Mapa de calor de vacantes por país en LATAM.

---

## Requisitos Previos

### Cuentas necesarias (¡todas gratuitas!)
1. **GitHub** — Para alojar el código y automatizar la ejecución.
2. **Supabase** — Base de datos PostgreSQL (500MB en plan gratuito).
3. **Streamlit Cloud** — Hosting del dashboard.

### Requisitos locales
- Python 3.9 o superior
- Git
- Editor de código (VS Code recomendado)
- Acceso a terminal

---

## Instalación y Configuración

### Fase 1: Configuración del Entorno Local

#### 1. Clonar y configurar el proyecto
```bash
# Crear directorio del proyecto
mkdir latam-job-intelligence
cd latam-job-intelligence

# Inicializar git
git init

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate

# Crear estructura de carpetas
mkdir -p scrapers/jobscraper/spiders
mkdir -p etl database analysis dashboard/pages config notebooks tests
mkdir -p .github/workflows
```

#### 2. Instalar dependencias
Crear `requirements.txt`:
```txt
scrapy==2.11.0
beautifulsoup4==4.12.2
selenium==4.15.2
requests==2.31.0
supabase==2.3.0
python-dotenv==1.0.0
pandas==2.1.4
numpy==1.26.2
plotly==5.18.0
streamlit==1.29.0
pyyaml==6.0.1
fake-useragent==1.4.0
python-dateutil==2.8.2
```

Instalar:
```bash
pip install -r requirements.txt
```

#### 3. Configurar variables de entorno
Crear archivo `.env`:
```env
SUPABASE_URL=tu_supabase_url_aqui
SUPABASE_KEY=tu_supabase_anon_key_aqui
```

Crear `.env.example` (para el equipo):
```env
SUPABASE_URL=
SUPABASE_KEY=
```

#### 4. Crear `.gitignore`
```
# Python
__pycache__/
*.py[cod]
*$py.class
venv/
*.egg-info/

# Variables de entorno
.env

# Scrapy
.scrapy/
httpcache/

# IDE
.vscode/
.idea/

# Logs
*.log
scraper.log

# Datos
*.csv
*.json
data/
```

---

### Fase 2: Configuración de la Base de Datos

#### 1. Crear proyecto en Supabase
1. Ir a [https://supabase.com](https://supabase.com) e iniciar sesión con GitHub.
2. Hacer clic en **New Project** y completar:
   - **Name**: latam-job-intelligence
   - **Database Password**: (guardar en lugar seguro)
   - **Region**: US East (más cercana a LATAM)
3. Esperar 2-3 minutos hasta que el proyecto esté listo.

#### 2. Ejecutar el esquema de base de datos
1. En el dashboard de Supabase, ir a **SQL Editor**.
2. Copiar el contenido de `database/schema.sql` y ejecutarlo.
3. Verificar que las tablas se hayan creado en **Table Editor**.

#### 3. Obtener credenciales
1. Ir a **Project Settings** → **API**.
2. Copiar:
   - **Project URL** (ej: `https://xxxxx.supabase.co`)
   - **anon public key** (cadena larga que empieza con `eyJ...`)
3. Agregar ambos valores al archivo `.env`.

#### 4. Probar la conexión
Crear `test_connection.py`:
```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

client = create_client(url, key)
response = client.table('jobs').select('*').limit(1).execute()

print("✅ Conexión exitosa!" if response else "❌ Conexión fallida")
```

Ejecutar:
```bash
python test_connection.py
```

---

### Fase 3: Configuración de Scrapy

#### 1. Inicializar el proyecto Scrapy
```bash
cd scrapers
scrapy startproject jobscraper
cd jobscraper
```

#### 2. Agregar los archivos del proyecto
Asegurarse de que los siguientes archivos estén en su lugar:
- `items.py` — Modelos de datos
- `pipelines.py` — Lógica ETL
- `settings.py` — Configuración de Scrapy
- `spiders/getonboard_spider.py`
- `spiders/computrabajo_spider.py`
- `spiders/linkedin_spider.py`

#### 3. Probar un spider
```bash
# Probar spider de GetonBoard
scrapy crawl getonboard -o test_output.json

# Verificar resultado
cat test_output.json
```

Resultado esperado: array JSON con datos de vacantes.

---

### Fase 4: Configuración del Dashboard

#### 1. Probar el dashboard localmente
```bash
streamlit run app.py
```

Se abrirá el navegador en `http://localhost:8501`.

> **Nota:** El dashboard puede mostrar "sin datos" si los scrapers aún no han corrido.

---

### Fase 5: Configuración de la Automatización

#### 1. Verificar el workflow de GitHub Actions
El archivo `.github/workflows/scrape_daily.yml` ya contiene la programación diaria a las 6:00 AM UTC.

#### 2. Probar la ejecución localmente
```bash
python run_scraper.py
```

Esto ejecutará los tres scrapers de forma secuencial.

---

## Ejecución del Sistema

### Desarrollo Local

#### Ejecutar un spider individual
```bash
cd scrapers/jobscraper
scrapy crawl getonboard
```

#### Ejecutar todos los scrapers
```bash
python run_scraper.py
```

#### Generar reporte
```bash
python analysis/report_generator.py
```

#### Iniciar el dashboard
```bash
streamlit run app.py
```

---

## Despliegue

### 1. Subir el proyecto a GitHub

```bash
git add .
git commit -m "Initial commit: LatAm Job Intelligence MVP"
git remote add origin https://github.com/TU-USUARIO/latam-job-intelligence.git
git push -u origin main
```

### 2. Configurar secretos en GitHub

1. Ir al repositorio → **Settings** → **Secrets and variables** → **Actions**.
2. Agregar los siguientes secretos:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

### 3. Activar GitHub Actions

1. Ir a la pestaña **Actions** del repositorio.
2. Verificar que el workflow **Daily Job Scraping** esté visible.
3. Hacer clic en **Enable workflow**.
4. Opcionalmente, ejecutar manualmente con **Run workflow** para una prueba inmediata.

> **Programación:** Se ejecuta automáticamente todos los días a las 6:00 AM UTC (1-3 AM hora LATAM).

### 4. Desplegar el Dashboard en Streamlit Cloud

1. Ir a [https://streamlit.io/cloud](https://streamlit.io/cloud) e iniciar sesión con GitHub.
2. Hacer clic en **New app** y seleccionar:
   - **Repository**: tu-usuario/latam-job-intelligence
   - **Branch**: main
   - **Main file**: app.py
3. En **Advanced settings**, agregar los secretos `SUPABASE_URL` y `SUPABASE_KEY`.
4. Hacer clic en **Deploy**.

**Resultado:** El dashboard quedará disponible en `https://tu-app.streamlit.app`.

---

## Flujo de Trabajo del Equipo

### Operaciones Diarias

1. **Scraping automatizado:** Se ejecuta diariamente vía GitHub Actions.
2. **Actualización de datos:** Fluye automáticamente hacia Supabase.
3. **Dashboard:** Se actualiza al refrescar el navegador.
4. **Monitoreo:** Revisar logs en la pestaña Actions de GitHub.

### Roles del Equipo

#### Desarrollador 1 — Spiders y ETL
- Mantener el código de los scrapers.
- Corregir scrapers que fallen.
- Agregar nuevas fuentes de datos.
- Mejorar la lógica de extracción.

#### Desarrollador 2 — Datos y Análisis
- Monitorear la calidad de los datos.
- Crear notebooks de análisis.
- Generar insights del mercado.
- Actualizar algoritmos de tendencias.

#### Desarrollador 3 — Dashboard y Reportes
- Mejorar las visualizaciones.
- Agregar nuevas funcionalidades al dashboard.
- Generar reportes semanales.
- Mejorar la experiencia de usuario.

### Rutina Semanal

**Lunes:** Revisar logs del fin de semana, verificar métricas de calidad y planificar mejoras de la semana.

**Miércoles:** Análisis de datos a mitad de semana, prueba de nuevas funcionalidades en local y actualización de documentación.

**Viernes:** Despliegue de mejoras, generación del reporte semanal y sesión de conocimiento compartido del equipo.

---

## Solución de Problemas

### Scrapers con errores
```bash
# Revisar logs
cat scraper.log

# Probar spider en modo detallado
scrapy crawl getonboard -L DEBUG

# Inspeccionar la estructura del sitio
scrapy shell "https://www.getonbrd.com/jobs"
```

**Solución:** Actualizar los selectores CSS en el código del spider si la estructura del sitio cambió.

---

### Error de conexión a la base de datos
```bash
# Probar conexión
python test_connection.py

# Verificar credenciales
cat .env
```

**Solución:** Confirmar que la URL y la clave de Supabase sean correctas.

---

### GitHub Actions con errores
1. Ir a la pestaña **Actions** y hacer clic en el workflow fallido.
2. Revisar los logs del error.
3. Causas más comunes:
   - Los secretos no están configurados correctamente.
   - El `requirements.txt` está incompleto.
   - La estructura del proyecto Scrapy tiene inconsistencias.

---

### Dashboard sin datos
```bash
# Verificar datos en Supabase
# Ir a Supabase → Table Editor → tabla jobs

# Probar localmente
streamlit run app.py
```

**Solución:** Ejecutar los scrapers primero si la tabla aún no tiene datos.

---

## Métricas de Éxito

| Métrica | Objetivo |
|---|---|
| Vacantes procesadas | 500+ por semana |
| Países cubiertos | 3+ (MX, CO, AR, CL, PE, EC) |
| Sectores clasificados | 3+ (EdTech, Fintech, IA) |
| Skills extraídas | 50+ |
| Uptime GitHub Actions | 95%+ |
| Frecuencia de actualización | Diaria |

---

## Recursos de Aprendizaje

**Scrapy**
- [Documentación oficial](https://docs.scrapy.org/)
- [Tutorial introductorio](https://docs.scrapy.org/en/latest/intro/tutorial.html)

**Supabase**
- [Guía de inicio rápido](https://supabase.com/docs/guides/getting-started)
- [Cliente Python](https://supabase.com/docs/reference/python/introduction)

**Streamlit**
- [Primeros pasos](https://docs.streamlit.io/library/get-started)
- [Galería de ejemplos](https://streamlit.io/gallery)

---

## Próximos Pasos

1. Agregar notificaciones por email con reportes diarios automáticos.
2. Implementar modelo de ML para predicción de salarios.
3. Integrar fuentes adicionales de empleo (alternativas a LinkedIn API).
4. Crear dashboard responsive para móviles.
5. Agregar autenticación de usuarios para insights personalizados.
6. Implementar algoritmo de matching entre perfiles y vacantes.

---

## 📞 Soporte

- **Issues:** Crear un issue en el repositorio de GitHub.
- **Preguntas:** Canal de Slack del equipo.
- **Documentación adicional:** Carpeta `docs/` del repositorio.

---

## 📄 Licencia

Este proyecto fue desarrollado con fines educativos como parte de una simulación laboral en tecnología.

---

**Construido con ❤️ para el Talento Tech de LATAM**

*Última actualización: Febrero 2026*