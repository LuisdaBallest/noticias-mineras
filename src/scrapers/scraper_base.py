class Scraper:
    def __init__(self, base_url, keywords):
        self.base_url = base_url
        self.keywords = keywords

    def fetch_html(self, url):
        import requests
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def parse_html(self, html):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def scrape(self):
        raise NotImplementedError("Subclasses should implement this method")