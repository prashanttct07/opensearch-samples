from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import json
import boto3
import time

# .env/bin/python -m pip install boto3 flask opensearch-py requests_aws4auth sentence_transformers gevent

host = 'search-demo.aos.us-west-2.on.aws' # OpenSearch endpoint
region = 'us-west-2' # e.g. us-west-2

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,
session_token=credentials.token)

auth = ('user', 'pwd')
# Create an OpenSearch client
client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = auth,
    timeout = 300,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)



# Load the SentenceTransformer model
model_name = 'sentence-transformers/msmarco-distilbert-base-tas-b'
model = SentenceTransformer(model_name)

# Set the desired vector size
vector_size = 768


def full_load(json_file_path, index_name):
    actions = []
    i = 0
    j = 0
    action = {"index": {"_index": index_name}}


    # if index_name exists in collection, don't run this again 
    # create a new index
    if not client.indices.exists(index=index_name):
        index_body = {
            "settings": {
                "index.knn": "true"
            },
            "mappings": {
                "properties": {
                    "v_product_description": {
                        "type": "knn_vector",
                        "dimension": vector_size,
                        "method": {
                        "name": "hnsw",
                        "engine": "faiss",
                        "space_type": "l2"
                        }
                    },
                    "v_question_text": {
                        "type": "knn_vector",
                        "dimension": vector_size,
                        "method": {
                        "name": "hnsw",
                        "engine": "faiss",
                        "space_type": "l2"
                        }
                    }
                }
            }
        }

        client.indices.create(
            index=index_name, 
            body=index_body
        )
        time.sleep(5)

    # Read and index the JSON data
    with open(json_file_path, 'r') as file:
        for line in file:
            json_data = json.loads(line)

            product_description = json_data['product_description']
            v_product_description = model.encode([product_description])[0].tolist()
            json_data['v_product_description'] = v_product_description

            question_text = json_data['question_text']
            v_question_text = model.encode([question_text])[0].tolist()
            json_data['v_question_text'] = v_question_text
            
            # Prepare bulk request
            actions.append(action)
            actions.append(json_data.copy())

            if(i > 100 ):
                # Index Documents
                # response = client.index(
                #     index = index_name,
                #     body = json_data
                # )
                client.bulk(body=actions)
                print(f"bulk request sent with size: {i}")
                print(f"total docs sent so far: {j}")
                i = 0
            i += 1
            j += 1 


            

# Read and index the JSON data
# https://amazon-pqa.s3.amazonaws.com/readme.txt

# wget https://amazon-pqa.s3.amazonaws.com/amazon_pqa_fashion_sneakers.json
full_load("amazon_pqa_fashion_sneakers.json", "vector_sneakers")

# wget https://amazon-pqa.s3.amazonaws.com/amazon_pqa_headsets.json
# full_load("amazon_pqa_headsets.json", "vector_headsets")

# full_load("amazon_pqa_games.json", "vector_games")

print ("Ingestion Completed")




