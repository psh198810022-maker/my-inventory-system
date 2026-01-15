import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 로그인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="2026년도 재고조사 관리 시스템", layout="wide")

PASSWORD = "1234" 

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.password_input == PASSWORD:
        st.session_state.authenticated = True
        del st.session_state.password_input
    else:
        st.error("비밀번호가 틀렸습니다.")

if not st.session_state.authenticated:
    st.title("🔒 로그인이 필요합니다")
    st.write("관계자 외 접근을 제한합니다.")
    st.text_input("접속 비밀번호를 입력하세요", type="password", key="password_input", on_change=check_password)
    st.stop() 

# =============================================================================
# 로그인 성공 시 실행
# =============================================================================
st.title("📊 2026년도 재고조사 관리 시스템")

# -----------------------------------------------------------------------------
# 2. 데이터 로드 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def load_data():
    try:
        file_url = st.secrets["excel_url"]
        
        # 구글 드라이브 링크 변환 로직
        if "/file/d/" in file_url:
            parts = file_url.split("/file/d/")
            if len(parts) > 1:
                file_id = parts[1].split("/")[0]
                download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            else:
                return None, None, "링크 형식이 올바르지 않습니다."
        elif "/spreadsheets/d/" in file_url:
            parts = file_url.split("/spreadsheets/d/")
            if len(parts) > 1:
                file_id = parts[1].split("/")[0]
                download_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            else:
                return None, None, "링크 형식이 올바르지 않습니다."
        else:
            return None, None, "올바른 구글 드라이브 공유
