import os
import json
import traceback
import urllib.parse
import boto3
from datetime import datetime
import time
from smart_search_qa import SmartSearchQA
from prompt import *

EMBEDDING_ENDPOINT_NAME = os.environ.get('embedding_endpoint_name')
LLM_ENDPOINT_NAME = os.environ.get('llm_endpoint_name')
INDEX =  os.environ.get('index')
HOST =  os.environ.get('host')
LANGUAGE =  os.environ.get('language')
region = os.environ.get('AWS_REGION')
table_name = os.environ.get('dynamodb_table_name')
search_engine_opensearch = True if str(os.environ.get('search_engine_opensearch')).lower() == 'true' else False
search_engine_kendra = True if str(os.environ.get('search_engine_kendra')).lower() == 'true' else False


port = 443

TOP_K = 2

domain_name = 'tg4k9c6ol5'
stage = 'prod'


def lambda_handler(event, context):
    
    print("event:",event)
    print("region:",region)
    print('table name:',table_name)
    
    evt_para = {}
    if 'queryStringParameters' in event.keys():
        evt_para = event['queryStringParameters']
    
    requestType = ''
    if isinstance(evt_para,dict) and "requestType" in evt_para.keys():
        requestType = evt_para['requestType']
        
    evt_body = {}
    if 'body' in event.keys() and requestType == 'websocket':
        if event['body'] != 'None' or event['body'] is not None:
            evt_body = json.loads(event['body'])
    else:
        evt_body = evt_para   

    index = INDEX
    if "index" in evt_body.keys():
        index = evt_body['index']
    elif "ind" in evt_body.keys():
        index = evt_body['ind']
    elif "indexName" in evt_body.keys():
        index = evt_body['indexName']
    print('index:',index)
    
    isCheckedContext= False
    if "isCheckedContext" in evt_body.keys():
        isCheckedContext = bool(evt_body['isCheckedContext'])

    isCheckedGenerateReport= False
    if "isCheckedGenerateReport" in evt_body.keys():
        isCheckedGenerateReport = bool(evt_body['isCheckedGenerateReport'])

    isCheckedKnowledgeBase= True
    if "isCheckedKnowledgeBase" in evt_body.keys():
        isCheckedKnowledgeBase = bool(evt_body['isCheckedKnowledgeBase'])

    isCheckedMapReduce= False
    if "isCheckedMapReduce" in evt_body.keys():
        isCheckedMapReduce = bool(evt_body['isCheckedMapReduce'])
    
    language=LANGUAGE
    if "language" in evt_body.keys():
        language = evt_body['language']

    sessionId=""
    if "session_id" in evt_body.keys():
        sessionId = str(evt_body['session_id'])
    print('session_id:',sessionId)
    
    sessionTemplateId=""
    if "sessionTemplateId" in evt_body.keys():
        sessionTemplateId = str(evt_body['sessionTemplateId'])
    print('sessionTemplateId:',sessionTemplateId)

    taskDefinition=""
    if "taskDefinition" in evt_body.keys():
        taskDefinition = str(evt_body['taskDefinition'])
    print('taskDefinition:',taskDefinition)

    temperature=0.01
    if "temperature" in evt_body.keys():
        temperature = float(evt_body['temperature'])

    embeddingEndpoint = EMBEDDING_ENDPOINT_NAME
    sagemakerEndpoint = LLM_ENDPOINT_NAME
    if "embedding_endpoint_name" in evt_body.keys():
        embeddingEndpoint = evt_body['embedding_endpoint_name']
    print("embeddingEndpoint:", embeddingEndpoint)
        
    if "llm_endpoint_name" in evt_body.keys():
        sagemakerEndpoint = evt_body['llm_endpoint_name']
    print("sagemakerEndpoint:", sagemakerEndpoint)
    
    modelType = 'normal'
    if "modelType" in evt_body.keys():
        modelType = evt_body['modelType']
  
    urlOrApiKey = ''
    if "urlOrApiKey" in evt_body.keys():
        urlOrApiKey = evt_body['urlOrApiKey']
  
    modelName = 'anthropic.claude-v2'
    if "modelName" in evt_body.keys():
        modelName = evt_body['modelName']

    bedrockMaxTokens = 512
    if "bedrockMaxTokens" in evt_body.keys():
        bedrockMaxTokens = int(evt_body['bedrockMaxTokens'])
    
    name=''
    if "name" in evt_body.keys():
        name = evt_body['name']
        
    if "llmData" in evt_body.keys():
        llmData = Dict(evt_body['llmData'])
        if "embeddingEndpoint" in llmData.keys():
            embeddingEndpoint = llmData['embeddingEndpoint']
        if "sagemakerEndpoint" in llmData.keys():
            sagemakerEndpoint = llmData['sagemakerEndpoint']
        if "modelName" in llmData.keys():
            modelName = llmData['modelName']
        if "modelType" in llmData.keys():
            modelType = llmData['modelType']
        recordId = ''
        if "recordId" in llmData.keys():
            recordId = llmData['recordId']
        if "urlOrApiKey" in llmData.keys():
            urlOrApiKey = llmData['urlOrApiKey']

    searchEngine = "opensearch"
    if not search_engine_opensearch and search_engine_kendra:
        searchEngine = "kendra"
    if "searchEngine" in evt_body.keys():
        searchEngine = evt_body['searchEngine']

    print('searchEngine:',searchEngine)

    username = None
    password = None
    host = HOST
    if searchEngine == "opensearch":
        # retrieve secret manager value by key using boto3                                             
        sm_client = boto3.client('secretsmanager')
        master_user = sm_client.get_secret_value(SecretId='opensearch-master-user')['SecretString']
        data= json.loads(master_user)
        username = data.get('username')
        password = data.get('password')
    elif searchEngine == "kendra":
        if "kendra_index_id" in evt_body.keys():
            host = evt_body['kendra_index_id']
    print("host:",host)
  
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    try:
        search_qa = SmartSearchQA()
        search_qa.init_cfg(index,
                         username,
                         password,
                         host,
                         port,
                         embeddingEndpoint,
                         region,
                         sagemakerEndpoint,
                         temperature,
                         language,
                         searchEngine,
                         modelType,
                         urlOrApiKey,
                         modelName,
                         bedrockMaxTokens
                         )
            
        query = "hello"
        if "query" in evt_body.keys():
            query = evt_body['query'].strip()
        elif "q" in evt_body.keys():
            query = evt_body['q'].strip()
        print('query:', query)
        
        contentCheckLabel = "terror"
        contentCheckSuggestion = "block"

        task = "qa"    
        if "task" in evt_body.keys():
            task = evt_body['task']
        print('task:',task)

        if task == "chat":
            
            if language == "chinese":
                prompt_template = CHINESE_CHAT_PROMPT_TEMPLATE
            elif language == "english":
                prompt_template = ENGLISH_CHAT_PROMPT_TEMPLATE
                if model_type == 'llama2':    
                    prompt_template = EN_CHAT_PROMPT_LLAMA2
            if "prompt" in evt_body.keys():
                prompt_template = evt_body['prompt']  

            if modelType == 'llama2':
                result = search_qa.get_answer_from_chat_llama2(query,prompt_template,table_name,sessionId)
            else:
                result = search_qa.get_chat(query,language,prompt_template,table_name,sessionId,modelType)
            
            print('chat result:',result)
            
            response['body'] = json.dumps(
            {
                'datetime':time.time()*1000,
                'text':result
            })

        elif task == "qa":

            if language == "chinese":
                prompt_template = CHINESE_PROMPT_TEMPLATE
                condense_question_prompt = CN_CONDENSE_QUESTION_PROMPT
                responseIfNoDocsFound = '找不到答案'
            elif language == "chinese-tc":
                prompt_template = CHINESE_TC_PROMPT_TEMPLATE
                condense_question_prompt = TC_CONDENSE_QUESTION_PROMPT
                responseIfNoDocsFound = '找不到答案'
            elif language == "english":
                prompt_template = ENGLISH_PROMPT_TEMPLATE
                condense_question_prompt = EN_CONDENSE_QUESTION_PROMPT
                if modelType == 'llama2':    
                    prompt_template = EN_CHAT_PROMPT_LLAMA2
                    condense_question_prompt = EN_CONDENSE_PROMPT_LLAMA2
                responseIfNoDocsFound = "Can't find answer"
            if "prompt" in evt_body.keys():
                prompt_template = evt_body['prompt']
                
            topK = TOP_K
            if "topK" in evt_body.keys():
                topK = int(evt_body['topK'])
            print('topK:',topK)
            
            searchMethod = 'vector' #vector/text/mix
            if "searchMethod" in evt_body.keys():
                searchMethod = evt_body['searchMethod']
            print('searchMethod:',searchMethod)
    
            txtDocsNum = 0
            if "txtDocsNum" in evt_body.keys():
                txtDocsNum = int(evt_body['txtDocsNum'])
            print('txtDocsNum:',txtDocsNum)   
            
            if "responseIfNoDocsFound" in evt_body.keys():
                responseIfNoDocsFound = evt_body['responseIfNoDocsFound']
            print('responseIfNoDocsFound:',responseIfNoDocsFound)
            
            vecDocsScoreThresholds = 0
            if "vecDocsScoreThresholds" in evt_body.keys():
                vecDocsScoreThresholds = float(evt_body['vecDocsScoreThresholds'])
            print('vecDocsScoreThresholds:',vecDocsScoreThresholds) 
            
            txtDocsScoreThresholds = 0
            if "txtDocsScoreThresholds" in evt_body.keys():
                txtDocsScoreThresholds = float(evt_body['txtDocsScoreThresholds'])
            print('txtDocsScoreThresholds:',txtDocsScoreThresholds) 
            
            if modelType == 'llama2':                            
                result = search_qa.get_answer_from_conversational_llama2(query,
                                            sessionId,
                                            table_name,
                                            prompt_template=prompt_template,
                                            condense_question_prompt=condense_question_prompt,
                                            top_k=topK
                                            )
            else:
                result = search_qa.get_answer_from_conversational(query,
                            sessionId,
                            table_name,
                            prompt_template=prompt_template,
                            condense_question_prompt=condense_question_prompt,
                            search_method=searchMethod,
                            top_k=topK,
                            txt_docs_num=txtDocsNum,
                            response_if_no_docs_found=responseIfNoDocsFound,
                            vec_docs_score_thresholds=vecDocsScoreThresholds,
                            txt_docs_score_thresholds=txtDocsScoreThresholds
                            )
                    
            print('result:',result)
            
            answer = result['answer']
            print('answer:',answer)
            
            source_documents = result['source_documents']
            if searchEngine == "opensearch":
                source_docs = [doc[0] for doc in source_documents]
                query_docs_scores = [doc[1] for doc in source_documents]
                sentences = [doc[2] for doc in source_documents]
            elif searchEngine == "kendra":
                source_docs = source_documents
                
            #cal query_answer_score
            isCheckedScoreQA = False
            query_answer_score = -1
            if "isCheckedScoreQA" in evt_body.keys():
                isCheckedScoreQA = bool(evt_body['isCheckedScoreQA'])
            if isCheckedScoreQA and searchEngine == "opensearch":
                if language.find("chinese")>=0 and len(answer) > 350:
                    answer = answer[:350]
                query_answer_score = search_qa.get_qa_relation_score(query,answer)
            print('1.query_answer_score:',query_answer_score)
                
            #cal answer_docs_scores
            isCheckedScoreAD = False
            answer_docs_scores = []
            if "isCheckedScoreAD" in evt_body.keys():
                isCheckedScoreAD = bool(evt_body['isCheckedScoreAD'])
            if isCheckedScoreAD:
                cal_answer = answer
                if language.find("chinese")>=0 and len(answer) > 150:
                    cal_answer = answer[:150]
                for source_doc in source_docs:
                    cal_source_page_content = source_doc.page_content
                    if language.find("chinese")>=0 and len(cal_source_page_content) > 150:
                        cal_source_page_content = cal_source_page_content[:150]
                    answer_docs_score = search_qa.get_qa_relation_score(cal_answer,cal_source_page_content)
                    answer_docs_scores.append(answer_docs_score)
            print('2.answer_docs_scores:',answer_docs_scores)
            
            response_type = ""
            if "response_type" in evt_body.keys():
                response_type = evt_body['response_type']         

            if response_type.find('web_ui') >= 0:
                source_list = []
                for i in range(len(source_docs)):
                    source = {}
                    source["_id"] = i
                    if language.find("chinese")>=0: 
                        source["_score"] = float(query_docs_scores[i]) if searchEngine == "opensearch" else 1
                    else:
                        source["_score"] = query_docs_scores[i] if searchEngine == "opensearch" else 1
                    
                    try:
                        source["title"] = os.path.split(source_docs[i].metadata['source'])[-1]
                    except KeyError:
                        print("KeyError,Source not found")
                        source["title"] = ''
                    source["sentence"] = sentences[i] if searchEngine == "opensearch" else source_docs[i].page_content.replace("\n","")
                    source["paragraph"] =source_docs[i].page_content.replace("\n","")
                    source["sentence_id"] = i
                    if 'row' in source_docs[i].metadata.keys():
                        source["paragraph_id"] = source_docs[i].metadata['row']
                    elif 'page' in source_docs[i].metadata.keys():
                        source["paragraph_id"] = source_docs[i].metadata['page']
                    else:
                        source["paragraph_id"] = i
                    source_list.append(source)
                                     
                response['body'] = json.dumps(
                {
                    'datetime':time.time()*1000,
                    'body': source_list,
                    'text': answer,
                    'contentCheckLabel':contentCheckLabel,
                    'contentCheckSuggestion':contentCheckSuggestion
                })

            else:    
                source_list = []
                for i in range(len(source_docs)):
                    source = {}
                    source["id"] = i
                    try:
                        source["title"] = os.path.split(source_docs[i].metadata['source'])[-1]
                    except KeyError:
                        print("KeyError found")                    
                    source["paragraph"] =source_docs[i].page_content.replace("\n","")
                    source["sentence"] = sentences[i] if searchEngine == "opensearch" else source_docs[i].page_content.replace("\n","")
                    if language.find("chinese")>=0: 
                        source["score"] = float(query_docs_scores[i]) if searchEngine == "opensearch" else 1
                    else:
                        source["score"] = query_docs_scores[i] if searchEngine == "opensearch" else 1

                    source_list.append(source)
            
                query_docs_score = query_docs_scores[0] if searchEngine == "opensearch" and len(query_docs_scores) > 0 else -1
                answer_docs_score = max(answer_docs_scores) if len(answer_docs_scores) > 0 else -1
                response['body'] = json.dumps(
                {
                    'datetime':time.time()*1000,
                    'source_list': source_list,
                    'text': answer,
                    'scoreQueryDoc': str(query_docs_score),
                    'scoreQueryAnswer': str(query_answer_score),
                    'scoreAnswerDoc': str(answer_docs_score),
                    'contentCheckLabel':contentCheckLabel,
                    'contentCheckSuggestion':contentCheckSuggestion

                })

        elif task == "summarize":
            
            prompt_template = SUMMARIZE_PROMPT_TEMPLATE
            if "prompt" in evt_body.keys():
                prompt_template = evt_body['prompt']

            chain_type = "stuff"  
            combine_prompt_template = COMBINE_SUMMARIZE_PROMPT_TEMPLATE
            
            
            if "chain_type" in evt_body.keys():
                chain_type = evt_body['chain_type']
                if chain_type =="map_reduce":
                    if "combine_prompt" in evt_body.keys():
                        combine_prompt_template = evt_body['combine_prompt']
            
            result = search_qa.get_summarize(query,chain_type,prompt_template,combine_prompt_template)
            
            response['body'] = json.dumps(
            {
                'datetime':time.time()*1000,
                'summarize': result,
                'contentCheckLabel':contentCheckLabel,
                'contentCheckSuggestion':contentCheckSuggestion,
            })
            
        if requestType == 'websocket':
            connectionId = str(event.get('requestContext',{}).get('connectionId'))
            endpoint_url=F"https://{domain_name}.execute-api.{region}.amazonaws.com/{stage}"
            apigw_management = boto3.client('apigatewaymanagementapi',
                                            endpoint_url=endpoint_url)
            api_res = apigw_management.post_to_connection(ConnectionId=connectionId,
                                                                    Data=response['body'])
            print('api_res',api_res)
        else:
            return response

    except Exception as e:
        traceback.print_exc()
        return {
            'statusCode': 400,
            'body': str(e)
        }
