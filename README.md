# Document Retrieval System

This project implements a document retrieval system for chat applications to use as context. It provides a backend API for retrieving documents based on similarity search.

## Features

- RESTful API for document retrieval
- Similarity search using Sentence Transformers and Chroma vector store
- Rate limiting for API requests
- Response caching for improved performance
- Background thread for scraping news articles
- Dockerized application

## Setup and Running

1. Clone the repository:
   ```
   git clone [repository-url]
   cd [repository-name]
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Docker

To build and run the Docker container:

```bash
docker build -t document-retrieval .
docker run -p 5000:5000 document-retrieval
```

## API Endpoints

1. `/health`: Returns a status check for the API to check if it is active.
2. `/search`: Performs a similarity search based on the given query and returns a list of top results.

   Parameters:
   - `text` (required): The query text
   - `top_k` (optional, default=5): Number of results to return
   - `threshold` (optional, default=0.5): Similarity threshold for results
   - `user_id` (required): Identifier for rate limiting

## Using the API with curl

Here's a simple tutorial on how to use the API with curl:

1. Health Check:
   ```
   curl http://localhost:5000/health
   ```

2. Perform a Search:
   ```
   curl -G http://localhost:5000/search \
     --data-urlencode "user_id=user123" \
     --data-urlencode "text=latest stock market trends" \
     --data-urlencode "top_k=3" \
     --data-urlencode "threshold=0.6"
   ```

3. Rate Limit Example:
   ```
   curl -G http://localhost:5000/search \
     --data-urlencode "user_id=user123" \
     --data-urlencode "text=test query"
   ```
   Note: You'll receive a rate limit error if you exceed 5 requests per hour for a user.

## Adjustments

- Ensure the server is running before making requests.
- Replace `localhost:5000` with the appropriate host and port if deployed elsewhere.
- The `user_id` parameter is required for all `/search` requests to enforce rate limiting.
- Adjust `top_k` and `threshold` parameters to fine-tune your search results.

## Caching Strategy

We use Time-to-Live (TTL) caching for improved performance and efficient rate limiting. TTL caching automatically expires entries after a given time which ensures that the data is fresh as well as ensures memory efficiency.

## Background Scraping

The application runs a background thread that periodically scrapes news articles and updates the vector store, ensuring access to fresh, relevant content.

## Logging

The application uses Python's logging module to record events, errors, and performance metrics for monitoring and debugging.

## Notes

- Ensure that there sufficient disk space for the Chroma vector store.
- The application is set to run in debug mode by default. For production, disable debug mode.

