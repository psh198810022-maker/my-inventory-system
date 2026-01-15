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
        
        if "/file/d/" in file_url:
            file_id = file_url.split("/file/d/")[1].split("/")[0]
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        elif "/spreadsheets/d/" in file_url:
            file_id = file_url.split("/spreadsheets/d/")[1].split("/")[0]
            download_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        else:
            return None, None, "올바른 구글 드라이브 공유 링크가 아닙니다."

        xls = pd.ExcelFile(download_url)
        
        # [1] 메인 재고 시트
        df_main = pd.read_excel(xls, sheet_name=0, header=1)
        
        # [2] 폐기예정목록 시트
        if "폐기예정목록" in xls.sheet_names:
            df_disposal_list = pd.read_excel(xls, sheet_name="폐기예정목록") 
        else:
            df_disposal_list = pd.DataFrame()

        # --- 전처리 ---
        df_main.columns = [str(c).strip() for c in df_main.columns]

        if df_main.empty:
            return None, None, "메인 데이터 파일이 비어있습니다."

        required_cols = ['idx', '대분류', '중분류', '소분류', '모델명', '제품번호', '25년 1월', '26년 1월']
        for col in required_cols:
            if col not in df_main.columns:
                df_main[col] = ""

        def calculate_change(row):
            u_val = str(row['25년 1월']).strip() if pd.notna(row['25년 1월']) else ""
            v_val = str(row['26년 1월']).strip() if pd.notna(row['26년 1월']) else ""

            if u_val == "" or u_val == "nan": return "신규 재고"
            elif u_val == v_val: return "변화 없음"
            else: return f"{u_val} → {v_val}"

        if '작년 대비 변화' not in df_main.columns or df_main['작년 대비 변화'].isnull().all():
            df_main['작년 대비 변화'] = df_main.apply(calculate_change, axis=1)

        return df_main, df_disposal_list, None

    except Exception as e:
        return None, None, f"데이터 로드 중 오류 발생: {str(e)}"

df, df_disposal_target, error_msg = load_data()

if error_msg:
    st.error(f"⚠️ 오류 발생: {error_msg}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 설정 및 매핑
# -----------------------------------------------------------------------------
DISPLAY_ORDER = [
    '정상재고',
    '25년~26년 행사장 분실',
    '25~26년도 판매, 이관, 기증', 
    '25~26년도 폐기',             
    '25~26년 사무실 분실',
    '24~25년 사무실 분실',
    '업무용',
    '이관, 판매, 기증',
    '폐기',
    '분실',
    '18년 이전 분실',
    '장기 렌탈'
]

COL_MAPPING = {
    '정상재고': '정상재고',
    '25년~26년 행사장 분실': '25년~26년 행사장 분실',
    '25~26년도 판매, 이관, 기증': '25년도 판매, 이관, 기증',
    '25~26년도 폐기': '25년도 폐기',
    '25~26년 사무실 분실': '25~26년 사무실 분실',
    '24~25년 사무실 분실': '24~25년 사무실 분실',
    '업무용': '업무용',
    '이관, 판매, 기증': '이관, 판매, 기증',
    '폐기': '폐기',
    '분실': '분실',
    '18년 이전 분실': '18년 이전 분실',
    '장기 렌탈': '장기 렌탈'
}

COLOR_DICT = {
    '정상재고': '#D4EDDA',
    '25년~26년 행사장 분실': '#FFDDC1',
    '25~26년도 판매, 이관, 기증': '#87CEEB',
    '25~26년도 폐기': '#A0522D',
    '25~26년 사무실 분실': '#FFABAB',
    '24~25년 사무실 분실':
