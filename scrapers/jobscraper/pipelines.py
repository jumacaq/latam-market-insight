# ETL Pipeline for cleaning, normalizing, and storing data
# =============================================================================


import os
#import httpx
import re
import hashlib
from datetime import datetime


from supabase import create_client
from bs4 import BeautifulSoup


from dotenv import load_dotenv

load_dotenv()





class CleaningPipeline:
    """Basic cleaning & validation before inserting into Supabase.
       Deep cleaning is performed later in ETL stage.
    """

    def process_item(self, item, spider):
        # Stable job_id for deduplication
        if not item.get("job_id"):
            item["job_id"] = self.generate_job_id(item)
            
        # --- Normalize minimal required fields ---
        item['title'] = self.clean_text(item.get('title'))
        item['company_name'] = self.clean_text(item.get('company_name'))
        item['location'] = self.clean_text(item.get('location'))
        raw_description = item.get('description')
        if raw_description:
            item['description'] = self.clean_html(raw_description)

        #if not item.get("country"):
            #item['country'] = self.extract_country(item.get('location'))

        # Timestamp
        item['scraped_at'] = datetime.now().isoformat()

        
        
        #)
        # Estos campos viajan vacíos, el ETL en Pandas los llenará luego
        item['country'] = None
        item['seniority_level'] = None
        item['salary_min'] = None
        item['salary_max'] = None
        return item

    # -------- BASIC HELPERS: no normalización avanzada aquí -------- #
    @staticmethod
    def clean_text(t):
        if not t:
            return None
        #t = re.sub(r"\s+", " ", t)
        t = t.replace("\u200b", "")
        return re.sub(r"\s+", " ", t).strip()
    

    @staticmethod
    def clean_html(html):
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        # Específico para LinkedIn: Quitar botones de "Ver más" y avisos de privacidad
        for extra in soup.select('.show-more-less-html__button, .ad-banner-container'):
            extra.decompose()
        #text = soup.get_text(separator=" ")
        for junk in soup(["script", "style", "nav", "svg", "button", "header", "footer"]):
            junk.decompose()
        text = soup.get_text(separator=" ")
        return re.sub(r"\s+", " ", text).strip()

    

    @staticmethod
    def generate_job_id(item):
        """Stable ID based on source_url (best), or fallback."""
        base = (
            f"{item.get('source_platform','')}"
            f"{item.get('title','')}"
            f"{item.get('company_name','')}"
            f"{item.get('location','')}"
        ).lower().strip()
        return hashlib.md5(base.encode()).hexdigest()
    


class SkillExtractionPipeline:
    """Extract technical skills from job descriptions"""
    
    TECH_SKILLS = [
        # Programming Languages
        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift',
        'Kotlin', 'TypeScript', 'R', 'Scala', 'Perl',
        
        # Frameworks & Libraries
        'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'FastAPI', 
        'Spring Boot', 'Express.js', 'Next.js', 'React Native', 'Flutter',
        
        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 
        'DynamoDB', 'Oracle', 'SQL Server',
        
        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI',
        'Terraform', 'Ansible', 'CI/CD',
        
        # Data & AI
        'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Pandas',
        'NumPy', 'Scikit-learn', 'Power BI', 'Tableau', 'Data Analysis',
        
        # Others
        'Git', 'Linux', 'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum'
    ]
    
    def process_item(self, item, spider):
        #description = item.get('description', '') + ' ' + item.get('requirements', '')
        full_text = f"{item.get('description') or ''} {item.get('requirements') or ''}"
        item['skills'] = self.extract_skills(full_text)
        #item['skills'] = extracted_skills
        return item
    
    def extract_skills(self, text):
        """Extract skills from text using keyword matching"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.TECH_SKILLS:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates


class SectorClassificationPipeline:
    """Classify jobs into sectors based on keywords"""
    
    
    SECTOR_KEYWORDS = {
        'EdTech': [
            'education', 'learning', 'edtech', 'e-learning', 'training', 'course', 
            'student', 'school', 'university', 'educación', 'aprendizaje', 'docente',
            'k-12', 'mooc', 'bootcamp', 'lms', 'canvas', 'moodle', 'blackboard', 
            'academia', 'pedagogía', 'instruccional', 'capacitación', 'tutor'
        ],
        'Fintech': [
            'fintech', 'financial', 'payment', 'banking', 'crypto', 'blockchain', 'bank',
            'trading', 'wallet', 'banco', 'finanzas', 'pagos', 'neobank', 'lending', 'tasa',
            'remesas', 'wealthtech', 'insurtech', 'cooperativa', 'crédito', 'inversión',
            'divisas', 'pasmarela', 'stripe', 'mercadopago', 'bitcoin', 'ether', 'defi'
        ],
        'AI & Machine Learning': [
            'ai', 'artificial intelligence', 'machine learning', 'deep learning', 'nlp', 
            'llm', 'generative ai', 'ia', 'inteligencia artificial', 'openai', 'pytorch', 
            'tensorflow', 'neural networks', 'data scientist', 'computer vision',
            'mlops', 'langchain', 'huggingface', 'genai', 'predictive', 'modelado',
            'algoritmos', 'chatgpt', 'llama', 'anthropic', 'data science'
        ],
        'E-commerce': [
            'ecommerce', 'e-commerce', 'retail', 'marketplace', 'shopify', 'magento', 
            'comercio electrónico', 'ventas online', 'logistics', 'carrito de compras',
            'b2c', 'b2b', 'dropshipping', 'vtex', 'woocommerce', 'pos', 'pasarela de pagos',
            'catálogo', 'inventario', 'shipping', 'last mile', 'minorista'
        ],
        'Cybersecurity': [
            'cybersecurity', 'ciberseguridad', 'security', 'infosec', 'pentesting', 
            'hacking', 'firewall', 'vulnerability', 'soc', 'seguridad informática',
            'siem', 'iam', 'zero trust', 'encriptación', 'malware', 'antivirus', 
            'threat intelligence', 'iso 27001', 'forensic', 'red team', 'blue team'
        ],
        'Future of Work': [
            'hrtech', 'remote work', 'collaboration tool', 'workplace digital', 
            'talent management', 'recruitment tech', 'nomad', 'asynchronous', 
            'coworking', 'human resources', 'recursos humanos', 'applicant tracking',
            'ats', 'gig economy', 'freelance', 'staffing'
        ],
        'HealthTech': [
            'healthtech', 'salud', 'medical', 'hospital', 'pharma', 'biotech', 
            'telemedicina', 'farma', 'medicina', 'biotecnología', 'clínica', 
            'paciente', 'historia clínica', 'digital health', 'e-health', 'wellness',
            'fitness', 'biomédica', 'laboratorio', 'diagnóstico'
        ],
    }
    def process_item(self, item, spider):
        if not item.get('sector'):
            item['sector'] = self.classify_sector(item)
        return item
    
    def classify_sector(self, item):
        """Classify job into a sector"""
        text = (
            str(item.get('title') or '') + ' ' + 
            str(item.get('description') or '') + ' ' + 
            str(item.get('company_name') or '')
        ).lower()
        
        # Sistema de puntuación para mayor precisión
        scores = {sector: 0 for sector in self.SECTOR_KEYWORDS.keys()}
        
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            for keyword in keywords:
                # Usamos expresiones regulares para buscar la palabra exacta (\b)
                # Esto evita que 'ia' coincida con 'ingenieria'
                pattern = rf'\b{re.escape(keyword.lower())}\b'
                matches = re.findall(pattern, text)
                scores[sector] += len(matches)
        
        # Encontrar el sector con la puntuación más alta
        if any(scores.values()):
            best_sector = max(scores, key=scores.get)
            # Solo retornamos si el sector ganador tiene al menos una coincidencia clara
            if scores[best_sector] > 0:
                return best_sector
        
        return 'Other'


class SupabasePipeline:
    """Store cleaned data in Supabase"""
    
    def __init__(self):
        self.client = None
    
    def open_spider(self, spider):
        """Initialize Supabase connection"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            spider.logger.error("Supabase credentials not found in environment variables")
            return
        

        self.client = create_client(
            supabase_url,
            supabase_service_key,
            
        )

        spider.logger.info("Connected to Supabase ")
        
    def process_item(self, item, spider):
        """Insert or update job in database"""
        if not self.client:
            spider.logger.error("Supabase client not initialized")
            return item
        
        try:
            # Prepare job data
            job_data = {k: v for k, v in dict(item).items() if k != 'skills'}
            self.client.table('jobs').upsert(job_data, on_conflict='job_id').execute()
            
            
           
            # Insert skills
            if item.get('skills'):
                skill_rows = []
                for s in item['skills']:
                    skill_rows.append({
                        "job_id": item["job_id"],
                        "skill_name": s,
                        "skill_category": "Pending ETL" # Se categorizará en el ETL
                    })

                self.client.table("skills").upsert(
                    skill_rows,
                    on_conflict="job_id,skill_name"
                ).execute()
                
            
            spider.logger.info(f"Saved job: {item.get('title')} at {item.get('company_name')}")
            
        except Exception as e:
            spider.logger.error(f"Error saving to Supabase: {str(e)}")
        
        return item
    
    @staticmethod
    def categorize_skill(skill):
        """Categorize skills"""
        programming = ['Python', 'JavaScript', 'Java', 'C++', 'Ruby', 'PHP', 'Go']
        frameworks = ['React', 'Angular', 'Django', 'Flask', 'Node.js', 'Spring Boot']
        databases = ['SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis']
        cloud = ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes']
        
        if skill in programming:
            return 'Programming Language'
        elif skill in frameworks:
            return 'Framework'
        elif skill in databases:
            return 'Database'
        elif skill in cloud:
            return 'Cloud/DevOps'
        else:
            return 'Other'
    
    def close_spider(self, spider):
        """Cleanup on spider close"""
        spider.logger.info("Closing Supabase connection")
