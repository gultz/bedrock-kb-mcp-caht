import streamlit as st
import logging
import sys

# logging.basicConfig(
#     level=logging.INFO,  # Default to INFO level
#     format='%(filename)s:%(lineno)d | %(message)s',
#     handlers=[
#         logging.StreamHandler(sys.stderr)
#     ]
# )
# logger = logging.getLogger("streamlit")

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
    <div style='font-size: 1.1em; line-height: 1.7; text-align: center;'>
    이 프로젝트는 <b>MCP(CHEMBL 등)</b>과 <b>Knowledge Base(Paper 등)</b>를 활용한 <b>AI PoC 데모</b>입니다.<br>
    <br>
    <ul style='text-align: left; display: inline-block;'>
        <li>왼쪽 <b>사이드바</b>에서 <span style='color:#4F8BF9;'><b>MCP</b></span> 또는 <span style='color:#4F8BF9;'><b>Knowledge Base</b></span> 기능을 직접 테스트해보세요!</li>
        <li>각 기능별 챗봇/검색 결과는 해당 페이지에서 확인할 수 있습니다.</li>
    </ul>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")



