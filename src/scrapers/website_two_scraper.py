
from bs4 import BeautifulSoup
import requests
import time
import re
from .scraper_base import Scraper
import streamlit as st

class WebsiteTwoScraper(Scraper):
    def __init__(self, keywords):
        self.keywords = keywords.split(',') if isinstance(keywords, str) else keywords
        self.base_url = st.secrets.get('WEBSITE_TWO_URL')
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
            # Use a session to handle cookies (important for popup handling)
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
        
        # Try several common image selectors - starting with the MundoMinero specific ones
        image_selectors = [
            'img.img-responsive.wp-post-image',  # MundoMinero specific class
            '.tt-featured-image img',            # Another MundoMinero specific
            '.featured-image img',
            '.post-thumbnail img',
            'article img:first-child',
            '.entry-content img:first-child',
            'figure img',
            'img.wp-post-image',
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
        
        # Skip placeholder or icon images (common small images that aren't article featured images)
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
            print("No HTML content retrieved from MundoMinero.mx")
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Debug information
        print(f"Page title: {soup.title.text if soup.title else 'No title found'}")
        
        # Try the specific MundoMinero.mx title class you identified
        title_elements = soup.find_all(class_="tt-post-title c-h5")
        
        if title_elements:
            print(f"Found {len(title_elements)} title elements with class 'tt-post-title c-h5'")
            
            for title_element in title_elements:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                        
                    # Extract the title
                    title = title_element.get_text(strip=True)
                    if not title:
                        continue
                        
                    print(f"Found title: {title}")
                    
                    # Get the link - typically the title is inside an <a> tag
                    link_element = title_element.parent if title_element.name == 'a' else title_element.find('a')
                    
                    # If we still don't have a link, try looking for nearby links
                    if not link_element or not link_element.has_attr('href'):
                        # Try to find a parent article
                        article_container = title_element.find_parent('article') or title_element.find_parent('div', class_='tt-post')
                        if article_container:
                            link_element = article_container.find('a')
                    
                    if not link_element or not link_element.has_attr('href'):
                        print(f"No link found for article: {title}")
                        continue
                        
                    link = link_element['href']
                    
                    # Make sure URL is absolute
                    if not link.startswith('http'):
                        if link.startswith('/'):
                            base_domain = '/'.join(self.base_url.split('/')[:3])
                            link = base_domain + link
                        else:
                            link = f"{self.base_url.rstrip('/')}/{link.lstrip('/')}"
                    
                    print(f"Found article: {title} - {link}")
                    
                    # Check if any keyword is in the title
                    if self.keywords and not any(keyword.lower() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                    
                    # Add a small delay to not overload the server
                    time.sleep(1)
                    
                    # Fetch the full article content
                    article_html = self.fetch_html(link)
                    if not article_html:
                        print(f"Failed to fetch article content for: {title}")
                        continue
                        
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    
                    # Extract the featured image
                    image = self.extract_image(article_soup, link)
                    
                    # Try MundoMinero specific content selectors first
                    content_element = article_soup.find(class_='tt-blog-content')
                    
                    # If that fails, try multiple generic content selector patterns
                    if not content_element:
                        for selector in [
                            'div.post-content',
                            'div.entry-content', 
                            'div.tt-content',
                            'div.content-inner',
                            'article div.post-content', 
                            'div.content',
                            'article', 
                            'div.entry',
                            'div.post',
                            'main',
                            'div#content'
                        ]:
                            content_element = article_soup.select_one(selector)
                            if content_element:
                                print(f"Found content with selector '{selector}'")
                                break
                    
                    if not content_element:
                        print(f"Could not find content for: {title}")
                        text = ""
                    else:
                        # Remove unwanted elements from content
                        for unwanted in content_element.select('script, style, nav, footer, .navigation, .comments, .related-posts, .fusion-sharing-box, .fusion-meta-info'):
                            unwanted.decompose()
                        
                        text = content_element.get_text(strip=True, separator=' ')
                        print(f"Extracted {len(text)} characters of content")
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'text': text,
                        'image': image
                    })
                    print(f"Successfully added article: {title}")
                    
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
            
            print(f"Total articles found after filtering: {len(articles)}")
            return articles
                    
        # If we didn't find articles using the specific class, fall back to the original approach
        print("No title elements found with class 'tt-post-title c-h5', trying alternative approaches...")
        
        # Look for articles or post containers
        article_containers = soup.find_all('article') or soup.select('.tt-post')
        
        if article_containers:
            print(f"Found {len(article_containers)} article containers")
            
            for container in article_containers:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    # Try to find the title in this container
                    title_element = None
                    
                    # Try the specific class first
                    title_element = container.find(class_="tt-post-title")
                    
                    # If that fails, try common heading patterns
                    if not title_element:
                        for heading in ['h2', 'h3', 'h1', 'h4', 'h5']:
                            for class_name in ['entry-title', 'title', 'heading', 'post-title', '']:
                                if class_name:
                                    title_element = container.find(heading, class_=class_name)
                                else:
                                    title_element = container.find(heading)
                                if title_element:
                                    break
                            if title_element:
                                break
                    
                    if not title_element:
                        print("No title element found in article container")
                        continue
                    
                    title = title_element.get_text(strip=True)
                    if not title:
                        print("Empty title found")
                        continue
                        
                    print(f"Found potential article title: {title}")
                    
                    # Find the link
                    link_element = title_element.find('a') or container.find('a', class_='read-more') or container.find('a')
                    if not link_element or not link_element.has_attr('href'):
                        print(f"No link found for article: {title}")
                        continue
                        
                    link = link_element['href']
                    
                    # Make URL absolute
                    if not link.startswith('http'):
                        if link.startswith('/'):
                            base_domain = '/'.join(self.base_url.split('/')[:3])
                            link = base_domain + link
                        else:
                            link = f"{self.base_url.rstrip('/')}/{link.lstrip('/')}"
                    
                    print(f"Found article: {title} - {link}")
                    
                    # Check keywords
                    if self.keywords and not any(keyword.lower() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                    
                    # Fetch article content
                    time.sleep(1)
                    article_html = self.fetch_html(link)
                    if not article_html:
                        print(f"Failed to fetch article content for: {title}")
                        continue
                        
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    
                    # Extract the featured image
                    image = self.extract_image(article_soup, link)
                    
                    # Try to find content
                    content_element = article_soup.find(class_='tt-blog-content')
                    
                    if not content_element:
                        for selector in [
                            'div.post-content',
                            'div.entry-content', 
                            'div.tt-content',
                            'div.content-inner',
                            'article div.post-content', 
                            'div.content',
                            'article', 
                            'div.entry',
                            'div.post',
                            'main',
                            'div#content'
                        ]:
                            content_element = article_soup.select_one(selector)
                            if content_element:
                                print(f"Found content with selector '{selector}'")
                                break
                    
                    if not content_element:
                        print(f"Could not find content for: {title}")
                        text = ""
                    else:
                        # Clean content
                        for unwanted in content_element.select('script, style, nav, footer, .navigation, .comments, .related-posts'):
                            unwanted.decompose()
                        
                        text = content_element.get_text(strip=True, separator=' ')
                        print(f"Extracted {len(text)} characters of content")
                    
                    articles.append({
                        'title': title,
                        'link': link,
                        'text': text,
                        'image': image
                    })
                    print(f"Successfully added article: {title}")
                    
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
                    
            print(f"Total articles found after filtering: {len(articles)}")
            return articles
            
        # Last resort - direct HTML search
        print("Attempting direct HTML pattern matching...")
        
        # Try to find title patterns directly in the HTML
        title_patterns = [
            r'<[^>]*class="[^"]*tt-post-title[^"]*"[^>]*>(.*?)</[^>]*>',
            r'<h\d[^>]*>(.*?)</h\d>',
            r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
        ]
        
        all_matches = []
        
        for pattern in title_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            if matches:
                print(f"Found {len(matches)} potential titles with pattern: {pattern}")
                all_matches.extend(matches)
                
        if all_matches:
            # Try to extract titles and links from the matches
            for match in all_matches:
                try:
                    # Break the loop if we've reached the limit
                    if len(articles) >= self.article_limit:
                        break
                    
                    # Extract text from the match
                    if isinstance(match, tuple):
                        # If the pattern captured multiple groups
                        link = match[0]
                        title_html = match[1]
                    else:
                        # If the pattern captured just one group (the title)
                        title_html = match
                        
                        # Try to find a nearby link
                        link_pattern = f'<a[^>]*href="([^"]+)"[^>]*>{re.escape(title_html)}</a>'
                        link_match = re.search(link_pattern, html_content, re.DOTALL)
                        if link_match:
                            link = link_match.group(1)
                        else:
                            # Can't find a link, skip this match
                            continue
                    
                    # Parse the HTML to get clean text
                    title = BeautifulSoup(title_html, 'html.parser').get_text(strip=True)
                    if not title:
                        continue
                        
                    # Make URL absolute
                    if not link.startswith('http'):
                        if link.startswith('/'):
                            base_domain = '/'.join(self.base_url.split('/')[:3])
                            link = base_domain + link
                        else:
                            link = f"{self.base_url.rstrip('/')}/{link.lstrip('/')}"
                            
                    print(f"Found article via direct HTML extraction: {title} - {link}")
                    
                    # Check keywords
                    if self.keywords and not any(keyword.lower() in title.lower() for keyword in self.keywords):
                        print(f"Skipping article (no matching keywords): {title}")
                        continue
                        
                    # Fetch article content
                    time.sleep(1)
                    article_html = self.fetch_html(link)
                    if not article_html:
                        continue
                        
                    # Parse the article content
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    
                    # Extract the featured image
                    image = self.extract_image(article_soup, link)
                    
                    # Look for content using multiple selectors
                    content_element = article_soup.find(class_='tt-blog-content')
                    
                    if not content_element:
                        content_element = article_soup.select_one('div.content, div.entry-content, article')
                        
                    if content_element:
                        text = content_element.get_text(strip=True, separator=' ')
                    else:
                        text = ""
                        
                    articles.append({
                        'title': title,
                        'link': link,
                        'text': text,
                        'image': image
                    })
                    
                except Exception as e:
                    print(f"Error processing match: {e}")
                    continue
                    
        # Return the articles we found
        print(f"Total articles found after filtering: {len(articles)}")
        return articles