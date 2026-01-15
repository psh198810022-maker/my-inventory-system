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
    st.text_input("비밀번호 입력", type="password", key="password_input", on_change=check_password)
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
        download_url = ""
        
        # [안전] URL 변환 로직
        if "/file/d/" in file_url:
            part = file_url.split("/file/d/")[1]
            file_id = part.split("/")[0]
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        elif "/spreadsheets/d/" in file_url:
            part = file_url.split("/spreadsheets/d/")[1]
            file_id = part.split("/")[0]
            download_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        else:
            return None, None, "링크 오류: 구글 드라이브 링크가 아닙니다."

        xls = pd.ExcelFile(download_url)
        
        # [1] 메인 시트 로드
        df_main = pd.read_excel(xls, sheet_name=0, header=1)
        
        # [2] 폐기예정목록 시트 로드
        target_name = "폐기예정목록"
        if target_name in xls.sheet_names:
            df_disposal_list = pd.read_excel(xls, sheet_name=target_name)
        else:
            df_disposal_list = pd.DataFrame()

        # 전처리
        df_main.columns = [str(c).strip() for c in df_main.columns]

        if df_main.empty:
            return None, None, "메인 데이터가 비어있습니다."

        cols = ['idx', '대분류', '중분류', '소분류', '모델명', '제품번호', '25년 1월', '26년 1월']
        for c in cols:
            if c not in df_main.columns:
                df_main[c] = ""

        # [안전] 변화 계산 함수
        def calc_change(row):
            v25 = str(row['25년 1월']).strip() if pd.notna(row['25년 1월']) else ""
            v26 = str(row['26년 1월']).strip() if pd.notna(row['26년 1월']) else ""

            if v25 == "" or v25 == "nan":
                return "신규 재고"
            if v25 == v26:
                return "변화 없음"
            return f"{v25} -> {v26}"

        if '작년 대비 변화' not in df_main.columns or df_main['작년 대비 변화'].isnull().all():
            df_main['작년 대비 변화'] = df_main.apply(calc_change, axis=1)

        return df_main, df_disposal_list, None

    except Exception as e:
        return None, None, f"에러 발생: {str(e)}"

df, df_disposal_target, error_msg = load_data()

if error_msg:
    st.error(f"오류: {error_msg}")
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

# 딕셔너리 키 매핑
COL_MAPPING = {}
COL_MAPPING['정상재고'] = '정상재고'
COL_MAPPING['25년~26년 행사장 분실'] = '25년~26년 행사장 분실'
COL_MAPPING['25~26년도 판매, 이관, 기증'] = '25년도 판매, 이관, 기증'
COL_MAPPING['25~26년도 폐기'] = '25년도 폐기'
COL_MAPPING['25~26년 사무실 분실'] = '25~26년 사무실 분실'
COL_MAPPING['24~25년 사무실 분실'] = '24~25년 사무실 분실'
COL_MAPPING['업무용'] = '업무용'
COL_MAPPING['이관, 판매, 기증'] = '이관, 판매, 기증'
COL_MAPPING['폐기'] = '폐기'
COL_MAPPING['분실'] = '분실'
COL_MAPPING['18년 이전 분실'] = '18년 이전 분실'
COL_MAPPING['장기 렌탈'] = '장기 렌탈'

# 색상 매핑
COLOR_DICT = {}
COLOR_DICT['정상재고'] = '#D4EDDA'
COLOR_DICT['25년~26년 행사장 분실'] = '#FFDDC1'
COLOR_DICT['25~26년도 판매, 이관, 기증'] = '#87CEEB'
COLOR_DICT['25~26년도 폐기'] = '#A0522D'
COLOR_DICT['25~26년 사무실 분실'] = '#FFABAB'
COLOR_DICT['24~25년 사무실 분실'] = '#E0BBE4'
COLOR_DICT['업무용'] = '#FFF3CD'
COLOR_DICT['이관, 판매, 기증'] = '#D1ECF1'
COLOR_DICT['폐기'] = '#C19A6B'
COLOR_DICT['분실'] = '#F8D7DA'
COLOR_DICT['18년 이전 분실'] = '#E2E3E5'
COLOR_DICT['장기 렌탈'] = '#604A33'

# -----------------------------------------------------------------------------
# 4. 화면 구성
# -----------------------------------------------------------------------------
st.sidebar.title("🗂️ 메뉴")
page = st.sidebar.radio("페이지 선택", ["🔍 재고 조회", "📊 보고서 (Report)", "🗑️ 폐기예정목록"])

st.sidebar.markdown("---")
if st.sidebar.button("🔄 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

# [PAGE 1] 재고 조회
if page == "🔍 재고 조회":
    st.subheader("조건 검색")
    st.sidebar.header("필터 설정")
    
    f_keys = ['전체 보기', '작년 대비 변화 있음', '신규재고'] + DISPLAY_ORDER
    sel_label = st.sidebar.selectbox("조회 모드", f_keys)
    
    sel_col = ''
    if sel_label == '전체 보기': sel_col = 'All'
    elif sel_label == '작년 대비 변화 있음': sel_col = 'Change'
    elif sel_label == '신규재고': sel_col = '신규재고'
    else: sel_col = COL_MAPPING.get(sel_label, '')

    st.sidebar.markdown("---")
    st.sidebar.markdown("**범례**")
    for label in DISPLAY_ORDER:
        c = COLOR_DICT.get(label, '#FFFFFF')
        tc = "white" if label in ['장기 렌탈', '25~26년도 폐기', '폐기'] else "black"
        st.sidebar.markdown(f'<div style="background-color:{c};color:{tc};padding:3px;margin-bottom:3px;">{label}</div>', unsafe_allow_html=True)

    f_df = df.copy()
    if sel_col == 'All': pass
    elif sel_col == 'Change': f_df = f_df[f_df['작년 대비 변화'] != '변화 없음']
    else:
        if sel_col in f_df.columns:
            f_df = f_df[f_df[sel_col].astype(str).str.upper().str.contains('V')]
        else:
            f_df = pd.DataFrame(columns=f_df.columns)

    st.markdown(f"**결과: {len(f_df)}건**")

    if not f_df.empty:
        conds, choices = [], []
        for lbl in DISPLAY_ORDER:
            cname = COL_MAPPING[lbl]
            if cname in f_df.columns:
                mask = f_df[cname].astype(str).str.upper().str.contains('V').to_numpy()
                conds.append(mask)
                choices.append(lbl)

        if conds: f_df['상태'] = np.select(conds, choices, default='')
        else: f_df['상태'] = ''

        def style_status(v):
            if v in COLOR_DICT:
                c = COLOR_DICT[v]
                tc = "white" if v in ['장기 렌탈', '25~26년도 폐기', '폐기'] else "black"
                return f'background-color: {c}; color: {tc}; font-weight: bold;'
            return ''
        
        def style_change(v):
            return 'background-color: #FFF2CC; color: black;' if v != '변화 없음' else ''

        cols_show = ['대분류', '중분류', '소분류', '모델명', '제품번호', '25년 1월', '26년 1월', '작년 대비 변화', '상태']
        final_cols = [c for c in cols_show if c in f_df.columns]

        st.dataframe(
            f_df[final_cols].style.map(style_status, subset=['상태'] if '상태' in final_cols else None).map(style_change, subset=['작년 대비 변화'] if '작년 대비 변화' in final_cols else None),
            use_container_width=True, height=800
        )
    else:
        st.info("데이터 없음")

# [PAGE 2] 보고서
elif page == "📊 보고서 (Report)":
    st.subheader("📉 자산 변동 현황")
    st.markdown("---")

    cnt_26 = df['26년 1월'].notna().sum()
    def get_cnt(c): return df[c].astype(str).str.upper().str.contains('V').sum() if c in df.columns else 0

    c1 = get_cnt('신규재고')
    c2 = get_cnt('업무용')
    loss = get_cnt('25년~26년 행사장 분실') + get_cnt('25~26년 사무실 분실')
    disp = get_cnt('25년도 폐기') + get_cnt('폐기')
    trans = get_cnt('25년도 판매, 이관, 기증') + get_cnt('이관, 판매, 기증')
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("2026년 총 재고", f"{cnt_26:,}")
    m2.metric("✨ 신규", f"{c1:,}")
    m3.metric("🏢 업무용", f"{c2:,}")
    m4.metric("📉 분실", f"{loss:,}")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("🗑️ 폐기", f"{disp:,}")
    m6.metric("🤝 이관/판매", f"{trans:,}")

    st.markdown("---")
    st.subheader("차트 분석")
    
    dat = pd.DataFrame({
        '항목': ['행사장 분실', '사무실 분실', '25~26 폐기', '기타 폐기', '25~26 이관', '기타 이관'],
        '수량': [get_cnt('25년~26년 행사장 분실'), get_cnt('25~26년 사무실 분실'), get_cnt('25년도 폐기'), get_cnt('폐기'), get_cnt('25년도 판매, 이관, 기증'), get_cnt('이관, 판매, 기증')],
        '색상': ['#dc3545', '#fd7e14', '#A0522D', '#C19A6B', '#87CEEB', '#17a2b8']
    })
    dat = dat[dat['수량'] > 0]
    
    if not dat.empty:
        fig = px.bar(dat, x='항목', y='수량', color='항목', text='수량', color_discrete_sequence=dat['색상'].tolist())
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    # [여기 수정됨] 제목 변경 완료
    st.subheader("📋 25년 변화 상세 내역 보기")
    t0, t1, t2, t3, t4 = st.tabs(["✨ 신규", "⚠️ 분실", "🤝 판매/이관", "🗑️ 폐기", "🏢 업무용"])
    
    v_cols = ['대분류', '중분류', '소분류', '모델명', '제품번호', '26년 1월']
    real_cols = [c for c in v_cols if c in df.columns]

    with t0:
        if '신규재고' in df.columns:
            d = df[df['신규재고'].astype(str).str.upper().str.contains('V')]
            st.dataframe(d[real_cols], use_container_width=True) if not d.empty else st.info("없음")

    with t1:
        c1 = df['25년~26년 행사장 분실'].astype(str).str.upper().str.contains('V') if '25년~26년 행사장 분실' in df.columns else False
        c2 = df['25~26년 사무실 분실'].astype(str).str.upper().str.contains('V') if '25~26년 사무실 분실' in df.columns else False
        d = df[c1 | c2].copy()
        if not d.empty:
            d['구분'] = np.where(d['25년~26년 행사장 분실'].astype(str).str.upper().str.contains('V'), '행사장', '사무실')
            st.dataframe(d[['구분'] + real_cols], use_container_width=True)
        else: st.success("없음")

    with t2:
        nm = '25년도 판매, 이관, 기증'
        if nm in df.columns:
            d = df[df[nm].astype(str).str.upper().str.contains('V')]
            st.dataframe(d[real_cols], use_container_width=True) if not d.empty else st.info("없음")

    with t3:
        nm = '25년도 폐기'
        if nm in df.columns:
            d = df[df[nm].astype(str).str.upper().str.contains('V')]
            st.dataframe(d[real_cols], use_container_width=True) if not d.empty else st.info("없음")
            
    with t4:
        if '업무용' in df.columns:
            d = df[df['업무용'].astype(str).str.upper().str.contains('V')]
            st.dataframe(d[real_cols], use_container_width=True) if not d.empty else st.info("없음")

# [PAGE 3] 폐기예정목록
elif page == "🗑️ 폐기예정목록":
    st.subheader("🗑️ 폐기 예정 자산")
    
    if df_disposal_target is not None and not df_disposal_target.empty:
        tab1, tab2 = st.tabs(["📋 전체 목록", "∑ 모델별 요약"])
        
        with tab1:
            dd = df_disposal_target.copy()
            if '상세사양' in dd.columns: dd = dd.drop(columns=['상세사양'])
            st.dataframe(dd, use_container_width=True, height=700)
            
        with tab2:
            grps = [c for c in ['대분류', '중분류', '모델명'] if c in df_disposal_target.columns]
            if not grps:
                st.warning("분류 기준 컬럼 없음")
            else:
                summ = df_disposal_target.groupby(grps).size().reset_index(name='수량')
                summ = summ.sort_values(by='수량', ascending=False).reset_index(drop=True)
                st.metric("총 폐기 수량", f"{summ['수량'].sum()}개")
                st.dataframe(summ, use_container_width=True)
    else:
        st.warning("데이터 없음 (시트명 확인 필요)")
