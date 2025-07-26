import streamlit as st
import mcp_agent
import logging
import sys

logger = logging.getLogger("Reactome_MCP")  # 예: "MCP" 또는 "KB"
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(filename)s:%(lineno)d | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

st.title("Reactome_MCP Page")
st.write("This is the  Reactome_MCP page content.")

if "Reactome_mcp_messages" not in st.session_state:
    st.session_state["Reactome_mcp_messages"] = [
        {"role": "assistant", "content": "안녕하세요, 무엇이 궁금하세요?"}
    ]
# 지난 답변 출력
for msg in st.session_state.Reactome_mcp_messages:
    st.chat_message(msg["role"]).write(msg["content"])


#유저가 쓴 chat을 query라는 변수에 담음
query = st.chat_input("chat with MCP")
if query:
    # Session에 메세지 저장
    st.session_state.Reactome_mcp_messages.append({"role": "user", "content": query})
    
    # UI에 출
    st.chat_message("user").write(query)

    # UI 출
    answer = mcp_agent.run_Reactome_agent(query)
    st.chat_message("assistant").write(answer)

    # Session 메세지 저장
    st.session_state.Reactome_mcp_messages.append({"role": "assistant", "content": answer})
