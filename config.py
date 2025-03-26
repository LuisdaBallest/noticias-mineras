import os

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    WEBSITE_ONE_URL = "https://www.websiteone.com/mining-news"
    WEBSITE_TWO_URL = "https://www.websitetwo.com/mining-news"
    KEYWORDS = ["mining", "gold", "copper", "silver", "minerals"]
    SUMMARY_LENGTH = 5  # Number of lines for the summary