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
    # content가 리스트인 경우 길이에 따라 처리
    if isinstance(content, list):
        if len(content) == 1:
            # 텍스트만 있는 경우
            display_content = content[0]
        else:
            # 메타데이터나 S3 URI가 있는 경우 - 전체 정보 표시
            display_content = f"**답변:** {content[0]}\n\n"
            
            if len(content) >= 2 and content[1]:  # metadata가 있는 경우
                display_content += "**참고 문서 정보:**\n"
                for i, metadata in enumerate(content[1], 1):
                    display_content += f"{i}. {metadata}\n"
                display_content += "\n"
            
            if len(content) >= 3 and content[2]:  # S3 URI가 있는 경우
                display_content += "**문서 경로:**\n"
                for i, s3_uri in enumerate(content[2], 1):
                    display_content += f"{i}. {s3_uri}\n"
        content = display_content
    st.chat_message(msg["role"]).write(content)


#유저가 쓴 chat을 query라는 변수에 담음
query = st.chat_input("Search documentation")
if query:
    # Session에 메세지 저장
    st.session_state.kb_messages.append({"role": "user", "content": query})
    
    # UI에 출력
    st.chat_message("user").write(query)

    # UI 출력
    answer = kb_client.query(query)
    
    # answer 리스트 길이에 따라 처리
    if len(answer) == 1:
        # 텍스트만 있는 경우
        display_content = answer[0]
    else:
        # 메타데이터나 S3 URI가 있는 경우 - 전체 정보 표시
        display_content = f"**답변:** {answer[0]}\n\n"
        
        if len(answer) >= 2 and answer[1]:  # metadata가 있는 경우
            display_content += "**참고 문서 정보:**\n"
            for i, metadata in enumerate(answer[1], 1):
                display_content += f"{i}. {metadata}\n"
            display_content += "\n"
        
        if len(answer) >= 3 and answer[2]:  # S3 URI가 있는 경우
            display_content += "**문서 경로:**\n"
            for i, s3_uri in enumerate(answer[2], 1):
                display_content += f"{i}. {s3_uri}\n"
    
    st.chat_message("assistant").write(display_content)

    # Session 메세지 저장 (전체 결과 저장)
    st.session_state.kb_messages.append({"role": "assistant", "content": answer})