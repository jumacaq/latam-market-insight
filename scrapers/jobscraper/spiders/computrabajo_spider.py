# Computrabajo is massive in LatAm (requires careful scraping)
# =============================================================================

import scrapy
from jobscraper.items import JobItem
import re
import datetime


class ComputrabajoSpider(scrapy.Spider):
    name = 'computrabajo'
    allowed_domains = ["computrabajo.com",
        "computrabajo.com.mx",
        "computrabajo.com.co",
        "computrabajo.com.pe",
        "computrabajo.com.ar",
        "computrabajo.com.ec",
        "computrabajo.com.cl"
    ]
    
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 2,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
        }
    }

    
    # Start URLs for different countries
    start_urls = [
        # Mexico - Tech jobs
        'https://mx.computrabajo.com/trabajo-de-programador',
        'https://mx.computrabajo.com/trabajo-de-desarrollador',
        'https://mx.computrabajo.com/trabajo-de-data-scientist',
        # Colombia
        'https://co.computrabajo.com/trabajo-de-programador',
        'https://co.computrabajo.com/trabajo-de-desarrollador',
        'https://co.computrabajo.com/trabajo-de-data-scientist',
    
        # Argentina
        'https://ar.computrabajo.com/trabajo-de-programador',
        'https://ar.computrabajo.com/trabajo-de-desarrollador',
        'https://ar.computrabajo.com/trabajo-de-data-scientist',
    
        # Perú
        'https://pe.computrabajo.com/trabajo-de-programador',
        'https://pe.computrabajo.com/trabajo-de-desarrollador',
        'https://pe.computrabajo.com/trabajo-de-data-scientist',
]
    
    
    
    def parse(self, response):
        """Parsea página de listados de ofertas"""
    
        offers = response.css("article.box_offer")
        self.logger.info(f"🔍 Encontradas {len(offers)} ofertas")
    
        for offer in offers:
            relative_url = offer.css("h2 a.js-o-link::attr(href)").get()
            if relative_url:
                self.logger.info(f"➡️ Siguiendo: {relative_url}") 
                yield response.follow(relative_url, callback=self.parse_job)
        # Paginación
        next_page = (
            response.css("a[rel='next']::attr(href)").get()
            or response.css("a.pagination__next::attr(href)").get()
        )
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_job(self, response):
        """Parsea una oferta individual"""
        item = JobItem()

        item["source_platform"] = "Computrabajo"
        item["source_url"] = response.url
        #item["job_id"] = self.extract_job_id_from_url(response.url)

        item["title"] = response.css("h1::text").get()
        # Compañía - varios patrones
        company = response.css("p.title-company a::text").get()
        if not company:
            company = response.css("p.title-company::text").get()  # a veces no es link
        if not company:
            company = response.css("a.it-blank::text").get()       # patrón frecuente en CT
        if not company:
            company = response.css("div[div-link='empresa'] p::text").get()  # sección empresa
            if company:
                company = company.strip().split("\n")[0]
        if company:
            company = company.strip()
            if len(company) < 3 or company.lower() in {"empresa", "ver empresa"}:
                company = None        
        item["company_name"] = company
    
        
        if not item.get("company_name"):
            self.logger.warning(f"Saltado (sin empresa) | title={item.get('title')} | url={response.url}")
            return
        # Ubicación
        location = response.css("p.location span::text").get()
        if not location:
            location = response.css("p.location::text").get()

        if location:
            location = location.strip()
            loc_lower = location.lower()

            if any(k in loc_lower for k in ["remoto", "trabajo desde casa", "home office"]):
                location = "Remote"

        item["location"] = location or None

        # País
        item["country"] = self.extract_country_from_domain(response.url)

        # Descripción
        html = response.css("div[div-link='oferta']").get()
        if not html:
            self.logger.warning(f"No se encontró descripción en {response.url}")
        item["description"] = html

        # Fecha de publicación
        #"span.date, span.dO::text"
        raw_date = response.css("p.fc_aux.fs13::text").get()
        item["posted_date"] = self.parse_relative_date(raw_date)

        # Salario
        tags = response.css(
            "div[div-link='oferta'] span.tag.base::text"
        ).getall()

        salary = None
        for t in tags:
            t_clean = t.strip()

            # Caso monto explícito
            if "$" in t_clean and any(ch.isdigit() for ch in t_clean):
                salary = t_clean
                break

            # Caso "A convenir"
            if "convenir" in t_clean.lower():
                salary = "A convenir"
                break

        item["salary_range"] = salary
        
        requirements_list = response.css(
            "div[div-link='oferta'] ul.disc li::text"
        ).getall()

        requirements = " ".join(r.strip() for r in requirements_list if r.strip())

        item["requirements"] = requirements if requirements else None


        yield item

    @staticmethod
    def extract_country_from_domain(url):
        domain_map = {
            "mx.com": "Mexico",
            "co.com": "Colombia",
            "pe.com": "Peru",
            "ar.com": "Argentina",
        }
        for d, country in domain_map.items():
            if d in url:
                return country
        return None

    @staticmethod
    def extract_job_id_from_url(url):
        match = re.search(r"/(\d+)$", url)
        return match.group(1) if match else None

    @staticmethod
    def parse_relative_date(text):
        """
        Convierte fechas relativas de Computrabajo a YYYY-MM-DD
        """
        if not text:
            return None

        text = text.lower().strip()
        text = re.sub(r"\(.*?\)", "", text).strip()  # quitar "(actualizada)"

        today = datetime.date.today()
    
        if "hoy" in text:
            return today.isoformat()

        if "ayer" in text:
            return (today - datetime.timedelta(days=1)).isoformat()

        # hace X días
        m = re.search(r"hace (\d+) día", text)
        if m:
            days = int(m.group(1))
            return (today - datetime.timedelta(days=days)).isoformat()

        # hace X horas
        m = re.search(r"hace (\d+) hora", text)
        if m:
            return today.isoformat()

        # fallback: no entendida
        return None
