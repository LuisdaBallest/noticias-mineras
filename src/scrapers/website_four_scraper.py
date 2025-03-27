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
        
        # Puedes descomentar la siguiente línea cuando necesites diagnosticar problemas
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
        
        # Try RumboMinero specific selectors first - based on the structure you provided
        image_selectors = [
            '.td-module-thumb img',        # Selector específico según la estructura mencionada
            '.td-post-featured-image img',  # Imagen destacada en la página de artículo
            '.wp-post-image',              # Clase común de WordPress
            '.entry-thumb img',
            '.featured-image img',
            'article img:first-child',
            '.entry-content img:first-child',
            'figure img',
            '.post-image img'
        ]
        
        for selector in image_selectors:
            print(f"Trying image selector: {selector}")
            img = soup.select_one(selector)
            if img and img.has_attr('src'):
                image_url = img['src']
                if img.has_attr('alt'):
                    image_alt = img['alt']
                print(f"Found image with selector '{selector}': {image_url}")
                break
                
        # If no image found with selectors, try looking for any image
        if not image_url:
            img = soup.find('img')
            if img and img.has_attr('src'):
                image_url = img['src']
                if img.has_attr('alt'):
                    image_alt = img['alt']
                print(f"Found fallback image: {image_url}")
        
        # Skip placeholder or icon images
        if image_url and (
            'placeholder' in image_url.lower() or 
            'icon' in image_url.lower() or
            'logo' in image_url.lower() or
            any(dim in image_url for dim in ['20x20', '32x32', '16x16', '24x24', '50x50'])
        ):
            print(f"Skipping placeholder/icon image: {image_url}")
            # Try to find another image
            for img in soup.find_all('img'):
                if img.has_attr('src') and img['src'] != image_url:
                    # Check if this might be a larger/featured image
                    if 'placeholder' not in img['src'].lower() and 'icon' not in img['src'].lower() and 'logo' not in img['src'].lower():
                        image_url = img['src']
                        if img.has_attr('alt'):
                            image_alt = img['alt']
                        print(f"Found better image: {image_url}")
                        break
        
        # Handle data-src for lazy-loaded images
        if not image_url or 'placeholder' in image_url:
            for img in soup.find_all('img'):
                if img.has_attr('data-src'):
                    image_url = img['data-src']
                    if img.has_attr('alt'):
                        image_alt = img['alt']
                    print(f"Found image from data-src: {image_url}")
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
                image_url = f"{url.rstrip('/').rsplit('/', 1)[0]}/{image_url.lstrip('/')}"
        
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
        
        # Debug information
        print(f"Page title: {soup.title.text if soup.title else 'No title found'}")
        
        # Buscar específicamente la estructura de RumboMinero
        # Buscar el div con id="tdi_130" que contiene los artículos
        main_container = soup.select_one('div#tdi_130.td_block_inner')
        
        if main_container:
            print(f"Found main container with id=tdi_130")
            
            # Buscar todos los módulos de artículos con la clase específica
            article_modules = main_container.select('.td_module_16.td_module_wrap.td-animation-stack')
            
            print(f"Found {len(article_modules)} article modules")
            
            for article_module in article_modules:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    # Obtener título y enlace
                    title_element = article_module.select_one('.entry-title.td-module-title a')
                    
                    if not title_element:
                        print("No title element found in article container")
                        continue
                    
                    title = title_element.get_text(strip=True)
                    link = title_element.get('href')
                    
                    if not title or not link:
                        print("Missing title or link")
                        continue
                        
                    print(f"Found article: {title}")
                        
                    # Verificar keywords
                    if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                    
                    # Obtener imagen
                    thumb_element = article_module.select_one('.td-module-thumb a img')
                    image = {'url': None, 'alt': title}
                    
                    if thumb_element:
                        # Intentar obtener src o data-img-url
                        if thumb_element.has_attr('src'):
                            image['url'] = thumb_element['src']
                        elif thumb_element.has_attr('data-img-url'):
                            image['url'] = thumb_element['data-img-url']
                        
                        # Obtener texto alternativo
                        if thumb_element.has_attr('alt'):
                            image['alt'] = thumb_element['alt']
                    
                    # Fetch article content
                    time.sleep(1)  # Be nice to the server
                    article_html = self.fetch_html(link)
                    
                    if article_html:
                        article_soup = BeautifulSoup(article_html, 'html.parser')
                        
                        # Si no tenemos imagen desde el listado, buscamos en la página del artículo
                        if not image['url']:
                            image = self.extract_image(article_soup, link)
                        
                        # Buscar el contenido del artículo
                        content_element = article_soup.select_one('.td-post-content')
                        
                        if not content_element:
                            # Intentar con selectores alternativos
                            for selector in [
                                '.td_block_wrap .tdb-block-inner',
                                '.td-post-content',
                                '.tdb_single_content',
                                'article .content',
                                '.entry-content'
                            ]:
                                content_element = article_soup.select_one(selector)
                                if content_element:
                                    print(f"Found content with selector '{selector}'")
                                    break
                        
                        if content_element:
                            # Limpiar el contenido
                            for unwanted in content_element.select('script, style, .sharedaddy, .jp-relatedposts, .social-share, .comments-area, .navigation'):
                                unwanted.decompose()
                            
                            text = content_element.get_text(strip=True, separator=' ')
                            print(f"Extracted {len(text)} characters of content")
                        else:
                            print(f"Could not find content for: {title}")
                            text = ""
                        
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
        else:
            print("Main container div#tdi_130.td_block_inner not found")
            
            # Método alternativo: buscar por estructura de módulos individuales
            article_modules = soup.select('.td_module_16.td_module_wrap.td-animation-stack')
            print(f"Trying alternative approach, found {len(article_modules)} article modules")
            
            if article_modules:
                for article_module in article_modules:
                    try:
                        # Break the loop if we've reached the limit
                        if len(articles) >= self.article_limit:
                            break
                        
                        # Obtener título y enlace
                        title_element = article_module.select_one('.entry-title.td-module-title a')
                        
                        if not title_element:
                            print("No title element found in article container")
                            continue
                        
                        title = title_element.get_text(strip=True)
                        link = title_element.get('href')
                        
                        if not title or not link:
                            print("Missing title or link")
                            continue
                            
                        print(f"Found article: {title}")
                            
                        # Verificar keywords
                        if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                            print(f"Skipping article (no matching keywords): {title}")
                            continue
                        
                        # Obtener imagen
                        thumb_element = article_module.select_one('.td-module-thumb a img')
                        image = {'url': None, 'alt': title}
                        
                        if thumb_element:
                            # Intentar obtener src o data-img-url
                            if thumb_element.has_attr('src'):
                                image['url'] = thumb_element['src']
                            elif thumb_element.has_attr('data-img-url'):
                                image['url'] = thumb_element['data-img-url']
                            
                            # Obtener texto alternativo
                            if thumb_element.has_attr('alt'):
                                image['alt'] = thumb_element['alt']
                        
                        # Fetch article content
                        time.sleep(1)  # Be nice to the server
                        article_html = self.fetch_html(link)
                        
                        if article_html:
                            article_soup = BeautifulSoup(article_html, 'html.parser')
                            
                            # Si no tenemos imagen desde el listado, buscamos en la página del artículo
                            if not image['url']:
                                image = self.extract_image(article_soup, link)
                            
                            # Buscar el contenido del artículo
                            content_element = article_soup.select_one('.td-post-content')
                            
                            if not content_element:
                                # Intentar con selectores alternativos
                                for selector in [
                                    '.td_block_wrap .tdb-block-inner',
                                    '.td-post-content',
                                    '.tdb_single_content',
                                    'article .content',
                                    '.entry-content'
                                ]:
                                    content_element = article_soup.select_one(selector)
                                    if content_element:
                                        print(f"Found content with selector '{selector}'")
                                        break
                            
                            if content_element:
                                # Limpiar el contenido
                                for unwanted in content_element.select('script, style, .sharedaddy, .jp-relatedposts, .social-share, .comments-area, .navigation'):
                                    unwanted.decompose()
                                
                                text = content_element.get_text(strip=True, separator=' ')
                                print(f"Extracted {len(text)} characters of content")
                            else:
                                print(f"Could not find content for: {title}")
                                text = ""
                            
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
        
        # Si todavía no tenemos artículos, intentar un enfoque más general con la estructura HTML
        if not articles:
            print("Attempting general HTML structure approach")
            
            # Buscar todos los módulos que podrían contener artículos
            potential_articles = soup.select('div[class*="td_module_"]')
            
            for article_div in potential_articles:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    # Buscar título y enlace
                    title_element = article_div.select_one('h3 a, h2 a, .entry-title a')
                    
                    if not title_element:
                        continue
                    
                    title = title_element.get_text(strip=True)
                    link = title_element.get('href')
                    
                    if not title or not link or 'rumbominero.com' not in link:
                        continue
                    
                    print(f"Found article with general approach: {title}")
                    
                    # Verificar keywords
                    if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                    
                    # Obtener imagen - buscar dentro del módulo primero
                    image = {'url': None, 'alt': title}
                    img = article_div.select_one('img')
                    
                    if img:
                        if img.has_attr('src'):
                            image['url'] = img['src']
                        elif img.has_attr('data-src'):
                            image['url'] = img['data-src']
                        elif img.has_attr('data-img-url'):
                            image['url'] = img['data-img-url']
                            
                        if img.has_attr('alt'):
                            image['alt'] = img['alt']
                    
                    # Fetch article content
                    time.sleep(1)  # Be nice to the server
                    article_html = self.fetch_html(link)
                    
                    if article_html:
                        article_soup = BeautifulSoup(article_html, 'html.parser')
                        
                        # Si no tenemos imagen desde el listado, buscamos en la página del artículo
                        if not image['url']:
                            image = self.extract_image(article_soup, link)
                        
                        # Buscar el contenido del artículo - probar diversos selectores
                        content_element = None
                        for selector in [
                            '.td-post-content',
                            '.td_block_wrap .tdb-block-inner',
                            '.tdb_single_content',
                            'article .content',
                            '.entry-content',
                            '.post-content',
                            'article'
                        ]:
                            content_element = article_soup.select_one(selector)
                            if content_element:
                                print(f"Found content with selector '{selector}'")
                                break
                        
                        if content_element:
                            # Limpiar el contenido
                            for unwanted in content_element.select('script, style, .sharedaddy, .jp-relatedposts, .social-share, .comments-area, .navigation'):
                                unwanted.decompose()
                            
                            text = content_element.get_text(strip=True, separator=' ')
                            print(f"Extracted {len(text)} characters of content")
                        else:
                            print(f"Could not find content for: {title}")
                            text = ""
                        
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
                    print(f"Error in general approach: {str(e)}")
                    continue
        
        print(f"Total articles found after filtering: {len(articles)}")
        return articles

    def analyze_page_structure(self, html_content):
        """Analiza la estructura de la página para ayudar a ajustar los selectores"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Buscar posibles contenedores de artículos
        print("\n=== ANÁLISIS DE ESTRUCTURA DE PÁGINA ===")
        
        # 1. Buscar divs con 'block_inner' en su clase
        block_inners = soup.select('div[class*="block_inner"]')
        print(f"Encontrados {len(block_inners)} divs con 'block_inner' en su clase")
        for i, container in enumerate(block_inners):
            container_id = container.get('id', 'sin-id')
            article_count = len(container.select('div[class*="td_module_"]'))
            print(f"  {i+1}. Container id={container_id} contiene {article_count} elementos de módulo")
        
        # 2. Buscar clases de módulos de artículos
        modules = soup.select('div[class*="td_module_"]')
        module_types = {}
        for module in modules:
            classes = module.get('class', [])
            module_type = next((c for c in classes if c.startswith('td_module_')), 'unknown')
            module_types[module_type] = module_types.get(module_type, 0) + 1
        
        print("\nTipos de módulos encontrados:")
        for module_type, count in module_types.items():
            print(f"  - {module_type}: {count} elementos")
        
        # 3. Analizar un módulo de ejemplo si existe
        if modules:
            print("\nEstructura de un módulo de ejemplo:")
            example = modules[0]
            
            # Título
            title_element = example.select_one('h3.entry-title, h3.td-module-title, .entry-title')
            if title_element:
                title_link = title_element.select_one('a')
                if title_link:
                    print(f"  Título: {title_link.get_text(strip=True)}")
                    print(f"  Enlace: {title_link.get('href', 'no-href')}")
            
            # Imagen
            img_element = example.select_one('img')
            if img_element:
                print(f"  Imagen src: {img_element.get('src', 'no-src')}")
                print(f"  Imagen data-src: {img_element.get('data-src', 'no-data-src')}")
                print(f"  Imagen data-img-url: {img_element.get('data-img-url', 'no-data-img-url')}")
        
        print("=== FIN DEL ANÁLISIS ===\n")