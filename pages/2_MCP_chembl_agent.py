# pages/chembl_mcp_live.py
import streamlit as st
import mcp_agent                                # run_chembl_agent(query)가 동기 함수
import logging, sys, io, queue, threading, time, contextlib

################################################################################
# 0. 기본 로거 설정 (기존 코드 그대로)
################################################################################
logger = logging.getLogger("CHEMBL_MCP")
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(filename)s:%(lineno)d | %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

################################################################################
# 1. stdout/stderr -> Queue 로 보내는 Tee 객체
################################################################################
class StreamToQueue(io.TextIOBase):
    def __init__(self, q): self.q = q
    def write(self, s):
        if s.strip():                 # 공백 줄 제거
            self.q.put(s)
    def flush(self): pass

################################################################################
# 2. 백그라운드에서 에이전트를 돌리는 함수
################################################################################
def agent_worker(query: str, q: queue.Queue, done: threading.Event):
    buf = StreamToQueue(q)
    # run_chembl_agent 내부 print/logger 모두 잡기
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            answer = mcp_agent.run_chembl_agent(query)
            q.put(f"\n✅ **Answer returned**\n{answer}\n")
        except Exception as e:
            q.put(f"\n❌ Error: {e}\n")
    done.set()

################################################################################
# 3. Streamlit UI
################################################################################
st.title("💬 CHEMBL MCP demo (live logs)")

# 세션 상태 초기화 ----------------------------------------------------------------
if "CHEMBL_MCP_messages" not in st.session_state:
    st.session_state["CHEMBL_MCP_messages"] = [
        {"role": "assistant", "content": "안녕하세요, 무엇이 궁금하세요?"}
    ]

# 지난 대화 렌더링 ----------------------------------------------------------------
for msg in st.session_state.CHEMBL_MCP_messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 사용자 입력 --------------------------------------------------------------------
query = st.chat_input("메시지를 입력하세요")
if query:
    # 3-1) 채팅창에 바로 출력
    st.session_state.CHEMBL_MCP_messages.append({"role": "user", "content": query})
    st.chat_message("user").write(query)

    # 3-2) 자리표시자 두 개: (a) 실시간 로그, (b) 최종 답
    log_placeholder = st.empty()
    ans_placeholder = st.chat_message("assistant")

    # 3-3) Queue / Done-flag 준비
    q, done_flag = queue.Queue(), threading.Event()

    # 3-4) 백그라운드 스레드 시작
    threading.Thread(target=agent_worker,
                     args=(query, q, done_flag),
                     daemon=True).start()

    # 3-5) 큐 polling → 실시간 로그 표시
    collected_lines = []
    while not (done_flag.is_set() and q.empty()):
        try:
            line = q.get_nowait()
            collected_lines.append(line)
            log_placeholder.code("".join(collected_lines))
        except queue.Empty:
            time.sleep(0.1)        # 100 ms 간격

    # 3-6) 최종 로그 한 번 더 갱신
    log_placeholder.code("".join(collected_lines))

    # 3-7) 마지막 줄(=정답) 추출 → 별도 채팅버블에 표시
    #     (answer는 ✅ 줄 이후 전부라고 가정)
    answer_text = ""
    for i, ln in enumerate(collected_lines):
        if ln.startswith("✅"):
            answer_text = "".join(collected_lines[i+1:]).lstrip()
            break
    if answer_text:
        ans_placeholder.write(answer_text)
        st.session_state.CHEMBL_MCP_messages.append(
            {"role": "assistant", "content": answer_text}
        )