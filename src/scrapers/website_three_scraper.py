from bs4 import BeautifulSoup
import requests
import time
import re
from .scraper_base import Scraper
import streamlit as st


class WebsiteThreeScraper(Scraper):
    def __init__(self, keywords):
        self.keywords = keywords.split(',') if isinstance(keywords, str) else keywords
        self.base_url = st.secrets.get('WEBSITE_THREE_URL')
        self.article_limit = 15  # Set the article limit
        
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
        """
        Extract main image from article
        For ProMineria, the image might be in a background style or img tag
        """
        image_url = None
        image_alt = ""
        
        # First, try to find article with background-image style
        article_elements = soup.select('li[style*="background-image"]')
        if article_elements:
            # Extract URL from style attribute
            style = article_elements[0].get('style', '')
            url_match = re.search(r"background-image:url\('([^']+)'\)", style)
            if url_match:
                image_url = url_match.group(1)
                print(f"Found image from background style: {image_url}")
        
        # If no background image found, try regular image selectors
        if not image_url:
            # Try specific ProMineria selectors first
            main_image = soup.select_one('.imagen_nota img')
            if main_image and main_image.has_attr('src'):
                image_url = main_image['src']
                if main_image.has_attr('alt'):
                    image_alt = main_image['alt']
                print(f"Found main article image: {image_url}")
                
        # If still no image, try other common selectors
        if not image_url:
            img_selectors = [
                '.nota_contenido img',
                '.featured-image img',
                'article img:first-child',
                '.entry-content img:first-child',
                'figure img',
                'img',
            ]
            
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img and img.has_attr('src'):
                    image_url = img['src']
                    if img.has_attr('alt'):
                        image_alt = img['alt']
                    print(f"Found image with selector '{selector}': {image_url}")
                    break
        
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
                    if 'placeholder' not in img['src'].lower() and 'icon' not in img['src'].lower() and 'logo' not in img['src'].lower():
                        image_url = img['src']
                        if img.has_attr('alt'):
                            image_alt = img['alt']
                        print(f"Found better image: {image_url}")
                        break
        
        # Make image URL absolute if it's relative
        if image_url:
            if image_url.startswith('//'):
                # Protocol-relative URL
                image_url = 'https:' + image_url
            elif not image_url.startswith(('http://', 'https://')):
                if image_url.startswith('/'):
                    # Root-relative URL
                    base_domain = 'https://www.promineria.com'
                    image_url = base_domain + image_url
                else:
                    # Path-relative URL
                    image_url = f"https://www.promineria.com/{image_url.lstrip('/')}"
        
            # Ensure image URL doesn't contain spaces or invalid characters
            image_url = image_url.replace(' ', '%20')
            print(f"Final image URL: {image_url}")
                
        return {
            'url': image_url,
            'alt': image_alt
        }

    def parse_articles(self, html_content):
        """Parse the HTML content to extract articles"""
        if not html_content:
            print("No HTML content retrieved from ProMineria.com")
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Debug information
        print(f"Page title: {soup.title.text if soup.title else 'No title found'}")
        
        # First, try to find news blocks with the specific structure described
        news_container = soup.find('div', class_='portada_noticias_cuadro')
        if news_container:
            print("Found news container with class 'portada_noticias_cuadro'")
            
            # Find all news items
            news_items = news_container.find_all('li', style=lambda value: value and 'background-image' in value)
            print(f"Found {len(news_items)} news items with background images")
            
            for item in news_items:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    # Extract the background image URL from style attribute
                    background_style = item.get('style', '')
                    image_match = re.search(r"background-image:url\('([^']+)'\)", background_style)
                    image_url = image_match.group(1) if image_match else None
                    
                    # Find the title container and extract title and URL
                    title_container = item.find('div', class_='contenido_cuadro_titulo')
                    if not title_container:
                        continue
                        
                    link_element = title_container.find('a')
                    if not link_element:
                        continue
                        
                    title = link_element.get_text(strip=True)
                    link = link_element.get('href')
                    
                    # Check if we have a valid title and link
                    if not title or not link:
                        continue
                        
                    print(f"Found article: {title}")
                    
                    # Make URL absolute if it's relative
                    if link.startswith('//'):
                        link = 'https:' + link
                    elif not link.startswith(('http://', 'https://')):
                        link = f"https://www.promineria.com/{link.lstrip('/')}"
                    
                    # Check keywords in title
                    if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                    
                    # Fetch article content
                    time.sleep(1)
                    article_html = self.fetch_html(link)
                    if not article_html:
                        print(f"Failed to fetch article content for: {title}")
                        continue
                        
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    
                    # Look for the article content
                    content_element = article_soup.find('div', class_='nota_contenido')
                    
                    if not content_element:
                        # Try other common content containers
                        content_element = article_soup.select_one('#cuerpo_nota, .contenido, .entry-content, article')
                    
                    if not content_element:
                        print(f"Could not find content for: {title}")
                        text = ""
                    else:
                        # Clean content
                        for unwanted in content_element.select('script, style, nav, footer, .comentarios, .redes_sociales'):
                            unwanted.decompose()
                        
                        text = content_element.get_text(strip=True, separator=' ')
                        print(f"Extracted {len(text)} characters of content")
                    
                    # Create image object
                    image = {
                        'url': 'https:' + image_url if image_url and image_url.startswith('//') else image_url,
                        'alt': title
                    }
                    
                    # If we don't have an image from the list, try to extract it from the article page
                    if not image['url']:
                        image = self.extract_image(article_soup, link)
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'text': text,
                        'image': image
                    })
                    print(f"Successfully added article: {title}")
                    
                except Exception as e:
                    print(f"Error parsing article: {str(e)}")
                    continue
        
        # If we didn't find any articles with the specific structure, try an alternative approach
        if not articles:
            print("No articles found with the specific structure, trying alternative approach...")
            
            # Look for articles with more generic selectors
            article_links = soup.select('a[href*="?p=nota&id="]')
            print(f"Found {len(article_links)} article links with generic selectors")
            
            for link_element in article_links:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    title = link_element.get_text(strip=True)
                    if not title:
                        continue
                        
                    link = link_element.get('href')
                    if not link:
                        continue
                    
                    # Make URL absolute
                    if link.startswith('//'):
                        link = 'https:' + link
                    elif not link.startswith(('http://', 'https://')):
                        link = f"https://www.promineria.com/{link.lstrip('/')}"
                    
                    print(f"Found article with generic selector: {title}")
                    
                    # Check keywords in title
                    if self.keywords and not any(keyword.lower().strip() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                    
                    # Fetch article content
                    time.sleep(1)
                    article_html = self.fetch_html(link)
                    if not article_html:
                        continue
                        
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    
                    # Extract image from article
                    image = self.extract_image(article_soup, link)
                    
                    # Look for content
                    content_element = article_soup.find('div', class_='nota_contenido')
                    
                    if not content_element:
                        content_element = article_soup.select_one('#cuerpo_nota, .contenido, .entry-content, article')
                        
                    if not content_element:
                        print(f"Could not find content for: {title}")
                        text = ""
                    else:
                        # Clean content
                        for unwanted in content_element.select('script, style, nav, footer'):
                            unwanted.decompose()
                            
                        text = content_element.get_text(strip=True, separator=' ')
                        print(f"Extracted {len(text)} characters of content")
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'text': text,
                        'image': image
                    })
                    
                except Exception as e:
                    print(f"Error processing article with generic selector: {str(e)}")
                    continue
        
        print(f"Total articles found after filtering: {len(articles)}")
        return articles