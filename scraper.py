import requests
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['document_retrieval']
documents = db['documents']

# List of news sources with their URLs and parsing functions
NEWS_SOURCES = [
    
    {
        'name': 'Economic Times',
        'url': 'https://economictimes.indiatimes.com/markets/stocks/news',
        'parser': lambda soup: [
            {
                'title': article.find('a').text.strip(),
                'content': article.find('p').text.strip() if article.find('p') else '',
                'link': 'https://economictimes.indiatimes.com' + article.find('a')['href']
            }
            for article in soup.find_all('div', class_='eachStory')
        ]
    }
]

def scrape_articles():
    for source in NEWS_SOURCES:
        try:
            response = requests.get(source['url'], headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = source['parser'](soup)
            
            for article in articles:
                # Check if article already exists
                existing_article = documents.find_one({'link': article['link']})
                if not existing_article:
                    article['source'] = source['name']
                    article['timestamp'] = time.time()
                    documents.insert_one(article)
                    logger.info(f"Inserted new article: {article['title']}")
                
            logger.info(f"Scraped {len(articles)} articles from {source['name']}")
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {str(e)}")

def run_scraper(interval=3600):
    while True:
        scrape_articles()
        time.sleep(interval)

if __name__ == '__main__':
    run_scraper()
