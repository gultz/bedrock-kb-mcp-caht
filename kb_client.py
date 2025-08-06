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
    # 1) 질문 임베딩 → KNN 검색 (같음)
    q_vec = embed_v2(question)
    knn = os_client.search(
        index=INDEX,
        body={"size": 5, "query": {"knn": {VEC_FIELD: {"vector": q_vec, "k": 5}}}}
    )

    # 2) 히트들을 하나의 문자열로 합치기 (섹션 구분 추가 권장)
    chunks = []
    for i, hit in enumerate(knn["hits"]["hits"], 1):
        txt = (hit["_source"].get(TEXT_FIELD) or "").strip()
        if not txt:
            continue
        src = hit["_source"].get("x-amz-bedrock-kb-source-uri") or hit["_id"]
        chunks.append(f"[Source {i}] {src}\n{txt}")

    merged = "\n\n----\n\n".join(chunks)
    payload = {
        "sourceType": "BYTE_CONTENT",
        "byteContent": {
            "contentType": "text/plain",
            "data": base64.b64encode(merged.encode("utf-8")).decode("ascii"),
            "identifier": f"knn-top{len(chunks)}"
        }
    }


    # 3) RnG 호출 (EXTERNAL_SOURCES는 sources 한 개만!)
    resp = bedrock_agent_runtime_client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "EXTERNAL_SOURCES",
            "externalSourcesConfiguration": {
                "modelArn": MODEL_ARN,
                "sources": [payload],  # <= 반드시 길이 1
                "generationConfiguration": {
                    "promptTemplate": {
                        "textPromptTemplate": (
                            "의학/제약 논문 맥락에서, 아래 검색결과만 근거로 "
                            "명확하고 간결한 한국어 답변을 작성하라.\n\n"
                            "[검색 결과]\n$search_results$\n\n[답변]"
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