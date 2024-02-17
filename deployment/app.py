#!/usr/bin/env python3
import os
import aws_cdk as cdk
from lib.ss_lambdastack import LambdaStack
from lib.ss_osstack import OpenSearchStack
from lib.ss_notebook import NotebookStack
from lib.ss_botstack import BotStack


ACCOUNT = os.getenv('AWS_ACCOUNT_ID', '')
REGION = os.getenv('AWS_REGION', '')
AWS_ENV = cdk.Environment(account=ACCOUNT, region=REGION)
env = AWS_ENV
print(env)
app = cdk.App()

searchstack = OpenSearchStack(app, "OpenSearchStack", env=env,
                              description="alex chatbot Knowledge Base on AWS")
search_engine_key = searchstack.search_domain_endpoint
lambdastack = LambdaStack(app, "LambdaStack",
                          search_engine_key=search_engine_key, env=env,
                          description="alex chatbot lambda")
lambdastack.add_dependency(searchstack)
notebookstack = NotebookStack(app, "NotebookStack",
                              search_engine_key=search_engine_key, env=env,
                              description="alex chatbot notebook")
notebookstack.add_dependency(searchstack)


if('bot' in app.node.try_get_context("extension")):
    botstack = BotStack(app, "BotStack", env=env, description="alex bot")
    botstack.add_dependency(lambdastack)


app.synth()
