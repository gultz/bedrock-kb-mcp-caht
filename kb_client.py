import json, boto3, base64
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy import AWSV4SignerAuth

REGION = "us-west-2"
AOSS_HOST = "fo3v57rqvibkb306p82j.us-west-2.aoss.amazonaws.com"
INDEX = "bedrock-knowledge-base-default-index"
TEXT_FIELD = "AMAZON_BEDROCK_TEXT"
VEC_FIELD  = "embedding_v2"  # 우리가 백필해 둔 v2 벡터 필드

session = boto3.Session()
auth = AWSV4SignerAuth(session.get_credentials(), REGION, service="aoss")
os_client = OpenSearch(
    hosts=[{"host": AOSS_HOST, "port": 443}],
    http_auth=auth, use_ssl=True, verify_certs=True,
    connection_class=RequestsHttpConnection,
)
br = boto3.client("bedrock-runtime", region_name=REGION)
bedrock_agent_runtime_client = session.client("bedrock-agent-runtime", region_name=REGION)

MODEL_ARN = "arn:aws:bedrock:us-west-2:170483442401:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"

def embed_v2(text: str):
    r = br.invoke_model(modelId="amazon.titan-embed-text-v2:0",
                        body=json.dumps({"inputText": text}))
    return json.loads(r["body"].read())["embedding"]

def query(question):
    # 1) 질문을 v2로 임베딩
    q_vec = embed_v2(question)

    # 2) AOSS에서 v2 필드로 KNN
    knn_body = {"size": 5, "query": {"knn": {VEC_FIELD: {"vector": q_vec, "k": 5}}}}
    knn = os_client.search(index=INDEX, body=knn_body)

    # 3) 검색 결과를 외부 소스로 구성 (필수: type="EXTERNAL", $search_results$에서 소비됨)
    sources = []
    for hit in knn["hits"]["hits"]:
        doc_id = hit["_id"]
        txt = (hit["_source"].get(TEXT_FIELD) or "").strip()
        if not txt:
            continue
        sources.append({
            "sourceType": "BYTE_CONTENT",
            "byteContent": {
                "contentType": "text/plain",
                "data": base64.b64encode(txt.encode("utf-8")).decode("ascii"),  # blob = base64
                "identifier": doc_id
            }
        })

    # 4) RnG 호출 (EXTERNAL_SOURCES)
    resp = bedrock_agent_runtime_client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "EXTERNAL_SOURCES",
            "externalSourcesConfiguration": {
                "modelArn": MODEL_ARN,
                "sources": sources,
                "generationConfiguration": {
                    "promptTemplate": {
                        "textPromptTemplate": (
                            "Based only on the following search results, answer in Korean clearly and concisely.\n"
                            "\n[Search Results]\n$search_results$\n"
                            "\n[Answer]"
                        )
                    },
                    "inferenceConfig": {
                        "textInferenceConfig": {"temperature": 0, "topP": 1, "maxTokens": 1024}
                    }
                }
            }
        },
    )
    return {
        "text": resp.get("output", {}).get("text"),
    }