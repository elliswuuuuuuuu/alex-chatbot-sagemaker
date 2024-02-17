import json

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  aws_ec2,
  aws_iam as _iam,
  aws_opensearchservice,
  aws_secretsmanager
)
from constructs import Construct

class OpenSearchStack(Stack):

  def __init__(self, scope: Construct, construct_id: str , **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)


    ops_domain_name = 'smartsearch'

    master_user_secret = aws_secretsmanager.Secret(self, "OpenSearchMasterUserSecret",
      generate_secret_string=aws_secretsmanager.SecretStringGenerator(
        secret_string_template=json.dumps({"username": "admin"}),
        generate_string_key="password",
        # Master password must be at least 8 characters long and contain at least one uppercase letter,
        # one lowercase letter, one number, and one special character.
        password_length=12
      ),
      secret_name = "opensearch-master-user"
    )

    ops_domain = aws_opensearchservice.Domain(self, "OpenSearch",
      domain_name=ops_domain_name,
      version=aws_opensearchservice.EngineVersion.OPENSEARCH_1_3,
      capacity={
        "master_nodes": 0,
        "master_node_instance_type": "m5.xlarge.search",
        "data_nodes": 1,
        "data_node_instance_type": "m5.xlarge.search"
      },
      ebs={
        "volume_size": 20,
        "volume_type": aws_ec2.EbsDeviceVolumeType.GP3
      },
      fine_grained_access_control=aws_opensearchservice.AdvancedSecurityOptions(
        master_user_name=master_user_secret.secret_value_from_json("username").unsafe_unwrap(),
        master_user_password=master_user_secret.secret_value_from_json("password")
      ),
      enforce_https=True,
      node_to_node_encryption=True,
      encryption_at_rest={
        "enabled": True
      },
      use_unsigned_basic_auth=True,   #default: False
      removal_policy=cdk.RemovalPolicy.DESTROY # default: cdk.RemovalPolicy.RETAIN
    )
    cdk.Tags.of(ops_domain).add('Name', 'smartsearch-ops')

    self.search_domain_endpoint = ops_domain.domain_endpoint
    self.search_domain_arn = ops_domain.domain_arn

    cdk.CfnOutput(self, 'OPSDomainEndpoint', value=self.search_domain_endpoint, export_name='OPSDomainEndpoint')
    cdk.CfnOutput(self, 'OPSDashboardsURL', value=f"{self.search_domain_endpoint}/_dashboards/", export_name='OPSDashboardsURL')