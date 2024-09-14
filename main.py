from flask import Flask
from flask_restful import Api, Resource
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from bson.binary import Binary
import pickle
from threading import Thread
from scraper import scrape_articles, run_scraper

app = Flask(__name__)
api = Api(app)

#Implementing connection to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['document_retrieval']
documents = db['documents']
user = db['user']

#Initialization of Sentence Transformer encoder
model = SentenceTransformer('all-MiniLM-L6-v2')

# Start background scraper
scraper_thread = Thread(target=run_scraper)
scraper_thread.start()

#Class to check if API is Active
class HealthCheck(Resource):
    def get(self):
        return{"status":"ok"}, 200


def encode_storeDocument(content):
    vector = model.encode([content])[0]
    doc_id = documents.insert_one({
        "content": content,
        "vector": Binary(pickle.dumps(vector, protocol=2)),
    }).inserted_id
    return doc_id

#Background Scraper for finding articles to be encoded and stored
def bg_scraper():
    while True:
        try:
            scrape_articles()
            #Each new article is encoded and then stored
            for d in documents.find({'vector': {'$exist':False}}):
                encode_storeDocument(d)
        except Exception as e:
            print(f"Error in background scraper: {{str(e)}}")
        time.sleep(3600) #sleep for 1 hour



api.add_resource(HealthCheck, '/health')
#api.add_resource(Search, '/search')

if __name__ == '__main__':
    app.run(debug=True)
