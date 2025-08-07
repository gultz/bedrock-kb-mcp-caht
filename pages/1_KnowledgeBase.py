import streamlit as st
import logging
import sys
import kb_client

logger = logging.getLogger("KB")  # 예: "MCP" 또는 "KB"
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter('%(filename)s:%(lineno)d | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

st.title("KB Page")
st.write("This is the KB page content.")


if "kb_messages" not in st.session_state:
    st.session_state["kb_messages"] = [
        {"role": "assistant", "content": "안녕하세요, 무엇이 궁금하세요?"}
    ]
# 지난 답변 출력
for msg in st.session_state.kb_messages:
    content = msg["content"]
    st.chat_message(msg["role"]).write(content)


#유저가 쓴 chat을 query라는 변수에 담음
query = st.chat_input("Search documentation")
if query:
    # Session에 메세지 저장
    st.session_state.kb_messages.append({"role": "user", "content": query})
    
    # UI에 출력
    st.chat_message("user").write(query)

    # UI 출력
    temp = kb_client.query(query)
    answer = temp[0]
    s3_uri_list = temp[1]
        

    # Session 메세지 저장 (전체 결과 저장)
    st.session_state.kb_messages.append({"role": "assistant", "content": answer})

    st.chat_message("assistant").write(answer)
    with st.expander("PDF URI"):
        for s3_uri in s3_uri_list:
            pdf_url = s3_uri
            # st.markdown(f'<iframe src="{pdf_url}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)