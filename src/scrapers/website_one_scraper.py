from bs4 import BeautifulSoup
import requests
from .scraper_base import Scraper
import streamlit as st


class WebsiteOneScraper(Scraper):
    def __init__(self, keywords):
        self.keywords = keywords.split(',') if isinstance(keywords, str) else keywords
        self.base_url = st.secrets.get('WEBSITE_ONE_URL')
        self.article_limit = 10  # Set the article limit

    def scrape(self):
        html_content = self.fetch_html(self.base_url)
        return self.parse_articles(html_content)

    def fetch_html(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None

    def extract_image(self, soup, url):
        """Extract main image from article"""
        image_url = None
        image_alt = ""
        
        # Try several common image selectors
        image_selectors = [
            '.featured-image img',
            '.post-thumbnail img',
            'article img:first-child',
            '.entry-content img:first-child',
            'figure img',
            'img.wp-post-image',
            '.post-image img'
        ]
        
        for selector in image_selectors:
            img = soup.select_one(selector)
            if img and img.has_attr('src'):
                image_url = img['src']
                if img.has_attr('alt'):
                    image_alt = img['alt']
                break
                
        # If no image found with selectors, try looking for any image
        if not image_url:
            img = soup.find('img')
            if img and img.has_attr('src'):
                image_url = img['src']
                if img.has_attr('alt'):
                    image_alt = img['alt']
        
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
                
        return {
            'url': image_url,
            'alt': image_alt
        }

    def parse_articles(self, html_content):
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Update the selectors based on the actual HTML structure of miningmexico.com
        for item in soup.find_all('article'):
            try:
                # Break the loop if we've reached the limit
                if len(articles) >= self.article_limit:
                    break
                    
                title_element = item.find('h2', class_='entry-title')
                if not title_element:
                    continue
                    
                title = title_element.text.strip()
                link = title_element.find('a')['href']
                
                # Check if any keyword is in the title
                if not any(keyword.lower() in title.lower() for keyword in self.keywords):
                    continue
                
                # Fetch the full article content
                article_html = self.fetch_html(link)
                article_soup = BeautifulSoup(article_html, 'html.parser')
                
                # Extract the featured image
                image = self.extract_image(article_soup, link)
                
                # Get the content (adjust the selector based on actual HTML)
                content_element = article_soup.find('div', class_='entry-content')
                text = content_element.get_text(strip=True) if content_element else ""
                
                articles.append({
                    'title': title,
                    'link': link,
                    'text': text,
                    'image': image
                })
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
                
        return articles