from langchain import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from typing import Dict
from datetime import datetime
import boto3
import json
import os
from langchain.chains import (
    StuffDocumentsChain,
    LLMChain,
    ReduceDocumentsChain,
    MapReduceDocumentsChain,
    ConversationChain,
    RetrievalQA
)
from langchain.prompts import PromptTemplate
from chinese_text_splitter import ChineseTextSplitter

# Must set TRANSFORMERS_CACHE in Environment Variable, otherwise hugging face will write to /home/sbx_user1051/, which is READ-ONLY
os.environ['TRANSFORMERS_CACHE'] = "/tmp"

table_name = os.environ['asr_content_table']
dynamodb_cli = boto3.client('dynamodb')
dynamodb_table = boto3.resource('dynamodb').Table(table_name)

# prompt = """
# 将会议记录总结结论，用 Markdown 列表的格式列举结论并进行详细描述，每个结论描述不少于80字。最后如果有的话，列出演讲者建议的下一步行动或行动项目。
# 会议记录内容:{text}
# 答案：
# """
# # 将会议记录总结6个结论，Markdown 列表的格式列举结论并进行详细描述，每个结论描述不少于80字。最后如果有的话，列出演讲者建议的下一步行动或行动项目。
# # 会议记录以####作为分隔符。

# combine_prompt_template = """
# 请根据{text}，总结一段摘要, 以Markdown 列表的格式列举结论并进行详细描述。
# ####{text}####
# ----
# 答案：
# """

MAP_TEMPLATE = """请根据以下的已知信息
                  {docs}
                  提出内容的核心观点，用 Markdown 列表的格式列举结论并进行详细描述，每个结论描述不少于80字。最后如果有的话，列出演讲者建议的下一步行动或行动项目。
                  答案:"""

REDUCE_TEMPLATE = """请根据以下的已知信息总结
                    {doc_summaries}
                    将这些内容提炼成主要主题的最终综合摘要, 保留核心观点、描述以及结论。以Markdown格式输出。
                    答案:"""

DOC_OVERLAP = 20

"""
    Long Text Processor
"""


class LongTextProcessor:

    def __init__(self, llm):
        self.llm = llm
        self.map_template = MAP_TEMPLATE
        self.map_prompt = PromptTemplate.from_template(self.map_template)
        self.map_chain = LLMChain(llm=self.llm, prompt=self.map_prompt)
        self.reduce_template = REDUCE_TEMPLATE
        self.reduce_prompt = PromptTemplate.from_template(self.reduce_template)
        self.reduce_chain = LLMChain(llm=self.llm, prompt=self.reduce_prompt)
        self.combine_documents_chain = StuffDocumentsChain(
            llm_chain=self.reduce_chain, document_variable_name="doc_summaries"
        )
        self.reduce_documents_chain = ReduceDocumentsChain(
            combine_documents_chain=self.combine_documents_chain,
            collapse_documents_chain=self.combine_documents_chain,
            token_max=4000,
        )
        self.map_reduce_chain = MapReduceDocumentsChain(
            llm_chain=self.map_chain,
            reduce_documents_chain=self.reduce_documents_chain,
            document_variable_name="docs",
            return_intermediate_steps=False,
        )

    def run_processing(self, text, chunk_size):
        print("Start to run MapReduce summarization...")

        text_splitter = ChineseTextSplitter(chunk_size=chunk_size, chunk_overlap=DOC_OVERLAP)
        docs = text_splitter.create_documents([text])
        split_docs = text_splitter.split_documents(docs)
        result = self.map_reduce_chain.run(split_docs)

        print(f"Processed Result: {result}")

        return result


"""
    Functions
"""


def init_model(endpoint_name: str = "pytorch-inference-llm-v1",
               region_name: str = 'us-west-2',  # os.environ['AWS_REGION'],
               temperature: float = 0):
    try:
        class ContentHandler(LLMContentHandler):
            content_type = "application/json"
            accepts = "application/json"

            def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
                input_str = json.dumps({"ask": prompt, **model_kwargs})
                return input_str.encode('utf-8')

            def transform_output(self, output: bytes) -> str:
                response_json = json.loads(output.read().decode("utf-8"))
                return response_json['answer']

        content_handler = ContentHandler()

        llm = SagemakerEndpoint(
            endpoint_name=endpoint_name,
            region_name=region_name,
            model_kwargs={"temperature": temperature},
            content_handler=content_handler,
        )
        return llm
    except Exception as e:
        return None


def get_raw_content_by_id(file_id):
    return dynamodb_table.get_item(
        Key={
            'file_id': file_id
        })['Item']['content']


def insert_summary(file_id, results):
    """
        Get item by file_id(key), append results as new column "summary"
    """
    return dynamodb_table.update_item(
        Key={
            'file_id': file_id
        },
        UpdateExpression='SET summary= :summary,last_updated_date= :last_updated_date',
        ExpressionAttributeValues={
            ':summary': results,
            ':last_updated_date': datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        }
    )


#### Init Model and Processor
llm = init_model()
long_text_processor = LongTextProcessor(llm)


def lambda_handler(event, context):
    print(event)

    if 'Records' not in event:
        # From API GW
        file_id = event['queryStringParameters']['file_id']
        chunk_size = 1024  # int(event['queryStringParameters']['chunk_line_quantity'])
    else:
        # From DynamoDB
        file_id = event['Records'][0]['dynamodb']['NewImage']['file_id']['S']
        chunk_size = 1024  # int(event['queryStringParameters']['chunk_line_quantity'])

    content = get_raw_content_by_id(file_id)

    print(f"content is : {content}")

    results = long_text_processor.run_processing(content, chunk_size)

    print("Process finished !")
    print(f"---->: {results}")

    # Update into DynamoDB table
    insert_summary(file_id, results)

    print(f"Summary for File[{file_id}] inserted into DynamoDB.")

    return {
        'statusCode': 200,
        'body': json.dumps("OK")
    }
