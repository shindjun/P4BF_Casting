import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# 페이지설정
st.set_page_config(page_title="BlastTap 6.0 AI Smart Control System", layout="wide")
st.title("🔥 BlastTap 6.0 AI Smart Control System")

if 'log' not in st.session_state:
    st.session_state['log'] = []

# PDF 수식설명서 버튼
st.sidebar.header("📄 시스템 설명서")
with open("blasttap6_manual.pdf", "rb") as file:
    st.sidebar.download_button("📥 수식설명서 다운로드", file, file_name="blasttap6_manual.pdf")

# 입력항목 --------------------------------------------------------

# 장입수지
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

# 조업지수
st.sidebar.header("조업지수 입력")
blast_volume = st.sidebar.number_input("송풍량 (Nm³/min)", value=4000.0)
oxygen_enrichment = st.sidebar.number_input("산소부화율 (%)", value=3.0)
oxygen_blow = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=6000.0)
humidification = st.sidebar.number_input("조습량 (g/Nm³)", value=20.0)
top_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.5)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.8)

# FeO, Si, K
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

# 계획수
st.sidebar.header("계획입력")
plan_charges = st.sidebar.number_input("계획 Charge 수", value=126)
plan_taps = st.sidebar.number_input("계획 TAP 수", value=9)
expected_total_molten = st.sidebar.number_input("예상이론출선량 (ton)", value=3100.0)

# ---------------------------------------------------
# AI 보정 수식계산
# ---------------------------------------------------
size_effect = (20 / ore_size + 60 / coke_size) / 2
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05
gas_effect = 1 + (blast_volume - 4000) / 8000
oxygen_boost = 1 + (oxygen_enrichment / 10)
humidity_effect = 1 - (humidification / 100)
pressure_boost = 1 + (top_pressure - 2.5) * 0.05
blow_pressure_boost = 1 + (blast_pressure - 3.5) * 0.03
feo_effect = 1 - (feo / 10)
si_effect = 1 + (si / 5)
temp_effect = 1 + ((measured_temp - target_temp) / 100) * 0.03

reduction_eff_total = reduction_efficiency * size_effect * melting_effect * \
                      gas_effect * oxygen_boost * humidity_effect * \
                      pressure_boost * blow_pressure_boost * feo_effect * \
                      si_effect * temp_effect * K_factor * 0.9

# ---------------------------------------------------
# 생성량 수지계산
# ---------------------------------------------------
total_ore = ore_per_charge * elapsed_charges
total_fe = total_ore * (tfe_percent / 100)
hot_metal = total_fe * reduction_eff_total
slag = hot_metal / slag_ratio
total_molten = hot_metal + slag

# 이론출선량 자동산출
plan_total_ore = ore_per_charge * plan_charges
plan_total_fe = plan_total_ore * (tfe_percent / 100)
plan_hot_metal = plan_total_fe * reduction_eff_total
plan_slag = plan_hot_metal / slag_ratio
plan_total_molten = plan_hot_metal + plan_slag

# AI+현장 혼합보정 적용
final_total_molten = (plan_total_molten * 0.7) + (expected_total_molten * 0.3)

# ---------------------------------------------------
# 출선수지 및 저선계산
# ---------------------------------------------------
lead_in_progress = lead_speed * lead_elapsed
follow_in_progress = follow_speed * follow_elapsed
total_tapped = lead_in_progress + follow_in_progress

residual_molten = max(final_total_molten - total_tapped, 0)
residual_rate = (residual_molten / final_total_molten) * 100

if residual_rate >= 9: status = "⚠ 저선과다 위험"
elif residual_rate >= 7: status = "주의"
else: status = "✅ 정상"

# ---------------------------------------------------
# 공취시간, 평균수지계산
# ---------------------------------------------------
lead_close_time = lead_start_dt + datetime.timedelta(minutes=(lead_target / lead_speed))
gap_minutes = (lead_close_time - follow_start_dt).total_seconds() / 60

avg_hot_metal_per_tap = hot_metal / completed_taps
avg_slag_per_tap = slag / completed_taps

# ---------------------------------------------------
# 시각화
# ---------------------------------------------------
st.header("📊 수지시각화")
time_labels = [i for i in range(0, int(elapsed_minutes)+1, 60)]
gen_series = [(final_total_molten / 1440) * t for t in time_labels]
tap_series = [total_tapped] * len(time_labels)
residual_series = [g - total_tapped for g in gen_series]

plt.figure(figsize=(10, 5))
plt.plot(time_labels, gen_series, label="누적 생성량")
plt.plot(time_labels, tap_series, label="누적 출선량")
plt.plot(time_labels, residual_series, label="저선량")
plt.xlabel("경과시간 (분)")
plt.ylabel("ton")
plt.title("실시간 용융수지 추적")
plt.legend()
plt.grid()
st.pyplot(plt)

# ---------------------------------------------------
# 결과 출력
# ---------------------------------------------------
st.header("📊 AI 수지 분석결과")

st.write(f"누적 생성량: {final_total_molten:.1f} ton")
st.write(f"누적 배출량: {total_tapped:.1f} ton")
st.write(f"현재 저선량: {residual_molten:.1f} ton")
st.write(f"저선율: {residual_rate:.2f} %")
st.write(f"조업상태: {status}")
st.write(f"선행 예상폐쇄시각: {lead_close_time.strftime('%H:%M')}")
st.write(f"공취 예상시간: {gap_minutes:.1f} 분")
st.write(f"TAP당 평균 용선배출량: {avg_hot_metal_per_tap:.1f} ton")
st.write(f"TAP당 평균 슬래그배출량: {avg_slag_per_tap:.1f} ton")
st.write(f"AI 이론출선량: {plan_total_molten:.1f} ton")
st.write(f"입력 이론출선량: {expected_total_molten:.1f} ton")

# ---------------------------------------------------
# 누적 기록저장
# ---------------------------------------------------
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "누적생성량": final_total_molten,
    "누적출선량": total_tapped,
    "저선량": residual_molten,
    "저선율": residual_rate
}
st.session_state['log'].append(record)

st.header("📋 누적 리포트 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업리포트.csv", mime='text/csv')
