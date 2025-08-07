# pages/chembl_mcp_live.py

###############################################################################
# 0. 기본 import & 로깅
###############################################################################
import streamlit as st
import mcp_agent                       # <- run_chembl_agent(query)
import logging, sys, io, queue, threading, time, contextlib

# --- logger for every run_chembl_agent 내부 print/logger 잡기 ---------------
logger = logging.getLogger("CHEMBL_MCP_STREAM")  # 예: "MCP" 또는 "KB"
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(filename)s:%(lineno)d | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

#te
###############################################################################
# 1. stdout / stderr 를 Queue 로 tee 하기 위한 래퍼
###############################################################################
class StreamToQueue(io.TextIOBase):
    """print() 또는 logging 이 write() 할 때마다 큐에 push"""
    def __init__(self, q: queue.Queue): self.q = q
    def write(self, s: str):
        if s.strip():                  # 공백줄 거르기
            self.q.put(s)
    def flush(self):                   # 필요 없지만 인터페이스용
        pass

###############################################################################
# 2. Agent 를 백그라운드에서 돌리면서 로그를 Queue 로 전달
###############################################################################
def agent_worker(query: str, log_q: queue.Queue, answer_q: queue.Queue, done_evt: threading.Event):
    buf = StreamToQueue(log_q)
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            answer = mcp_agent.run_chembl_agent(query)
            answer_q.put(answer)
        except Exception as exc:
            log_q.put(f"\n❌ Error: {exc}\n")
    done_evt.set()

###############################################################################
# 3. Streamlit UI
###############################################################################
st.set_page_config(page_title="CHEMBL-MCP demo", page_icon="🔬")
st.title("💬 CHEMBL MCP demo — live tool-usage log")

# --- 세션 상태: 대화 히스토리 ----------------------------------------------
if "CHEMBL_STREAM_MCP_messages" not in st.session_state:
    st.session_state["CHEMBL_STREAM_MCP_messages"] = [
        {"role": "assistant", "content": "안녕하세요, 무엇이 궁금하세요?"}
    ]

# --- 과거 메시지 렌더 --------------------------------------------------------
for msg in st.session_state.CHEMBL_STREAM_MCP_messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- 사용자 입력 ------------------------------------------------------------
query = st.chat_input("메시지를 입력하세요")
if query:
    # 3-1. 히스토리에 추가 & 즉시 출력
    st.session_state.CHEMBL_STREAM_MCP_messages.append({"role": "user", "content": query})

    st.chat_message("user").write(query)

    # 3-2. 질문-단위 전용 container 만들기
                    # 묶음
    log_box     = st.empty()
    # 3-3. 큐 & 이벤트 & worker-thread 준비
    log_q          = queue.Queue()
    answer_q          = queue.Queue()
    done_flag  = threading.Event()

    threading.Thread(
        target=agent_worker,
        args=(query, log_q, answer_q, done_flag),
        daemon=True,
    ).start()

    # 3-4. polling 으로 큐 읽어와서 로그 갱신
    lines: list[str] = []
    while not (done_flag.is_set() and log_q.empty()):
        try:
            line = log_q.get_nowait()
            lines.append(line)
            log_box.code("".join(lines))   # 실시간
        except queue.Empty:
            time.sleep(0.1)

    # 3-5. 최종 로그 한 번 더 그리기
    log_box.code("".join(lines), language="")
    time.sleep(1)

    answer_text = answer_q.get() if not answer_q.empty() else "⚠️ No answer!"
   
    st.chat_message("assistant").write(answer_text)

    # Session 메세지 저장
    st.session_state.CHEMBL_STREAM_MCP_messages.append({"role": "assistant", "content": answer_text})
    
    
    # # 3-7. 답변 chat-bubble + 히스토리 저장
    # if answer_text:
    #     answer_box.write(answer_text)
    #     st.session_state.chembl_chat_history.append(("assistant", answer_text))