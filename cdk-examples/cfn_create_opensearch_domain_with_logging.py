#!/usr/bin/env python
# __author__ = "Prashant Agrawal"

# References:
# https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_opensearchservice/CfnDomain.html
# https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_logs/CfnResourcePolicy.html
# https://docs.aws.amazon.com/cdk/api/v1/python/aws_cdk.aws_logs/CfnLogGroup.html

from aws_cdk import (
    aws_opensearchservice as opensearchservice,
    Aws, CfnOutput, Stack, RemovalPolicy, SecretValue, Duration,
    aws_logs as logs
)
from constructs import Construct
import random
import string

# OpenSearch specific constants, change this config if you would like you to change instance type, count and size
DOMAIN_NAME = 'opensearch-stack-demo'
DOMAIN_ADMIN_UNAME='opensearch'
DOMAIN_ADMIN_PW=''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(13)) + random.choice(string.ascii_lowercase) + random.choice(string.ascii_uppercase) + random.choice(string.digits) + "!"
DOMAIN_VERSION="OpenSearch_2.3"
DOMAIN_DATA_NODE_INSTANCE_TYPE='m6g.large.search'
DOMAIN_DATA_NODE_INSTANCE_COUNT=2
DOMAIN_INSTANCE_VOLUME_SIZE=100
DOMAIN_AZ_COUNT=2


## By default opensearch stack will be setup without dedicated master node, to have dedicated master node in stack do change the number of nodes and type (if needed)
## Maximum Master Instance count supported by service is 5, so either have 3 or 5 dedicated node for master
DOMAIN_MASTER_NODE_INSTANCE_TYPE='c6g.large.search'
DOMAIN_MASTER_NODE_INSTANCE_COUNT=3

class OpenSearchStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Setup Log Groups for Amazon OpenSearch Service
        search_slow_log_group = logs.CfnLogGroup(self, "SEARCH_SLOW_LOGS",
                                         log_group_name="/aws/OpenSearchService/domains/opensearch-stack-demo/search-logs",
                                         retention_in_days=3653
                                         )

        index_slow_log_group = logs.CfnLogGroup(self, "INDEX_SLOW_LOGS",
                                         log_group_name="/aws/OpenSearchService/domains/opensearch-stack-demo/index-logs",
                                         retention_in_days=3653
                                         )

        application_log_group = logs.CfnLogGroup(self, "ES_APPLICATION_LOGS",
                                         log_group_name="/aws/OpenSearchService/domains/opensearch-stack-demo/application-logs",
                                         retention_in_days=3653
                                         )

        audit_log_group = logs.CfnLogGroup(self, "AUDIT_LOGS",
                                         log_group_name="/aws/OpenSearchService/domains/opensearch-stack-demo/audit-logs",
                                         retention_in_days=3653
                                         )

        # Setup Resource Policy
        cfn_resource_policy = logs.CfnResourcePolicy(self, "MyCfnResourcePolicy",
                                                     policy_document="{ \"Version\": \"2012-10-17\", \"Statement\": [ {\"Effect\": \"Allow\", \"Principal\": { \"Service\": [ \"es.amazonaws.com\" ] }, \"Action\":[\"logs:PutLogEvents\", \"logs:CreateLogStream\"], \"Resource\": [\"arn:aws:logs:*:*\"] } ] }",
                                                     policy_name="opensearch-stack-demo-policy"
                                                     )

        # Setup Amazon OpenSearch Service Domain
        cfn_domain = opensearchservice.CfnDomain(self, "MyCfnDomain",
                                                 cluster_config=opensearchservice.CfnDomain.ClusterConfigProperty(
                                                   dedicated_master_count=DOMAIN_MASTER_NODE_INSTANCE_COUNT,
                                                   dedicated_master_enabled=True,
                                                   dedicated_master_type=DOMAIN_MASTER_NODE_INSTANCE_TYPE,
                                                   instance_count=DOMAIN_DATA_NODE_INSTANCE_COUNT,
                                                   instance_type=DOMAIN_DATA_NODE_INSTANCE_TYPE,
                                                   zone_awareness_config=opensearchservice.CfnDomain.ZoneAwarenessConfigProperty(
                                                     availability_zone_count=DOMAIN_AZ_COUNT
                                                   ),
                                                   zone_awareness_enabled=True
                                                 ),
                                                 advanced_security_options=opensearchservice.CfnDomain.AdvancedSecurityOptionsInputProperty(
                                                   enabled=True,
                                                   internal_user_database_enabled=True,
                                                   master_user_options=opensearchservice.CfnDomain.MasterUserOptionsProperty(
                                                     master_user_name=DOMAIN_ADMIN_UNAME,
                                                     master_user_password=DOMAIN_ADMIN_PW
                                                   )
                                                 ),
                                                 domain_endpoint_options=opensearchservice.CfnDomain.DomainEndpointOptionsProperty(
                                                   enforce_https=True
                                                 ),
                                                 domain_name=DOMAIN_NAME,
                                                 ebs_options=opensearchservice.CfnDomain.EBSOptionsProperty(
                                                   ebs_enabled=True,
                                                   volume_size=DOMAIN_INSTANCE_VOLUME_SIZE,
                                                   volume_type="gp2"
                                                 ),
                                                 encryption_at_rest_options=opensearchservice.CfnDomain.EncryptionAtRestOptionsProperty(
                                                   enabled=True
                                                 ),
                                                 engine_version=DOMAIN_VERSION,
                                                 log_publishing_options={
                                                   "SEARCH_SLOW_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                                                     cloud_watch_logs_log_group_arn=search_slow_log_group.attr_arn,
                                                     enabled=True
                                                   ),
                                                   "INDEX_SLOW_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                                                     cloud_watch_logs_log_group_arn=index_slow_log_group.attr_arn,
                                                     enabled=True
                                                   ),
                                                   "ES_APPLICATION_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                                                     cloud_watch_logs_log_group_arn=application_log_group.attr_arn,
                                                     enabled=True
                                                   ),
                                                   "AUDIT_LOGS": opensearchservice.CfnDomain.LogPublishingOptionProperty(
                                                     cloud_watch_logs_log_group_arn=audit_log_group.attr_arn,
                                                     enabled=True
                                                   ),
                                                 },
                                                 node_to_node_encryption_options=opensearchservice.CfnDomain.NodeToNodeEncryptionOptionsProperty(
                                                   enabled=True
                                                 )
                                                 )
        cfn_domain.add_depends_on(cfn_resource_policy)
        cfn_domain.add_depends_on(search_slow_log_group)
        cfn_domain.add_depends_on(index_slow_log_group)
        cfn_domain.add_depends_on(audit_log_group)
        cfn_domain.add_depends_on(application_log_group)

        CfnOutput(self, "AdminUser",
                  value=DOMAIN_ADMIN_UNAME,
                  description="User Name for Amazon OpenSearch Service")

        CfnOutput(self, "AdminPassword",
                  value=DOMAIN_ADMIN_PW,
                  description="User Password for Amazon OpenSearch Service")


