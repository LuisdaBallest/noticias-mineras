import streamlit as st
from scrapers.website_one_scraper import WebsiteOneScraper
from scrapers.website_two_scraper import WebsiteTwoScraper
from summarizer.openai_summarizer import OpenAISummarizer

def main():
    st.title("Noticias Mineras México")
    
    keywords = st.text_input("Introduce palabras clave, separadas por coma:")
    
    if st.button("Scrape News"):
        if keywords:
            keywords_list = [keyword.strip() for keyword in keywords.split(",")]
            articles = []

            # Scrape articles from both websites
            website_one_scraper = WebsiteOneScraper()
            website_two_scraper = WebsiteTwoScraper()

            articles.extend(website_one_scraper.scrape(keywords_list))
            articles.extend(website_two_scraper.scrape(keywords_list))

            if articles:
                summarizer = OpenAISummarizer()
                summaries = [summarizer.summarize(article) for article in articles]

                st.subheader("Notas resumidas:")
                for summary in summaries:
                    st.write(summary)
            else:
                st.write("No se encontraron noticias para las palabras clave proporcionadas.")
        else:
            st.write("Por favor, introduzca palabras clave para buscar noticias.")

if __name__ == "__main__":
    main()