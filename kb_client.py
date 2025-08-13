import json, boto3, base64
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy import AWSV4SignerAuth
import re, os

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

#--------------------------------

def embed_v2(text: str):
    r = br.invoke_model(modelId="amazon.titan-embed-text-v2:0",
                        body=json.dumps({"inputText": text}))
    return json.loads(r["body"].read())["embedding"]


def s3uri_to_https(s3uri: str) -> str:
    bucket_and_key = s3uri[len("s3://"):]
    bucket, key = bucket_and_key.split("/", 1)
    return f"https://{bucket}.s3.{REGION}.amazonaws.com/{key}"


def is_chitchat(q: str) -> bool:
    # 아주 얕은 인사/잡담은 KB 우회
    return bool(re.match(r'^(안녕|하이|hello|hi|ㅎㅇ|뭐해|날씨|요즘)', q.strip(), re.I))

def general_chat(question: str) -> str:
# 일반 대화 모드: system 프롬프트로 톤만 통제
    resp = br.invoke_model(
        modelId="arn:aws:bedrock:us-west-2:170483442401:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 1,
            "messages": [        
                {
                    "role": "user",
                    "content": [{"type": "text", "text": question}]
                }
            ]
        })
    )
    return json.loads(resp["body"].read())["content"][0]["text"]

def contains_difficulty_phrase(answer: str) -> bool:
    """
    답변에 '어렵습니다'라는 단어가 포함되어 있으면 True 반환.
    대소문자 구분 없이 체크.
    """
    if not answer:
        return False
    return "어렵습니다" in answer

#----------------------------main------------------

# 간단 토크나이저 & 겹침 계산 (영문/한글 알파뉴메릭)
_token_pat = re.compile(r"[A-Za-z0-9가-힣]+")

def tokens(s: str):
    return set(t.lower() for t in _token_pat.findall(s))

def overlap_count(q: str, t: str) -> int:
    qs, ts = tokens(q), tokens(t)
    return len(qs & ts)

#--------------------------------



def query(question):
    # 1) 질문을 v2로 임베딩
    # 1) 질문 임베딩 → KNN 검색 (같음)
    q_vec = embed_v2(question)
    knn = os_client.search(
        index=INDEX,
        body={"size": 5, "query": {"knn": {VEC_FIELD: {"vector": q_vec, "k": 5}}}}
    )
    hits = knn["hits"]["hits"]



    # 4) 히트 필터링 (조건 4개 중 2개 이상 만족 시 채택)
    chunks = []
    s3_uri_list = []

    for i, hit in enumerate(hits, 1):
        txt = (hit["_source"].get(TEXT_FIELD) or "").strip()
        if not txt:
            continue
        src = hit["_source"].get("x-amz-bedrock-kb-source-uri") or hit["_id"]
        # 기존 포맷 유지
        chunks.append(f"[Source {i}] {src}\n{txt}")
        if str(src).startswith("s3://"):
            s3_uri_list.append(src)

   
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
    "0) 질문이 모호하여 답변이 어려울 경우, 혹은 이상한 질문이라면, 답변에 반드시 '어렵습니다'라는 단어를 포함.\n"
    "1) 답변이 어려울 경우 [S#] 인용 절대 하지 말 것.\n"
    "A) 수치·연도·효능·안전성 등 구체적 사실은 [S#] 인용 필수.\n"
    "B) '배경지식' 섹션에는 정의/맥락 등 일반 설명만(숫자·연구결과 금지).\n"
    "C) 근거 부족 시 '자료 불충분' + 추가 필요정보 1–2줄.\n"
    "D) 상충 정보는 양쪽 기술 + 불확실함 명시.\n"
    "E) 한국어 간결체, 8-11문장.\n\n"
    "출력 형식:\n"
    "[Answer]\n 3–8문장. 필요한 문장에 [#] 인용.\n"
    "[Background] 1–3문장 (인용·수치 금지) — 필요 시만.\n"
    "[References]\n"
    "- [1] s3://...\n"
    "- [2] s3://...\n\n"
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

    s3_uri_list = list({s3uri_to_https(uri) for uri in s3_uri_list})    

    if(contains_difficulty_phrase(resp.get("output", {}).get("text"))):
        return [resp.get("output", {}).get("text"), []]
    else:
        return [resp.get("output", {}).get("text"), s3_uri_list]


    # s3_uri_list = list({s3uri_to_https(uri) for uri in s3_uri_list})    
    # return  [resp.get("output", {}).get("text"), s3_uri_list]
    
