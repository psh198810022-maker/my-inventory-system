import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 로그인 (보안 강화)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="2026년도 재고조사 관리 시스템", layout="wide")

# [보안] 비밀번호 설정 (원하는 비밀번호로 바꾸세요)
# 주의: 아주 강력한 보안은 아니지만, 일반적인 접근을 막을 수 있습니다.
PASSWORD = "Eren4667051!" 

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
    st.text_input("접속 비밀번호를 입력하세요", type="password", key="password_input", on_change=check_password)
    st.stop() # 비밀번호가 틀리면 여기서 멈춤

# =============================================================================
# 로그인 성공 시 아래 내용 실행
# =============================================================================
st.title("📊 2026년도 재고조사 관리 시스템")

# -----------------------------------------------------------------------------
# 2. 데이터 로드 함수
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name=0, header=1)
        df.columns = [str(c).strip() for c in df.columns]

        if df.empty:
            return None, "데이터 파일이 비어있습니다."

        required_cols = ['idx', '대분류', '중분류', '모델명', '제품번호', '25년 1월', '26년 1월']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""

        def calculate_change(row):
            u_val = str(row['25년 1월']).strip() if pd.notna(row['25년 1월']) else ""
            v_val = str(row['26년 1월']).strip() if pd.notna(row['26년 1월']) else ""

            if u_val == "" or u_val == "nan": return "신규 재고"
            elif u_val == v_val: return "변화 없음"
            else: return f"{u_val} → {v_val}"

        if '작년 대비 변화' not in df.columns or df['작년 대비 변화'].isnull().all():
            df['작년 대비 변화'] = df.apply(calculate_change, axis=1)

        return df, None
    except Exception as e:
        return None, str(e)

# 파일 로드
FILE_PATH = '휴레항.xlsx'
df, error_msg = load_data(FILE_PATH)

if df is None:
    st.warning(f"기본 파일 로드 실패: {error_msg}")
    uploaded_file = st.sidebar.file_uploader("엑셀 파일 업로드", type=['xlsx'])
    if uploaded_file:
        df, error_msg = load_data(uploaded_file)
        if df is None:
            st.error(f"파일 오류: {error_msg}")
            st.stop()
    else:
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
    '24~25년 사무실 분실': '#E0BBE4',
    '업무용': '#FFF3CD',
    '이관, 판매, 기증': '#D1ECF1',
    '폐기': '#C19A6B',
    '분실': '#F8D7DA',
    '18년 이전 분실': '#E2E3E5',
    '장기 렌탈': '#604A33'
}

# -----------------------------------------------------------------------------
# 4. 사이드바 네비게이션
# -----------------------------------------------------------------------------
st.sidebar.title("🗂️ 메뉴")
page = st.sidebar.radio("이동할 페이지를 선택하세요", ["🔍 재고 조회", "📊 보고서 (Report)"])

st.sidebar.markdown("---")

# =============================================================================
# [PAGE 1] 재고 조회
# =============================================================================
if page == "🔍 재고 조회":
    st.title("🔍 재고 조회 및 관리")

    st.sidebar.header("조건 검색")
    filter_keys = ['전체 보기', '작년 대비 변화 있음', '신규재고'] + DISPLAY_ORDER
    selected_filter_label = st.sidebar.selectbox("조회 모드 선택", filter_keys)
    
    if selected_filter_label == '전체 보기': selected_col = 'All'
    elif selected_filter_label == '작년 대비 변화 있음': selected_col = 'Change'
    elif selected_filter_label == '신규재고': selected_col = '신규재고'
    else: selected_col = COL_MAPPING.get(selected_filter_label, '')

    st.sidebar.markdown("---")
    st.sidebar.header("상태별 색상")
    for label in DISPLAY_ORDER:
        color = COLOR_DICT.get(label, '#FFFFFF')
        text_color = "white" if label in ['장기 렌탈', '25~26년도 폐기', '폐기'] else "black"
        style_str = f"background-color: {color}; color: {text_color}; padding: 5px; border-radius: 5px; margin-bottom: 5px; font-size:14px;"
        st.sidebar.markdown(f'<div style="{style_str}">{label}</div>', unsafe_allow_html=True)

    filtered_df = df.copy()
    if selected_col == 'All': pass
    elif selected_col == 'Change': filtered_df = filtered_df[filtered_df['작년 대비 변화'] != '변화 없음']
    else:
        if selected_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[selected_col].astype(str).str.upper().str.contains('V')]
        else:
            filtered_df = pd.DataFrame(columns=filtered_df.columns)

    st.markdown(f"**검색 결과: {len(filtered_df)}건**")

    if not filtered_df.empty:
        conditions = []
        choices = []
        for key_label in DISPLAY_ORDER:
            col_name = COL_MAPPING[key_label]
            if col_name in filtered_df.columns:
                mask = filtered_df[col_name].astype(str).str.upper().str.contains('V').to_numpy()
                conditions.append(mask)
                choices.append(key_label)

        if conditions: filtered_df['상태'] = np.select(conditions, choices, default='')
        else: filtered_df['상태'] = ''

        def color_status_col(val):
            if val in COLOR_DICT:
                bg = COLOR_DICT[val]
                txt = "white" if val in ['장기 렌탈', '25~26년도 폐기', '폐기'] else "black"
                return f'background-color: {bg}; color: {txt}; font-weight: bold;'
            return ''
        
        def color_change_col(val):
            if val != '변화 없음': return 'background-color: #FFF2CC; color: black;'
            return ''

        final_cols = ['대분류', '중분류', '모델명', '제품번호', '25년 1월', '26년 1월', '작년 대비 변화', '상태']
        st.dataframe(
            filtered_df[final_cols].style
            .map(color_status_col, subset=['상태'])
            .map(color_change_col, subset=['작년 대비 변화']),
            use_container_width=True,
            height=800
        )
    else:
        st.info("조건에 맞는 데이터가 없습니다.")

# =============================================================================
# [PAGE 2] 보고서 (Report)
# =============================================================================
elif page == "📊 보고서 (Report)":
    st.title("📊 재고 변동 보고서 (Report)")
    st.markdown("---")

    count_25 = df['25년 1월'].notna().sum()
    count_26 = df['26년 1월'].notna().sum()

    def get_count(col_name):
        if col_name in df.columns:
            return df[col_name].astype(str).str.upper().str.contains('V').sum()
        return 0

    count_new = get_count('신규재고')
    count_business = get_count('업무용')
    count_loss_event = get_count('25년~26년 행사장 분실')
    count_loss_office = get_count('25~26년 사무실 분실')
    count_disposal_25 = get_count('25년도 폐기')
    count_transfer_25 = get_count('25년도 판매, 이관, 기증')
    count_disposal_old = get_count('폐기')
    count_transfer_old = get_count('이관, 판매, 기증')
    
    total_disposal = count_disposal_25 + count_disposal_old
    total_transfer = count_transfer_25 + count_transfer_old
    total_loss = count_loss_event + count_loss_office
    
    st.subheader("📌 주요 재고 현황")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("2026년 총 재고", f"{count_26:,}개")
    with col2: st.metric("✨ 신규 재고", f"{count_new:,}개")
    with col3: st.metric("🏢 업무용 자산", f"{count_business:,}개")
    with col4: st.metric("📉 총 분실 (25-26)", f"{total_loss:,}개")

    st.markdown("")
    col5, col6, col7, col8 = st.columns(4)
    with col5: st.metric("🗑️ 총 폐기", f"{total_disposal:,}개")
    with col6: st.metric("🤝 총 이관/판매/기증", f"{total_transfer:,}개")
    with col7: pass
    with col8: pass

    st.markdown("---")

    st.subheader("📉 자산 감소/변동 요인 분석")
    change_data = pd.DataFrame({
        '항목': ['행사장 분실', '사무실 분실', '25~26년도 폐기', '기타 폐기', '25~26년도 이관/판매', '기타 이관/판매'],
        '수량': [count_loss_event, count_loss_office, count_disposal_25, count_disposal_old, count_transfer_25, count_transfer_old],
        '색상': ['#dc3545', '#fd7e14', '#A0522D', '#C19A6B', '#87CEEB', '#17a2b8']
    })
    change_data = change_data[change_data['수량'] > 0]
    
    if not change_data.empty:
        fig = px.bar(change_data, x='항목', y='수량', color='항목', text='수량',
                     color_discrete_sequence=change_data['색상'].tolist())
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="수량")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("감소/변동 내역이 없습니다.")

    st.markdown("---")
    st.subheader("📋 상세 내역 조회")
    
    sub_tab0, sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["✨ 신규재고 내역", "⚠️ 분실 내역", "🤝 25~26년도 판매/이관/기증", "🗑️ 25~26년도 폐기", "🏢 업무용 내역"])
    view_cols = ['구분', '중분류', '모델명', '제품번호', '26년 1월']

    with sub_tab0:
        if '신규재고' in df.columns:
            new_items = df[df['신규재고'].astype(str).str.upper().str.contains('V')].copy()
            if not new_items.empty:
                new_items['구분'] = '신규재고'
                st.dataframe(new_items[view_cols], use_container_width=True)
            else: st.info("신규재고 내역이 없습니다.")

    with sub_tab1:
        cond1 = df['25년~26년 행사장 분실'].astype(str).str.upper().str.contains('V') if '25년~26년 행사장 분실' in df.columns else False
        cond2 = df['25~26년 사무실 분실'].astype(str).str.upper().str.contains('V') if '25~26년 사무실 분실' in df.columns else False
        loss_items = df[cond1 | cond2].copy()
        if not loss_items.empty:
            loss_items['구분'] = np.where(loss_items['25년~26년 행사장 분실'].astype(str).str.upper().str.contains('V'), '행사장 분실', '사무실 분실')
            st.dataframe(loss_items[view_cols], use_container_width=True)
        else: st.success("해당 기간 분실 내역이 없습니다.")

    with sub_tab2:
        col_name = '25년도 판매, 이관, 기증'
        if col_name in df.columns:
            items_trans = df[df[col_name].astype(str).str.upper().str.contains('V')].copy()
            if not items_trans.empty:
                items_trans['구분'] = '25~26 판매/이관'
                st.dataframe(items_trans[view_cols], use_container_width=True)
            else: st.info("내역이 없습니다.")

    with sub_tab3:
        col_name = '25년도 폐기'
        if col_name in df.columns:
            items_disp = df[df[col_name].astype(str).str.upper().str.contains('V')].copy()
            if not items_disp.empty:
                items_disp['구분'] = '25~26 폐기'
                st.dataframe(items_disp[view_cols], use_container_width=True)
            else: st.info("내역이 없습니다.")
            
    with sub_tab4:
        if '업무용' in df.columns:
            biz_items = df[df['업무용'].astype(str).str.upper().str.contains('V')].copy()
            if not biz_items.empty:
                biz_items['구분'] = '업무용'
                st.dataframe(biz_items[view_cols], use_container_width=True)
            else: st.info("업무용으로 분류된 자산이 없습니다.")