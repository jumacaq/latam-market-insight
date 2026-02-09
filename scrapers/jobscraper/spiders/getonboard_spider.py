# GetonBoard is a popular LatAm tech job board (very scraper-friendly)

import scrapy
from datetime import datetime
import re
from jobscraper.items import JobItem


class GetonBoardSpider(scrapy.Spider):
    name = 'getonboard'
    allowed_domains = ['getonbrd.com']
    
    # Start URLs for different countries and sectors
    start_urls = [
    'https://www.getonbrd.com/empleos',
    'https://www.getonbrd.com/empleos?country=MX',  # Mexico
    'https://www.getonbrd.com/empleos?country=CL',  # Chile
    'https://www.getonbrd.com/empleos?country=CO',  # Colombia
    'https://www.getonbrd.com/empleos?country=AR',  # Argentina
    'https://www.getonbrd.com/empleos?country=PE',  # Peru   
    ]
    
    def parse(self, response):
        """Parse job listing page"""
        #all_links = response.css('a::attr(href)').getall()
        links = response.css('a.gb-results-list__item::attr(href)').getall()
        
        for link in links:
            yield response.follow(link, callback=self.parse_job)
        
        # Filtrar solo links de trabajos (no categorías)
        #job_links = [l for l in all_links if '/empleos/' in l and l.count('/') >= 4]
        #unique_links = list(set(job_links))
        
        #self.logger.info(f"🔍 Encontrados {len(unique_links)} trabajos únicos")

        # Follow pagination
        next_page = response.css('a.next_page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_job(self, response):
        """Parse individual job page"""
        item = JobItem()
        raw_title = response.xpath('//h1//text()').getall()
        item['title'] = " ".join([t.strip() for t in raw_title if t.strip()]).split(" en ")[0] if raw_title else None
        #item['title'] = response.css('h1[itemprop="title"]::text').get() or \
                        #response.css('div.gb-landing-cover__title strong::text').get() or \
                        #response.xpath('//h1/text()').get()
        item['company_name'] = response.css('span[itemprop="name"]::text').get() or \
                               response.css('.gb-landing-cover__sub-title strong::text').get() or \
                               response.xpath('//meta[@property="og:site_name"]/@content').get() or \
                               "Jobs"   
        item['location'] = response.css('span[itemprop="addressLocality"]::text').get() or \
                           response.css('div.gb-landing-cover__sub-title::text').getall()
        item['description'] = response.css('div[itemprop="description"]').get() or \
                              response.css('div#job-body').get() or \
                              response.css('div.gb-landing-section').get()
        item['source_platform'] = 'GetonBoard'
        item['source_url'] = response.url
        item['scraped_at'] = datetime.now().isoformat()
        # Estandarización para el Pipeline y el ETL
        item['salary_range'] = response.css('div.gb-landing-cover__salary::text').get() or \
                               response.css('.gb-results-list__item-salary::text').get() or "A convenir"
        item['country'] = None
        item['seniority_level'] = None
        item['salary_min'] = None
        item['salary_max'] = None
        item['skills'] = []
        # Limpieza básica de la ubicación si viene como lista
        if isinstance(item['location'], list):
            item['location'] = " ".join([l.strip() for l in item['location'] if l.strip()])
        # Validación final antes de enviar al Pipeline
        if item.get('title') and (item.get('description') or item.get('title')):
            # Limpiar espacios en blanco extra de última hora
            item['title'] = item['title'].strip() if item['title'] else None
            item['company_name'] = item['company_name'].strip() if item['company_name'] else "Empresa no especificada"
            yield item
        #if item.get('title') and item.get('description'):
            #yield item
        else:
            self.logger.warning(f"⚠️ Saltado por datos incompletos: {response.url}")
    
    
    @staticmethod
    def extract_job_id(url):
        """Extract job ID from URL"""
        match = re.search(r'/jobs/([a-zA-Z0-9-]+)', url)
        return match.group(1) if match else None
    
    @staticmethod
    def normalize_seniority(seniority):
        """Normalize seniority levels"""
        if not seniority:
            return None
        
        seniority_lower = seniority.lower()
        if 'junior' in seniority_lower:
            return 'Junior'
        elif 'senior' in seniority_lower:
            return 'Senior'
        elif 'semi senior' in seniority_lower or 'ssr' in seniority_lower:
            return 'Mid'
        elif 'expert' in seniority_lower or 'lead' in seniority_lower:
            return 'Lead'
        else:
            return 'Mid'
        
    
    @staticmethod
    def extract_country_from_url(url):
        """Extract country from URL"""
        if '/mexico' in url:
            return 'Mexico'
        elif '/chile' in url:
            return 'Chile'
        elif '/colombia' in url:
            return 'Colombia'
        elif '/argentina' in url:
            return 'Argentina'
        elif '/remote-latam' in url:
            return 'Remote LatAm'
        return None
