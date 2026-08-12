import streamlit as st
import pandas as pd
import numpy as np

# 페이지 기본 설정
st.set_page_config(layout="wide", page_title="나만의 포트폴리오")

st.title("🚀매출 데이터 분석 리포트")
st.markdown("---")

# [사이드바] 데이터 업로드 및 설정
with st.sidebar:
    st.header("설정")
    uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])
    
    # 차트 옵션 (데이터가 있을 때만 활성화)
    chart_type = st.selectbox("차트 종류 선택", ["Line Chart", "Bar Chart", "Area Chart"])

    prevcnt = st.slider("미리 보기 개수", 5, 50, 10)

# [메인] 데이터 처리 로직
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("파일 업로드 성공!")
else:
    # 실습용 더미 데이터 생성 (파일이 없을 경우)
    st.info("CSV 파일을 업로드하면 해당 데이터로 분석합니다. (현재는 샘플 데이터)")
    df = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['A', 'B', 'C']
    )

# [레이아웃] 다중 컬럼으로 화면 분할
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 데이터 미리보기")
    st.dataframe(df.head(prevcnt)) # 데이터프레임 출력

with col2:
    st.subheader("📈 데이터 시각화")
    # 선택한 차트 종류에 따라 시각화
    if chart_type == "Line Chart":
        st.line_chart(df)
    elif chart_type == "Bar Chart":
        st.bar_chart(df)
    elif chart_type == "Area Chart":
        st.area_chart(df)

# 통계 요약
st.subheader("기초 통계")
with st.expander("기초 통계"):
    st.write(df.describe())
