import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# 페이지 설정
st.set_page_config(page_title="BlastTap 6.0 AI Smart Control System", layout="wide")
st.title("🔥 BlastTap 6.0 AI Smart Control System")

# PDF 설명서 호출 부분 제거
# 오류방지: PDF 파일 없을 때 Streamlit Cloud에서 안전하게 실행

if 'log' not in st.session_state:
    st.session_state['log'] = []

# 장입수지 입력
st.sidebar.header("장입수지 입력")
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.5)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
slag_ratio = st.sidebar.number_input("Slag비율 (용선:슬래그)", value=2.25)
ore_size = st.sidebar.number_input("Ore 입도 (mm)", value=20.0)
coke_size = st.sidebar.number_input("Coke 입도 (mm)", value=60.0)
reduction_efficiency = st.sidebar.number_input("환원율 (기본)", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)
furnace_volume = st.sidebar.number_input("고로 유효내용적 (m³)", value=3200.0)

# 조업지수 입력
st.sidebar.header("조업지수 입력")
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=4000.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
oxygen_blow = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=6000.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=20.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.8)

# FeO / Si 보정
st.sidebar.header("FeO / Si 보정")
feo = st.sidebar.number_input("슬래그 FeO (%)", value=0.8)
si = st.sidebar.number_input("용선 Si (%)", value=0.5)
K_factor = st.sidebar.number_input("K 보정계수", value=1.0)

# AI 목표온도 계산
base_temp = 1500
oxygen_effect = oxygen_enrichment * 5
blast_effect = (blast_volume - 4000) * 0.02
slag_effect = (slag_ratio - 2.25) * 10
pressure_effect = (top_pressure - 2.5) * 8
target_temp = base_temp + oxygen_effect + blast_effect + slag_effect + pressure_effect
st.sidebar.write(f"AI 자동목표용선온도: {target_temp:.1f} °C")
measured_temp = st.sidebar.number_input("현장 용선온도 (°C)", value=1520.0)

# 장입속도
now = datetime.datetime.now()
today_start = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = min(elapsed_minutes, 1440)

st.sidebar.header("장입속도 입력")
mode = st.sidebar.radio("장입방식", ["장입속도 기반 (자동)", "누적 Charge 직접입력"])
if mode == "장입속도 기반 (자동)":
    charge_rate = st.sidebar.number_input("장입속도 (charge/h)", value=5.5)
    elapsed_charges = charge_rate * (elapsed_minutes / 60)
else:
    elapsed_charges = st.sidebar.number_input("누적 Charge 수", value=30.0)

# 출선 실적
st.sidebar.header("출선 실적")
lead_start_time = st.sidebar.time_input("선행 출선 시작시각", value=datetime.time(8, 0))
follow_start_time = st.sidebar.time_input("후행 출선 시작시각", value=datetime.time(9, 0))
lead_start_dt = datetime.datetime.combine(datetime.date.today(), lead_start_time)
follow_start_dt = datetime.datetime.combine(datetime.date.today(), follow_start_time)
lead_elapsed = (now - lead_start_dt).total_seconds() / 60
follow_elapsed = (now - follow_start_dt).total_seconds() / 60

lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.8)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.8)
lead_target = st.sidebar.number_input("선행 목표출선량 (ton)", value=1215.0)

completed_taps = st.sidebar.number_input("종료된 TAP 수", value=5)
