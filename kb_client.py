import os, sys, boto3

#profile_name = 'jw'

session = boto3.Session()
region_name = session.region_name or "us-west-2"
ssm = session.client('ssm', region_name=region_name)
bedrock_agent_runtime_client = session.client("bedrock-agent-runtime", region_name="us-west-2")

# def get_knowledge_base_id(key, enc=False):
#     if enc: WithDecryption = True
#     else: WithDecryption = False
#     response = ssm.get_parameters(
#         Names=[key,],
#         WithDecryption=WithDecryption
#     )
#     return response['Parameters'][0]['Value']

MODEL_ARN = "arn:aws:bedrock:us-west-2:170483442401:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
# KNOWLEDGE_BASE_ID = get_knowledge_base_id(key="/RAGChatBot/KNOWLEDGE_BASE_ID", enc=False)
KNOWLEDGE_BASE_ID = "UUKNDSQHHQ"


def parse_bedrock_response(response):
    # text는 항상 있으므로 값만 반환
    text = response.get("output", {}).get("text")
    
    metadata_list = []
    s3_uri_list = []

    for citation in response.get("citations", []):
        for ref in citation.get("retrievedReferences", []):
            metadata = ref.get("metadata", {})
            if metadata:
                metadata_list.append(metadata)
            
            s3_uri = ref.get("location", {}).get("s3Location", {}).get("uri")
            if s3_uri:
                s3_uri_list.append(s3_uri)
    
    # 반환 형식: text, metadata_list (있을 경우), s3_uri_list (있을 경우)
    result = [text]
    
    if metadata_list:
        result.append(metadata_list)
    if s3_uri_list:
        result.append(s3_uri_list)
    
    return result

def query(question)
    response = bedrock_agent_runtime_client.retrieve_and_generate(
        input={
            'text': question
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': MODEL_ARN,
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'overrideSearchType': 'HYBRID'
                    }
                },
                'generationConfiguration': {
                    "promptTemplate": { 
                       "textPromptTemplate": (
                            "Based only on the following search results, answer in Korean clearly and concisely.\n"
                            "\n[Search Results]\n$search_results$\n"
                            "\n[Answer]"
                        )
                    }
                }
            }
        },
    )


    parsed = parse_bedrock_response(response)
    
    return parsed
