from bs4 import BeautifulSoup
import requests
import time
import re
from .scraper_base import Scraper
import streamlit as st


class WebsiteFourScraper(Scraper):
    def __init__(self, keywords):
        self.keywords = keywords.split(',') if isinstance(keywords, str) else keywords
        self.base_url = st.secrets.get('WEBSITE_FOUR_URL', 'https://www.rumbominero.com/category/mexico/')
        self.article_limit = 10  # Set the article limit
        
    def scrape(self):
        print(f"Starting scrape of {self.base_url}")
        html_content = self.fetch_html(self.base_url)
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
        
        # Buscar el contenedor principal según la estructura proporcionada
        main_container = soup.select_one('div[id="tdi_130"], .td_block_inner')
        
        if main_container:
            print(f"Found main container: {main_container.name} with id={main_container.get('id', 'no-id')}")
            
            # Buscar todos los módulos de artículos según la estructura proporcionada
            article_modules = main_container.select('.td_module_16, .td_module_wrap, .td-animation-stack')
            
            if not article_modules:
                # Intentar con otro selector más genérico
                article_modules = main_container.select('div[class*="td_module_"]')
            
            print(f"Found {len(article_modules)} article modules")
            
            for article_module in article_modules:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    # Buscar el thumbnail y el enlace/título como mencionaste
                    thumb_container = article_module.select_one('.td-module-thumb')
                    
                    if thumb_container:
                        # Buscar el enlace del artículo con la clase específica
                        link_element = thumb_container.select_one('a.td-image-wrap')
                        
                        if link_element and link_element.has_attr('href') and link_element.has_attr('title'):
                            # Extraer título del atributo title del enlace
                            title = link_element.get('title', '').strip()
                            link = link_element['href']
                            
                            # Si encontramos título y enlace, procesamos el artículo
                            if title and link:
                                print(f"Found article: {title}")
                                
                                # Verificar keywords
                                if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                                    print(f"Skipping article (no matching keywords): {title}")
                                    continue
                                
                                # Extraer imagen directamente del thumbnail
                                image = {'url': None, 'alt': title}
                                img_element = thumb_container.select_one('img')
                                
                                if img_element:
                                    # Intentar obtener la URL de la imagen
                                    if img_element.has_attr('src'):
                                        image['url'] = img_element['src']
                                    elif img_element.has_attr('data-src'):
                                        image['url'] = img_element['data-src']
                                        
                                    # Obtener texto alternativo si está disponible
                                    if img_element.has_attr('alt'):
                                        image['alt'] = img_element['alt']
                                        
                                    # Hacer URL de imagen absoluta si es necesario
                                    if image['url'] and not image['url'].startswith('http'):
                                        if image['url'].startswith('//'):
                                            image['url'] = 'https:' + image['url']
                                        elif image['url'].startswith('/'):
                                            base_domain = 'https://www.rumbominero.com'
                                            image['url'] = base_domain + image['url']
                                
                                # Fetch article content
                                time.sleep(1)  # Be nice to the server
                                article_html = self.fetch_html(link)
                                
                                if article_html:
                                    article_soup = BeautifulSoup(article_html, 'html.parser')
                                    
                                    # Si no obtuvimos una imagen válida del listado, intentar extraerla de la página del artículo
                                    if not image['url'] or 'placeholder' in image['url']:
                                        image = self.extract_image(article_soup, link)
                                    
                                    # Try to find content - RumboMinero typically uses .td-post-content
                                    content_element = article_soup.select_one('.td-post-content, .entry-content, article .content')
                                    
                                    if not content_element:
                                        # Try more generic selectors if specific ones fail
                                        for selector in [
                                            'div.post-content',
                                            'div.content', 
                                            'article',
                                            'div.entry',
                                            'main',
                                            'div#content'
                                        ]:
                                            content_element = article_soup.select_one(selector)
                                            if content_element:
                                                print(f"Found content with selector '{selector}'")
                                                break
                                    
                                    if content_element:
                                        # Clean content - remove scripts, social sharing, etc.
                                        for unwanted in content_element.select('script, style, .sharedaddy, .jp-relatedposts, .social-share, .comments-area, .navigation'):
                                            unwanted.decompose()
                                        
                                        text = content_element.get_text(strip=True, separator=' ')
                                        print(f"Extracted {len(text)} characters of content")
                                    else:
                                        print(f"Could not find content for: {title}")
                                        text = ""
                                        
                                    # Add the article to our list
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
            print("Could not find the main article container")
            
            # Try alternative approach for finding articles
            # Find all td_module elements across the page as a fallback
            article_modules = soup.select('div[class*="td_module_"]')
            print(f"Fallback: Found {len(article_modules)} article modules")
            
            for article_module in article_modules:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    # Look for link with title
                    link_element = article_module.select_one('a[title]') or article_module.select_one('.entry-title a')
                    
                    if link_element and link_element.has_attr('href'):
                        # Get title from link text or title attribute
                        title = link_element.get_text(strip=True) or link_element.get('title', '')
                        link = link_element['href']
                        
                        if title and link:
                            print(f"Found article via fallback: {title}")
                            
                            # Check keywords
                            if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                                print(f"Skipping article (no matching keywords): {title}")
                                continue
                            
                            # Process article as before
                            # Rest of processing code similar to above
                            # ...
                
                except Exception as e:
                    print(f"Error in fallback article parsing: {str(e)}")
                    continue
                    
        # Final fallback if no articles found yet
        if not articles:
            # Look for links that might be article titles anywhere on the page
            potential_articles = soup.select('a[title], .entry-title a, h3 a, h2 a')
            
            print(f"Final fallback: Found {len(potential_articles)} potential article links")
            
            for link_element in potential_articles:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                        
                    title = link_element.get_text(strip=True) or link_element.get('title', '')
                    if not title or len(title) < 10:  # Skip very short titles or empty ones
                        continue
                        
                    if not link_element.has_attr('href'):
                        continue
                        
                    link = link_element['href']
                    
                    # Make sure this is an article link
                    if not ('rumbominero.com' in link and '/noticias/' in link):
                        continue
                        
                    print(f"Found potential article via final fallback: {title}")
                    
                    # Check keywords
                    if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                    
                    # Process article (similar to above code)
                    # ...
                    
                except Exception as e:
                    print(f"Error in final fallback article processing: {str(e)}")
                    continue
        
        print(f"Total articles found after filtering: {len(articles)}")
        return articles