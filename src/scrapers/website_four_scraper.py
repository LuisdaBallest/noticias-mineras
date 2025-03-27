from bs4 import BeautifulSoup
import requests
import time
import re
from .scraper_base import Scraper
import streamlit as st


class WebsiteFourScraper(Scraper):
    def __init__(self, keywords):
        self.keywords = keywords.split(',') if isinstance(keywords, str) else keywords
        self.base_url = st.secrets.get('WEBSITE_FOUR_URL')
        self.article_limit = 10  # Set the article limit
        
    def scrape(self):
        print(f"Starting scrape of {self.base_url}")
        html_content = self.fetch_html(self.base_url)
        
        # Para diagnóstico
        # self.analyze_page_structure(html_content)
        
        return self.parse_articles(html_content)

    def fetch_html(self, url):
        try:
            print(f"Fetching HTML from {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
            # Use a session to handle cookies
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            print(f"Successfully fetched {url} (Status: {response.status_code})")
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def extract_image(self, soup, url):
        """Extract main image from article"""
        image_url = None
        image_alt = ""
        
        # Try RumboMinero specific selectors first
        image_selectors = [
            '.td-post-featured-image img',  # Imagen destacada en la página de artículo
            '.wp-post-image',               # Clase común de WordPress
            '.td-module-thumb img',         # Selector para thumbs en listados
            '.entry-thumb',                 # Otro selector común
            'article img:first-child',
            '.entry-content img:first-child',
            'figure img',
            '.td_block_inner img',          # Bloques de contenido
            '.td-module-image img'          # Otro selector para módulos
        ]
        
        for selector in image_selectors:
            img = soup.select_one(selector)
            if img:
                # Intentar varios atributos donde podría estar la URL
                for attr in ['data-src', 'data-lazy-src', 'src', 'data-img-url']:
                    if img.has_attr(attr) and img[attr]:
                        image_url = img[attr]
                        if img.has_attr('alt'):
                            image_alt = img['alt']
                        print(f"Found image with selector '{selector}': {image_url}")
                        break
                if image_url:
                    break
        
        # Si no se encontró imagen, buscar cualquier imagen
        if not image_url:
            for img in soup.find_all('img'):
                # Evitar logos, iconos, banners pequeños
                skip_patterns = ['logo', 'icon', 'banner', 'avatar', 'placeholder']
                
                # Intentar varios atributos
                for attr in ['data-src', 'data-lazy-src', 'src', 'data-img-url']:
                    if img.has_attr(attr) and img[attr]:
                        img_url = img[attr]
                        # Verificar si debe omitirse
                        if not any(pattern in img_url.lower() for pattern in skip_patterns):
                            image_url = img_url
                            if img.has_attr('alt'):
                                image_alt = img['alt']
                            print(f"Found fallback image: {image_url}")
                            break
                if image_url:
                    break
        
        # Make image URL absolute if it's relative
        if image_url and not image_url.startswith('http'):
            if image_url.startswith('//'):
                # Protocol-relative URL
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                # Root-relative URL
                base_domain = '/'.join(url.split('/')[:3])
                image_url = base_domain + image_url
            else:
                # Path-relative URL
                if '/' in url.rstrip('/').rsplit('/', 1)[0]:
                    image_url = f"{url.rstrip('/').rsplit('/', 1)[0]}/{image_url.lstrip('/')}"
                else:
                    # Si todo falla, intenta construir la URL desde el dominio base
                    domain = '/'.join(url.split('/')[:3])
                    image_url = f"{domain}/{image_url.lstrip('/')}"
        
        # Ensure image URL doesn't contain spaces or invalid characters
        if image_url:
            image_url = image_url.replace(' ', '%20')
            print(f"Final image URL: {image_url}")
                
        return {
            'url': image_url,
            'alt': image_alt
        }

    def parse_articles(self, html_content):
        if not html_content:
            print("No HTML content retrieved from RumboMinero.com")
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Debug información básica
        print(f"Page title: {soup.title.text if soup.title else 'No title found'}")
        
        # ---- PRIMERA ESTRATEGIA: Buscar cualquier módulo de artículo ----
        # Buscar todos los posibles módulos de artículos (patrón común en el tema de WordPress)
        article_modules = soup.select('div[class*="td_module_"]')
        print(f"Found {len(article_modules)} potential article modules")
        
        for article_module in article_modules:
            try:
                # Break the loop if we've reached the limit
                if len(articles) >= self.article_limit:
                    break
                
                # Obtener título y enlace - buscar tags h3/h4 con enlaces
                title_element = None
                for selector in ['h3 a', 'h4 a', '.entry-title a', '.td-module-title a']:
                    title_element = article_module.select_one(selector)
                    if title_element:
                        break
                
                if not title_element:
                    # Probar buscando cualquier enlace dentro del módulo
                    links = article_module.find_all('a')
                    for link in links:
                        # Evitar enlaces que probablemente no sean títulos
                        if link.get_text().strip() and len(link.get_text().strip()) > 15:
                            title_element = link
                            break
                
                if not title_element:
                    continue
                
                title = title_element.get_text(strip=True)
                link = title_element.get('href')
                
                if not title or not link:
                    continue
                    
                print(f"Found article: {title}")
                
                # Verificar que el enlace sea del mismo dominio
                if 'rumbominero.com' not in link:
                    continue
                    
                # Verificar keywords
                if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                    print(f"Skipping article (no matching keywords): {title}")
                    continue
                
                # Obtener imagen
                image = {'url': None, 'alt': title}
                img_element = None
                
                # Buscar imagen en varios posibles elementos
                for selector in ['.td-module-thumb img', '.entry-thumb', 'img']:
                    img_element = article_module.select_one(selector)
                    if img_element:
                        break
                
                if img_element:
                    # Intentar varios atributos donde podría estar la URL
                    for attr in ['data-src', 'data-lazy-src', 'src', 'data-img-url']:
                        if img_element.has_attr(attr) and img_element[attr]:
                            image['url'] = img_element[attr]
                            if img_element.has_attr('alt'):
                                image['alt'] = img_element['alt']
                            break
                
                # Fetch article content
                time.sleep(1)  # Be nice to the server
                article_html = self.fetch_html(link)
                
                if article_html:
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    
                    # Si no tenemos imagen desde el listado, buscamos en la página del artículo
                    if not image['url']:
                        image = self.extract_image(article_soup, link)
                    
                    # Buscar el contenido del artículo
                    content_element = None
                    for selector in [
                        '.td-post-content',
                        '.tdb_single_content',
                        '.td_block_wrap .tdb-block-inner',
                        'article .content',
                        '.entry-content',
                        '.post-content',
                        'article'
                    ]:
                        content_element = article_soup.select_one(selector)
                        if content_element:
                            print(f"Found content with selector '{selector}'")
                            break
                    
                    text = ""
                    if content_element:
                        # Limpiar el contenido
                        for unwanted in content_element.select('script, style, .sharedaddy, .jp-relatedposts, .social-share, .comments-area, .navigation'):
                            unwanted.decompose()
                        
                        paragraphs = content_element.find_all('p')
                        if paragraphs:
                            text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                        else:
                            text = content_element.get_text(strip=True, separator=' ')
                            
                        print(f"Extracted {len(text)} characters of content")
                    else:
                        print(f"Could not find content for: {title}")
                    
                    # Añadir el artículo a nuestra lista
                    articles.append({
                        'title': title,
                        'link': link,
                        'text': text,
                        'image': image
                    })
                    print(f"Successfully added article: {title}")
                else:
                    print(f"Failed to fetch article content for: {title}")
            
            except Exception as e:
                print(f"Error parsing article: {str(e)}")
                continue
        
        # ---- SEGUNDA ESTRATEGIA: Si no se encontraron artículos, buscar en bloques de contenido ----
        if not articles:
            print("First strategy found no articles. Trying alternative approach...")
            
            # Bloques comunes en temas de newspaper
            block_elements = soup.select('.td_block_inner, .tdb-block-inner')
            
            for block in block_elements:
                links = block.find_all('a')
                processed_links = set()  # Para evitar procesar el mismo enlace dos veces
                
                for link in links:
                    try:
                        # Break the loop if we've reached the limit
                        if len(articles) >= self.article_limit:
                            break
                        
                        href = link.get('href')
                        
                        # Saltar enlaces no válidos o ya procesados
                        if not href or href in processed_links or 'rumbominero.com' not in href:
                            continue
                            
                        processed_links.add(href)
                        
                        # Verificar si el enlace parece ser un artículo (no categorías o tags)
                        if '/category/' in href or '/tag/' in href:
                            continue
                        
                        # Asumir que el texto del enlace es el título
                        title = link.get_text(strip=True)
                        
                        # Saltar enlaces sin texto o con texto muy corto
                        if not title or len(title) < 15:
                            continue
                            
                        print(f"Found potential article link: {title}")
                        
                        # Verificar keywords
                        if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                            print(f"Skipping article (no matching keywords): {title}")
                            continue
                        
                        # Fetch article content
                        time.sleep(1)
                        article_html = self.fetch_html(href)
                        
                        if article_html:
                            article_soup = BeautifulSoup(article_html, 'html.parser')
                            
                            # Obtener imagen del artículo
                            image = self.extract_image(article_soup, href)
                            
                            # Buscar el contenido del artículo
                            content_element = None
                            for selector in [
                                '.td-post-content',
                                '.tdb_single_content',
                                '.td_block_wrap .tdb-block-inner',
                                'article .content',
                                '.entry-content',
                                '.post-content',
                                'article'
                            ]:
                                content_element = article_soup.select_one(selector)
                                if content_element:
                                    break
                            
                            text = ""
                            if content_element:
                                # Limpiar el contenido
                                for unwanted in content_element.select('script, style, .sharedaddy, .jp-relatedposts, .social-share, .comments-area, .navigation'):
                                    unwanted.decompose()
                                
                                paragraphs = content_element.find_all('p')
                                if paragraphs:
                                    text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                                else:
                                    text = content_element.get_text(strip=True, separator=' ')
                                
                                print(f"Extracted {len(text)} characters of content")
                            else:
                                print(f"Could not find content for: {title}")
                            
                            # Añadir el artículo a nuestra lista
                            articles.append({
                                'title': title,
                                'link': href,
                                'text': text,
                                'image': image
                            })
                            print(f"Successfully added article (strategy 2): {title}")
                    except Exception as e:
                        print(f"Error processing link: {str(e)}")
        
        print(f"Total articles found after all strategies: {len(articles)}")
        return articles

    def analyze_page_structure(self, html_content):
        """Analyzes the page structure to help adjust selectors"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\n=== PAGE STRUCTURE ANALYSIS ===")
        print(f"Page title: {soup.title.text if soup.title else 'No title found'}")
        
        # Examine block_inner divs
        block_inners = soup.select('div[class*="block_inner"]')
        print(f"\nFound {len(block_inners)} block_inner divs")
        
        # Find article modules
        modules = soup.select('div[class*="td_module_"]')
        print(f"\nFound {len(modules)} article modules")
        
        # Count each module type
        module_types = {}
        for module in modules:
            classes = module.get('class', [])
            module_type = next((c for c in classes if c.startswith('td_module_')), 'unknown')
            module_types[module_type] = module_types.get(module_type, 0) + 1
        
        print("\nModule types count:")
        for module_type, count in module_types.items():
            print(f"  - {module_type}: {count}")
        
        # Examine a sample module
        if modules:
            print("\nSample module structure:")
            sample = modules[0]
            print(f"  Classes: {sample.get('class')}")
            
            # Title element
            title_elem = sample.select_one('h3.entry-title, h3.td-module-title, .entry-title')
            if title_elem:
                title_link = title_elem.select_one('a')
                if title_link:
                    print(f"  Title: {title_link.get_text(strip=True)}")
                    print(f"  Link: {title_link.get('href', 'no-href')}")
            
            # Image element
            img_elem = sample.select_one('img')
            if img_elem:
                print(f"  Image src: {img_elem.get('src', 'no-src')}")
                print(f"  Image data-src: {img_elem.get('data-src', 'no-data-src')}")
                print(f"  Image data-img-url: {img_elem.get('data-img-url', 'no-data-img-url')}")
        
        # List main block containers
        main_blocks = soup.select('.td_block_wrap, .tdb_block_inner')
        print(f"\nFound {len(main_blocks)} main block containers")
        
        # List all links on the page for analysis
        links = soup.find_all('a')
        article_links = []
        
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Filter for potential article links
            if href and 'rumbominero.com' in href and '/category/' not in href and '/tag/' not in href:
                if text and len(text) > 15:  # Title likely has more than 15 chars
                    article_links.append((text, href))
        
        print(f"\nFound {len(article_links)} potential article links")
        if article_links:
            print("Sample articles:")
            for i, (title, href) in enumerate(article_links[:5]):
                print(f"  {i+1}. {title} - {href}")
        
        print("=== END OF ANALYSIS ===\n")