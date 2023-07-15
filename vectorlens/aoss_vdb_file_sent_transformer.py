from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import json
import boto3

# python3 -m pip install boto3 requests_aws4auth opensearch-py sentence_transformers flask gevent

host = '0n2qav61946ja1c7k2a1.us-east-2.aoss.amazonaws.com' # OpenSearch Serverless collection endpoint
region = 'us-east-2' # e.g. us-west-2

service = 'aoss'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,
session_token=credentials.token)

# Create an OpenSearch client
client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
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

    # Read and index the JSON data
    with open(json_file_path, 'r') as file:
        for line in file:
            json_data = json.loads(line)

            product_description = json_data['product_description']
            # print(f"product_description: {product_description}")

            v_product_description = model.encode([product_description])[0].tolist()
            # v_product_description = model.encode([product_description])[0].tolist()[:vector_size]

            # Pad or truncate vector to vector size if necessary
            # v_product_description += [0.0] * max(0, vector_size - len(v_product_description))
            # v_product_description = v_product_description[:vector_size]
            json_data['v_product_description'] = v_product_description


            question_text = json_data['question_text']
            v_question_text = model.encode([question_text])[0].tolist()
            # v_question_text = model.encode([question_text])[0].tolist()[:vector_size]
            # print(f"question_text: {question_text}")

            # Pad or truncate vector to vector size if necessary
            # v_question_text += [0.0] * max(0, vector_size - len(v_question_text))
            # v_question_text = v_question_text[:vector_size]
            json_data['v_question_text'] = v_question_text
            
            # Prepare bulk request
            actions.append(action)
            actions.append(json_data.copy())

            if(i > 200 ):
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

# full_load("amazon_pqa_fashion_sneakers.json", "vector_sneakers")

# wget https://amazon-pqa.s3.amazonaws.com/amazon_pqa_headsets.json
# full_load("amazon_pqa_headsets.json", "vector_headsets")

full_load("amazon_pqa_games.json", "vector_games")

print ("Ingestion Completed")

# If we are seeing -1 to 1 use cosine similarity 

# If we have - infinite to + infinite then use l2





