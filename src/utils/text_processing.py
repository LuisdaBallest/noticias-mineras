def clean_text(text):
    # Remove unwanted characters and whitespace
    cleaned_text = ' '.join(text.split())
    return cleaned_text

def format_article(article):
    # Format the article for better readability
    formatted_article = f"Title: {article['title']}\n\n{article['content']}"
    return formatted_article

def extract_keywords(text, keywords):
    # Extract keywords from the text
    extracted_keywords = [word for word in keywords if word in text]
    return extracted_keywords