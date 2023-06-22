################################################################################
#                              Python Script                                   #
#                                                                              #
# Use this script to delete data older than d days for p prefix                #
#                                                                              #
# Change History                                                               #
# 06/22/2023  Prashant Agrawal                                                 #
#                                                                              #
# usage:                                                                       #
# python3 cleanup.py -e <host> -r <region> -d <retenion days> -p <prefix>      #                                                                              #
################################################################################

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3, time, sys
import sys, getopt
from datetime import datetime
import io
import time


def cleanUp(client, days, prefix):
    # get the current time in millis since the epoch
    epoch_ms = time.time() * 1000
    retention_in_ms = days * 24 * 60 * 60 * 1000

    cat_indices = client.cat.indices(index=prefix+"*", h="index", s="index")
    # print(cat_indices)

    # Traverse index and get creation date
    index = io.StringIO(cat_indices)
    for i in index:
        settings = client.indices.get_settings(index=i.strip())
        creation_date = settings[i.strip()]["settings"]["index"]["creation_date"]
        # print (creation_date)
        index_age = epoch_ms - int(creation_date)
        # print(index_age)

        if index_age > retention_in_ms:
            client.indices.delete(index=i.strip())
            print ("Deleting index " + i.strip() + " as this is older than configured retention of " + str(days) + " days")
        else:
            print ("Keeping index " + i.strip() + " as this is within configured retention of " + str(days) + " days")
     
def main(argv):
    now = datetime.now()
    host = ''  # OpenSearch Service/Collection ednpoint without https
    region = ''  # Region
    prefix = 'opensearch'  # Default is opensearch
    service = "aoss"
    days = 30  # Default days = 30, to delete any index older than 30 days
    # Usage 
    # python3 cleanup.py -e b0tr7856fkx6vn24ys02.us-east-2.aoss.amazonaws.com -r us-east-2 -d 10 -p opensearch

    opts, args = getopt.getopt(argv, "d:e:r:p:")
    for opt, arg in opts:
        if opt == '-d':
            days = int(arg)
        elif opt == '-e':
            host = arg
        elif opt == '-r':
            region = arg
        elif opt == '-p':
            prefix = arg

    if host == '':
        print("required argument -e <Amazon OpenSearch Service/Serverless endpoint>")
        exit()

    if region == '':
        print("required argument -r <Amazon OpenSearch Service/Serverless region>")
        exit()

    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(region=region, service=service,
                       refreshable_credentials=credentials)

    # Build the OpenSearch client
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        timeout=300,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    if service == 'aoss':
        print(
            f"{str(now)}: OpenSearch Clean Up - Clean Up started for OpenSearch Serverless Collection: {host}, in Region {region}, with prefix {prefix} and retention days as {days} \n")
    elif service == 'es':
        print(
            f"{str(now)}: OpenSearch Clean Up - Clean Up started for OpenSearch Service Domain: {host}, in Region {region}, with prefix {prefix} and retention days as {days} \n")

    cleanUp(client, days, prefix)

# Crontab for every 4 hrs
# 0 */4 * * * python3 /home/ec2-user/environments/aoss_cleanup.py -e <host> -r <region> -d <retenion_days> -p <prefix> >> /home/ec2-user/environments/cleanup_log.txt

if __name__ == '__main__':
    main(sys.argv[1:])

