import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.font_manager as fm

# 한국어 폰트 설정
rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

# 페이지 기본 설정
st.set_page_config(page_title="전력량 계산 및 가구별 전력량 시각화", layout="wide")

# 탭 구성
tab1, tab2 = st.tabs(["1. 전력량 계산기", "2. 가구별 전력량 데이터 시각화"])

# 1. 전력량 계산기
with tab1:
    st.title("전력량 계산기")

    # 데이터 저장용 리스트 초기화
    if "device_data" not in st.session_state:
        st.session_state.device_data = [
            {"기기": "", "전력 소모량 (W)": 1, "일 사용 시간 (시간)": 1} for _ in range(3)
        ]

    # 1. 기기 데이터 입력
    st.header("1. 기기 데이터 입력")
    cols = st.columns(3)  # 3열 배치
    for idx, device in enumerate(st.session_state.device_data):
        with cols[idx % 3]:  # 3열 순환 배치
            st.write(f"**기기 {idx + 1}**")
            device_name = st.text_input(f"기기 이름 {idx + 1}", value=device["기기"], key=f"device_name_{idx}", label_visibility="collapsed", placeholder="기기 이름")
            power = st.number_input(
                f"전력 소모량 (W) {idx + 1}",
                min_value=1,
                value=max(device["전력 소모량 (W)"], 1),
                step=1,
                key=f"power_{idx}",
                label_visibility="collapsed",
            )
            usage_hours = st.number_input(
                f"일 사용 시간 (시간) {idx + 1}",
                min_value=1,
                value=max(device["일 사용 시간 (시간)"], 1),
                step=1,
                key=f"usage_hours_{idx}",
                label_visibility="collapsed",
            )
            st.session_state.device_data[idx] = {
                "기기": device_name,
                "전력 소모량 (W)": power,
                "일 사용 시간 (시간)": usage_hours,
            }

    # 데이터 삭제 및 추가
    cols = st.columns(2)
    with cols[0]:
        if st.button("기기 추가"):
            st.session_state.device_data.append({"기기": "", "전력 소모량 (W)": 1, "일 사용 시간 (시간)": 1})
            st.success("새로운 기기 입력 칸이 추가되었습니다.")
    with cols[1]:
        if len(st.session_state.device_data) > 3 and st.button("기기 삭제"):
            st.session_state.device_data.pop()
            st.warning("마지막 기기가 삭제되었습니다.")

    # 2. 전력 소모 데이터표
    st.header("2. 전력 소모 데이터표")
    df = pd.DataFrame(st.session_state.device_data)
    df["일 전력량 (kWh)"] = df["전력 소모량 (W)"] * df["일 사용 시간 (시간)"] / 1000
    df["월 전력량 (kWh)"] = df["일 전력량 (kWh)"] * 30
    st.dataframe(df)

    # 3. 파이차트: 하루 기기별 전력소모량 비율
    st.header("3. 하루 기기별 전력소모량 비율 차트")
    if not df.empty and df["일 전력량 (kWh)"].sum() > 0:
        fig, ax = plt.subplots(figsize=(6, 6))  # 파이차트 크기 조정
        ax.pie(
            df["일 전력량 (kWh)"], 
            labels=df["기기"], 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=plt.cm.Paired.colors
        )
        plt.title("하루 기기별 전력 소모 비율")
        st.pyplot(fig)

    # 4. 월 사용량 및 전기요금 계산 (누진세 적용)
    st.header("4. 월 사용량 및 전기요금")
    total_monthly_energy = df["월 전력량 (kWh)"].sum()
    st.write(f"총 월 사용량: **{total_monthly_energy:.2f} kWh**")

    # 누진세 계산
    if total_monthly_energy <= 200:
        electricity_bill = total_monthly_energy * 100  # 1단계
    elif total_monthly_energy <= 400:
        electricity_bill = 200 * 100 + (total_monthly_energy - 200) * 200  # 2단계
    else:
        electricity_bill = 200 * 100 + 200 * 200 + (total_monthly_energy - 400) * 300  # 3단계

    st.write(f"예상 전기요금: **{electricity_bill:,.0f} 원**")

    # 5. 목표 전력 사용량 입력 및 피드백
    st.header("5. 목표 전력 사용량 설정")
    goal_energy = st.number_input("목표 월 전력 사용량 (kWh)", min_value=1, step=1)
    if goal_energy:
        if total_monthly_energy > goal_energy:
            st.warning(f"현재 사용량이 목표를 초과했습니다. **{total_monthly_energy - goal_energy:.2f} kWh**를 줄이세요.")
        else:
            st.success(f"축하합니다! 목표 사용량보다 **{goal_energy - total_monthly_energy:.2f} kWh** 적게 사용하고 있습니다.")

# 2. 가구별 전력량 데이터 시각화
with tab2:
    st.title("가구별 전력량 데이터 시각화")

    # 파일 업로드
    uploaded_file = st.file_uploader("데이터 파일 업로드 (CSV)", type=["csv"])

    if uploaded_file:
        # 데이터 로드 및 전처리
        df = pd.read_csv(uploaded_file, encoding="utf-8")
        df["대상가구수(호)"] = df["대상가구수(호)"].str.replace(",", "").astype(int)
        df["가구당 평균전력 사용량(kWh)"] = df["가구당 평균전력 사용량(kWh)"].astype(float)
        df["가구당 평균 전기요금(원)"] = df["가구당 평균 전기요금(원)"].str.replace(",", "").astype(int)

        # 1. 데이터 표시
        st.subheader("1. 데이터 내용")
        st.dataframe(df)

        # 2. 월별 가구당 평균 사용량 및 전기요금
        st.subheader("2. 월별 가구당 평균 사용량 및 전기요금")
        gu_selected = st.selectbox("구 선택", df["시군구"].unique())
        gu_data = df[df["시군구"] == gu_selected]

        # 평균 사용량
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(gu_data["연월"], gu_data["가구당 평균전력 사용량(kWh)"], color="skyblue")
        ax.set_title(f"{gu_selected} 월별 가구당 평균 사용량")
        ax.set_xlabel("연월")
        ax.set_ylabel("평균 사용량 (kWh)")
        ax.set_xticklabels(gu_data["연월"], rotation=45)
        st.pyplot(fig)

        # 평균 요금
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(gu_data["연월"], gu_data["가구당 평균 전기요금(원)"], color="orange")
        ax.set_title(f"{gu_selected} 월별 가구당 평균 전기요금")
        ax.set_xlabel("연월")
        ax.set_ylabel("평균 요금 (원)")
        #ax.set_xticks(range(len(gu_data["연월"])))
        ax.set_xticklabels(gu_data["연월"], rotation=45)
        st.pyplot(fig)

        # 3. 추이 그래프
        st.subheader("3. 추이 그래프")
        options = ["가구당 평균전력 사용량(kWh)", "가구당 평균 전기요금(원)"]
        selected_option = st.radio("데이터 선택", options)

        aggregated_data = df.groupby("연월").agg(
            총가구수=("대상가구수(호)", "sum"),
            총사용량=("가구당 평균전력 사용량(kWh)", "sum"),
            총요금=("가구당 평균 전기요금(원)", "sum"),
        )
        aggregated_data["가구당 평균 사용량"] = aggregated_data["총사용량"] / aggregated_data["총가구수"]
        aggregated_data["가구당 평균 요금"] = aggregated_data["총요금"] / aggregated_data["총가구수"]

        fig, ax = plt.subplots(figsize=(10, 5))
        if selected_option == "가구당 평균전력 사용량(kWh)":
            data_to_plot = aggregated_data["가구당 평균 사용량"]
            ylabel = "평균 사용량 (kWh)"
            color = "green"
        else:
            data_to_plot = aggregated_data["가구당 평균 요금"]
            ylabel = "평균 요금 (원)"
            color = "orange"

        ax.plot(aggregated_data.index, data_to_plot, marker="o", color=color, label=selected_option)
        for i, value in enumerate(data_to_plot):
            ax.text(i, value, f"{value:,.0f}", ha="center", va="bottom", fontsize=9, color="black", fontweight="bold")

        ax.set_title("추이 그래프", fontsize=14, fontweight="bold")
        ax.set_xlabel("연월")
        ax.set_ylabel(ylabel)
        ax.set_xticks(range(len(aggregated_data.index)))
        ax.set_xticklabels(aggregated_data.index, rotation=45)
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        st.pyplot(fig)

    else:
        st.info("데이터 파일을 업로드해 주세요.")
