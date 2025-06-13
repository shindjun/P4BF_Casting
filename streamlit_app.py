import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# 페이지 설정
st.set_page_config(page_title="BlastTap 6.0 AI 통합조업엔진", layout="wide")
st.title("🔥 BlastTap 6.0 AI 실시간 통합조업 수지추적")

if 'log' not in st.session_state:
    st.session_state['log'] = []

# ----------------------------------------------------
# ① 장입수지 입력
# ----------------------------------------------------
st.sidebar.header("장입수지 입력")
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.5)
ore_coke_ratio = st.sidebar.number_input("Ore/Coke 비율", value=5.0)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
slag_ratio = st.sidebar.number_input("Slag비율 (용선:슬래그)", value=2.25)
ore_size = st.sidebar.number_input("Ore 입도 (mm)", value=20.0)
coke_size = st.sidebar.number_input("Coke 입도 (mm)", value=60.0)
reduction_efficiency = st.sidebar.number_input("환원율 (기본)", value=1.0)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# ----------------------------------------------------
# ② 조업지수 입력
# ----------------------------------------------------
st.sidebar.header("조업지수 입력")
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=4000.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
oxygen_blow = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=6000.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=20.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.8)

# ----------------------------------------------------
# ③ FeO / Si 보정 입력
# ----------------------------------------------------
st.sidebar.header("FeO / Si 보정 입력")
feo = st.sidebar.number_input("슬래그 FeO (%)", value=
