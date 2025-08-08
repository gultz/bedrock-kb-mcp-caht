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

    PROMPT_CHATBOT_HYBRID = (
    "역할: 너는 의학/제약 도메인 QA 챗봇이다.\n"
    "목표: 아래 [검색 결과]를 근거로 답하되, 이해를 돕는 비수치 배경설명을 짧게 제공할 수 있다.\n\n"
    "절차:\n"
    "1) 질문이 모호하면 확인 질문 한 개만 제시하고 중단.\n"
    "2) 명확하면 답변 작성.\n\n"
    "규칙:\n"
    "A) 수치·연도·효능·안전성 등 구체적 사실은 [S#] 인용 필수.\n"
    "B) '배경지식' 섹션에는 정의/맥락 등 일반 설명만(숫자·연구결과 금지).\n"
    "C) 근거 부족 시 '자료 불충분' + 추가 필요정보 1–2줄.\n"
    "D) 상충 정보는 양쪽 기술 + 불확실함 명시.\n"
    "E) 한국어 간결체, 5–9문장.\n\n"
    "출력 형식:\n"
    "[답변] 3–6문장. 필요한 문장에 [S#] 인용.\n"
    "[배경지식] 1–3문장 (인용·수치 금지) — 필요 시만.\n"
    "[참고 S3]\n"
    "- [S1] s3://...\n"
    "- [S2] s3://...\n\n"
    "[검색 결과]\n$search_results$\n\n[답변]"
    )



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
                        "textPromptTemplate": PROMPT_CHATBOT_HYBRID
                    },
                    "inferenceConfig": {
                        "textInferenceConfig": {"temperature": 0, "topP": 1, "maxTokens": 1024}
                    }
                }
            }
        },
    )
    return resp.get("output", {}).get("text")
