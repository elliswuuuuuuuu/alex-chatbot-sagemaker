#!/usr/bin/env python3
import os
import aws_cdk as cdk
from lib.ss_vpcstack import VpcStack
from lib.ss_lambdastack import LambdaStack
from lib.ss_lambdavpcstack import LambdaVPCStack
from lib.ss_osstack import OpenSearchStack
from lib.ss_osvpcstack import OpenSearchVPCStack
from lib.ss_notebook import NotebookStack
from lib.ss_botstack import BotStack
from lib.ss_kendrastack import KendraStack
from lib.ss_bedrockstack import BedrockStack

ACCOUNT = os.getenv('AWS_ACCOUNT_ID', '')
REGION = os.getenv('AWS_REGION', '')
AWS_ENV = cdk.Environment(account=ACCOUNT, region=REGION)
env = AWS_ENV
print(env)
app = cdk.App()

searchstack = OpenSearchStack(app, "OpenSearchStack", env=env, description="Guidance for Custom Search of an Enterprise Knowledge Base on AWS - (SO9251)")
search_engine_key = searchstack.search_domain_endpoint
lambdastack = LambdaStack(app, "LambdaStack", search_engine_key=search_engine_key, env=env, description="Guidance for Custom Search of an Enterprise Knowledge Base on AWS - (SO9251)")
lambdastack.add_dependency(searchstack)
bedrockstack = BedrockStack( app, "BedrockStack", env=env)
notebookstack = NotebookStack(app, "NotebookStack", search_engine_key=search_engine_key, env=env, description="Guidance for Custom Search of an Enterprise Knowledge Base on AWS - (SO9251)")
notebookstack.add_dependency(searchstack)

app.synth()
