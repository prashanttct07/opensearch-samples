from flask import Flask, render_template, request
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import json
import boto3
from sentence_transformers import SentenceTransformer
from gevent.pywsgi import WSGIServer
import logging
from datetime import datetime

# .env/bin/python -m pip install boto3 flask opensearch-py requests_aws4auth sentence_transformers gevent

host = 'search-demo.aos.us-west-2.on.aws' # OpenSearch endpoint
region = 'us-west-2' # e.g. us-west-2
service = 'es'
# Specify index name
index_name = 'vector-*'


# Load the SentenceTransformer model
model_name = 'sentence-transformers/msmarco-distilbert-base-tas-b'
model = SentenceTransformer(model_name)

# Set the desired vector size
vector_size = 768

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,
                   session_token=credentials.token)
auth = ('user', 'pwd')

# Create an OpenSearch client
client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    timeout = 300,
    http_auth = auth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)



app = Flask(__name__)

# Configure logging
logger = logging.getLogger('werkzeug') # grabs underlying WSGI logger
handler = logging.FileHandler('vectorlens.log') # creates handler for the log file
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler) # adds handler to the werkzeug WSGI logger




@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])


def search():
    query = request.form['query']
    dataset = request.form['dataset']
    # star wars electronics art 
    # I am looking to buy sneakers
    # Michael Jordan Boots
    # Michael Jordan Sandals
    # Find me product similar to blue sneaker for women

    if dataset == 'sneakers':
        index_name = "vector_sneakers"
    elif dataset == 'headsets':
        index_name = "vector_headsets"
    elif dataset == 'games':
        index_name = "vector_games"

    q_vector = model.encode(query).tolist()
    # print(q_vector)

    approx_knn_query = {
        "size": 3,
        "_source": {
            "includes": [
                "item_name",
                "product_description"
            ]
        },
        "query": {
            "knn": {
                "v_product_description": {
                    "vector": q_vector,
                    "k": vector_size
                }
            }
        }
    }


    # print (approx_knn_query)

    response = client.search(
        body = approx_knn_query,
        index = index_name
    )
    # print('\nSearch results:')

    # print(response)

    # Extract relevant information from the search result
    hits = response['hits']['hits']
    search_results = [{'item_name': hit['_source']['item_name'], 'product_description' : hit['_source']['product_description']} for hit in hits]


    kw_query = {
        "size": 3,
        "_source": {
            "includes": [
                "item_name",
                "product_description"
            ]
        },
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["product_description"]
            }
        }
    }

    kw_response = client.search(
        body = kw_query,
        index = index_name
    )

    # Extract relevant information from the search result
    kw_hits = kw_response['hits']['hits']
    kw_search_results = [{'item_name': hit['_source']['item_name'], 'product_description' : hit['_source']['product_description']} for hit in kw_hits]


    return render_template('search.html', query=query, results=search_results, kw_results=kw_search_results)


if __name__ == '__main__':
    app.run()
    http_server = WSGIServer(('127.0.0.1', 5000), app)
    # http_server = WSGIServer(('0.0.0.0', 80), app)
    # http_server.serve_forever()




