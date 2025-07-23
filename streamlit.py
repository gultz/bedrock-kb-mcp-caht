import streamlit as st
import chat
import logging
import sys

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("streamlit")

st.set_page_config(
    page_title="JW Pharmaceutical AI PoC",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 상단 로고/이모지와 제목
st.markdown("<h1 style='text-align: center;'>💊 JW Pharmaceutical AI PoC</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4F8BF9;'>MCP & Knowledge Base 기반 생성형 AI 데모</h3>", unsafe_allow_html=True)

# 구분선
st.markdown("---")

# 설명 영역
st.markdown(
    """
    <div style='font-size: 1.1em; line-height: 1.7;'>
    이 프로젝트는 <b>MCP(CHEMBL 등)</b>과 <b>Knowledge Base(Paper 등)</b>를 활용한 <b>AI PoC 데모</b>입니다.<br>
    <br>
    <ul>
        <li>왼쪽 <b>사이드바</b>에서 <span style='color:#4F8BF9;'><b>MCP</b></span> 또는 <span style='color:#4F8BF9;'><b>Knowledge Base</b></span> 기능을 직접 테스트해보세요!</li>
        <li>각 기능별 챗봇/검색 결과는 해당 페이지에서 확인할 수 있습니다.</li>
    </ul>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")



# st.markdown('''- [Github](https://github.com/aws-samples/kr-tech-blog-sample-code/cdk_bedrock_rag_chatbot/)에서 코드를 확인하실 수 있습니다.''')


# col1, col2, col3 = st.columns([1, 1, 1])
# with col1:
#     btn1 = st.button("👉 **이 RAG의 아키텍처를 보여주세요.**")
# with col2:
#     btn2 = st.button("👉 **이 애플리케이션의 UI는 어떻게 만들어졌나요?**")

# if "messages" not in st.session_state:
#     st.session_state["messages"] = [
#         {"role": "assistant", "content": "안녕하세요, 무엇이 궁금하세요?"}
#     ]
# # 지난 답변 출력
# for msg in st.session_state.messages:
#     st.chat_message(msg["role"]).write(msg["content"])

# if btn1:
#     query = "이 RAG의 아키텍처를 보여주세요."
#     st.chat_message("user").write(query)
#     st.chat_message("assistant").image('architecture.png')

#     st.session_state.messages.append({"role": "user", "content": query}) 
#     st.session_state.messages.append({"role": "assistant", "content": "아키텍처 이미지를 다시 확인하려면 위 버튼을 다시 눌러주세요."})

# if btn2:
#     query = "이 애플리케이션의 UI는 어떻게 만들어졌나요?"
#     answer = '''이 챗봇은 [Streamlit](https://docs.streamlit.io/)을 이용해 만들어졌어요.   
#                 Streamlit은 간단한 Python 기반 코드로 대화형 웹앱을 구축 가능한 오픈소스 라이브러리입니다.    
#                 아래 app.py 코드를 통해 Streamlit을 통해 간단히 챗봇 데모를 만드는 방법에 대해 알아보세요:
#                 💁‍♀️ [app.py 코드 확인하기](https://github.com/aws-samples/kr-tech-blog-sample-code/cdk_bedrock_rag_chatbot/application/streamlit.py)
#             '''
#     st.chat_message("user").write(query)
#     st.chat_message("assistant").write(answer)
    
#     st.session_state.messages.append({"role": "user", "content": query}) 
#     st.session_state.messages.append({"role": "assistant", "content": answer})

# 유저가 쓴 chat을 query라는 변수에 담음
# query = st.chat_input("Search documentation")
# if query:
#     # Session에 메세지 저장
#     st.session_state.messages.append({"role": "user", "content": query})
    
#     # UI에 출력
#     st.chat_message("user").write(query)

#     # UI 출력
#     answer = bedrock.query(query)
#     st.chat_message("assistant").write(answer)

#     # Session 메세지 저장
#     st.session_state.messages.append({"role": "assistant", "content": answer})
        
