# # pages/chembl_mcp_live.py
# """
# Streamlit page that
#   • runs mcp_agent.run_chembl_agent(query)  (동기)
#   • 캡쳐되는 stdout/stderr 를 한-줄-한-줄 화면에 실시간으로 표시
#   • 최종 답변은 예쁜 chat-bubble 로 출력
#   • 질문-답변-로그 묶음을 계속 화면에 남겨 둠
# """

# ###############################################################################
# # 0. 기본 import & 로깅
# ###############################################################################
# import streamlit as st
# import mcp_agent                       # <- run_chembl_agent(query)
# import logging, sys, io, queue, threading, time, contextlib

# # --- logger for every run_chembl_agent 내부 print/logger 잡기 ---------------
# LOGGER_NAME = "CHEMBL_MCP"
# logger = logging.getLogger(LOGGER_NAME)
# if not logger.hasHandlers():           # 중복 Handler 방지
#     handler = logging.StreamHandler(sys.stderr)
#     handler.setFormatter(logging.Formatter('%(filename)s:%(lineno)d | %(message)s'))
#     logger.addHandler(handler)
# logger.setLevel(logging.INFO)

# ###############################################################################
# # 1. stdout / stderr 를 Queue 로 tee 하기 위한 래퍼
# ###############################################################################
# class StreamToQueue(io.TextIOBase):
#     """print() 또는 logging 이 write() 할 때마다 큐에 push"""
#     def __init__(self, q: queue.Queue): self.q = q
#     def write(self, s: str):
#         if s.strip():                  # 공백줄 거르기
#             self.q.put(s)
#     def flush(self):                   # 필요 없지만 인터페이스용
#         pass

# ###############################################################################
# # 2. Agent 를 백그라운드에서 돌리면서 로그를 Queue 로 전달
# ###############################################################################
# def agent_worker(query: str, q: queue.Queue, done_evt: threading.Event):
#     buf = StreamToQueue(q)
#     with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
#         try:
#             answer = mcp_agent.run_chembl_agent(query)
#             q.put(f"\n✅ **Answer returned**\n{answer}\n")
#         except Exception as exc:
#             q.put(f"\n❌ Error: {exc}\n")
#     done_evt.set()

# ###############################################################################
# # 3. Streamlit UI
# ###############################################################################
# st.set_page_config(page_title="CHEMBL-MCP demo", page_icon="🔬")
# st.title("💬 CHEMBL MCP demo — live tool-usage log")

# # --- 세션 상태: 대화 히스토리 ----------------------------------------------
# if "chembl_chat_history" not in st.session_state:
#     # 리스트의 각 원소는 (role, text)
#     st.session_state.chembl_chat_history = [
#         ("assistant", "안녕하세요, 무엇이 궁금하세요?"),
#     ]

# # --- 과거 메시지 렌더 --------------------------------------------------------
# for role, text in st.session_state.chembl_chat_history:
#     st.chat_message(role).write(text)

# # --- 사용자 입력 ------------------------------------------------------------
# query = st.chat_input("메시지를 입력하세요")
# if query:
#     # 3-1. 히스토리에 추가 & 즉시 출력
#     st.session_state.chembl_chat_history.append(("user", query))
#     st.chat_message("user").write(query)

#     # 3-2. 질문-단위 전용 container 만들기
#     container   = st.container()                   # 묶음
#     log_box     = container.empty()                # 실시간 로그
#     answer_box  = container.chat_message("assistant")

#     # 3-3. 큐 & 이벤트 & worker-thread 준비
#     q          = queue.Queue()
#     done_flag  = threading.Event()
#     threading.Thread(
#         target=agent_worker,
#         args=(query, q, done_flag),
#         daemon=True,
#     ).start()

#     # 3-4. polling 으로 큐 읽어와서 로그 갱신
#     lines: list[str] = []
#     while not (done_flag.is_set() and q.empty()):
#         try:
#             line = q.get_nowait()
#             lines.append(line)
#             log_box.code("".join(lines), language="")   # 실시간
#         except queue.Empty:
#             time.sleep(0.1)

#     # 3-5. 최종 로그 한 번 더 그리기
#     log_box.code("".join(lines), language="")

#     # 3-6. '✅' 이후가 정답
#     answer_text = ""
#     for idx, ln in enumerate(lines):
#         if ln.startswith("✅"):
#             answer_text = "".join(lines[idx + 1:]).lstrip()
#             break

#     # 3-7. 답변 chat-bubble + 히스토리 저장
#     if answer_text:
#         answer_box.write(answer_text)
#         st.session_state.chembl_chat_history.append(("assistant", answer_text))