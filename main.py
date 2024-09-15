from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from sentence_transformers import SentenceTransformer
import time
import threading
from scraper import scrape_articles
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import logging
from functools import wraps
from cachetools import TTLCache
import random

app = Flask(__name__)
api = Api(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the encoder model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Langchain components
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")

# In-memory cache for rate limiting
user_request_cache = TTLCache(maxsize=1000, ttl=3600)

# Response cache
response_cache = TTLCache(maxsize=100, ttl=300)  # Cache for 5 minutes

def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = request.args.get('user_id')
        if not user_id:
            return {"error": "user_id is required"}, 400
        
        current_count = user_request_cache.get(user_id, 0)
        if current_count >= 5:
            return {"error": "Rate limit exceeded"}, 429
        
        user_request_cache[user_id] = current_count + 1
        return func(*args, **kwargs)
    return wrapper

class HealthCheck(Resource):
    def get(self):
        responses = ["I'm alive!", "All systems operational.", "Ready to serve!", "Healthy and happy!"]
        return {"status": random.choice(responses)}, 200

class Search(Resource):
    @rate_limit
    def get(self):
        text = request.args.get('text')
        top_k = int(request.args.get('top_k', 5))
        threshold = float(request.args.get('threshold', 0.5))

        # Check cache
        cache_key = f"{text}_{top_k}_{threshold}"
        cached_result = response_cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {text}")
            return cached_result

        start_time = time.time()

        try:
            # Perform the search using Langchain
            results = vector_store.similarity_search_with_score(text, k=top_k)

            # Filter results based on threshold and format the output
            filtered_results = [
                {
                    "id": result[0].metadata.get('link', ''),
                    "title": result[0].metadata.get('title', ''),
                    "content": result[0].page_content,
                    "similarity": 1 - result[1]  # Convert distance to similarity
                }
                for result in results
                if 1 - result[1] >= threshold
            ]

            end_time = time.time()
            inference_time = end_time - start_time

            response = {
                "results": filtered_results,
                "inference_time": inference_time
            }

            # Cache the response
            response_cache[cache_key] = response

            logger.info(f"Search completed for query: {text}, inference time: {inference_time:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return {"error": "An error occurred during the search"}, 500

def background_scraper():
    while True:
        try:
            scrape_articles()
            logger.info("Background scraping completed")
        except Exception as e:
            logger.error(f"Error in background scraper: {str(e)}")
        time.sleep(3600)  # Sleep for 1 hour

api.add_resource(HealthCheck, '/health')
api.add_resource(Search, '/search')

if __name__ == '__main__':
    # Start the background scraper thread
    scraper_thread = threading.Thread(target=background_scraper, daemon=True)
    scraper_thread.start()
    app.run(debug=True)