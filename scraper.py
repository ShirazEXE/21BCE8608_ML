import requests
from bs4 import BeautifulSoup
import time
import logging
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Langchain components
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")

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
                existing_docs = vector_store.similarity_search(article['link'], k=1)
                if not existing_docs or existing_docs[0].metadata['link'] != article['link']:
                    # Prepare the document for Chroma
                    doc = Document(
                        page_content=f"{article['title']}\n\n{article['content']}",
                        metadata={
                            'title': article['title'],
                            'link': article['link'],
                            'source': source['name'],
                            'timestamp': time.time()
                        }
                    )
                    # Add the document to ChromaDB
                    vector_store.add_documents([doc])
                    logger.info(f"Inserted new article: {article['title']}")
                
            logger.info(f"Scraped {len(articles)} articles from {source['name']}")
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {str(e)}")

def run_scraper(interval=3600):
    while True:
        scrape_articles()
        vector_store.persist()  # Save changes
        time.sleep(interval)

if __name__ == '__main__':
    run_scraper()