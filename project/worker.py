import os
import time
import nltk
from celery import Celery
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector
import redis
import json

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

# database connection
db_config = {
    'host': 'mysql',
    'user': 'root',
    'password': '123456',
    'database': 'machine_learning'
}

conn = mysql.connector.connect(**db_config)

@celery.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True

def calculate_cosine_similarities(products, redis_key = None):
    # Nltk downloads
    nltk.download('stopwords')

    # Preprocess data
    vectorizer = TfidfVectorizer(stop_words='english') 
    descriptions = [(product['name'] + product['description'] + product['category']) for product in products]
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    # Calculate cosine similarities
    cosine_similarities = cosine_similarity(tfidf_matrix, tfidf_matrix)


    return cosine_similarities

@celery.task(name="get_product_recommendation")
def get_product_recommendation(product_id: int):
    # Getting cached recomendation
    cached_recomendations_data = redis_client.get('product-recomendation-' + str(product_id))
    if cached_recomendations_data is not None:
        cached_recomendations_data_string = cached_recomendations_data.decode('utf-8')
        cached_recomendations = json.loads(cached_recomendations_data_string)
        product_ids = [cached_recomendation["product_id"] for cached_recomendation in cached_recomendations]

        cursor = conn.cursor()
        placeholders = ",".join(map(str, product_ids))
        query = f"SELECT id, name, description, category FROM products WHERE id IN ({placeholders})"
        cursor.execute(query)

        results = cursor.fetchall()
        product_recomendations = []
        for row in results:
            cached_recomendation = next((e for e in cached_recomendations if e["product_id"] == row[0]), None)
            product_recomendation = {
                "product": {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'category': row[3]
                },
                "score": cached_recomendation["score"],
            }
            product_recomendations.append(product_recomendation)

        sorted_product_recommendations = sorted(product_recomendations, key=lambda x: x["score"], reverse=True)

        return sorted_product_recommendations

    # Getting product datas
    cursor = conn.cursor()

    query = "SELECT id, name, description, category FROM products"
    cursor.execute(query)

    results = cursor.fetchall()
    products = []
    for row in results:
        product = {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'category': row[3]
        }
        products.append(product)

    # Nltk downloads
    nltk.download('stopwords')

    # Preprocess data
    vectorizer = TfidfVectorizer(stop_words='english') 
    descriptions = [(product['name'] + product['description'] + product['category']) for product in products]
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    # Calculate cosine similarities
    cosine_similarities = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Get recommendations
    idx = next((index for (index, d) in enumerate(products) if d["id"] == product_id), None)
    if idx is None:
        return "Product not found"
    
    sim_scores = list(enumerate(cosine_similarities[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    recommendations = [{
        "product": products[i[0]],
        "score":i[1]
    } for i in sim_scores if i[0] != idx]

    # Save to redis
    recomendation_cache = [{
        "score": recomendation["score"],
        "product_id": recomendation["product"]["id"]
    } for recomendation in recommendations]
    recommendations_cache_json = json.dumps(recomendation_cache)
    recomendation_key = 'product-recomendation-' + str(product_id)
    redis_client.set(recomendation_key, recommendations_cache_json)
    redis_client.expire(recomendation_key, 604800)
    
    return recommendations