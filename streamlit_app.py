import streamlit as st
import pandas as pd
import datetime
import random

# 페이지 설정
st.set_page_config(page_title="BlastTap 5.8", layout="centered")
st.title("🔥 BlastTap 5.8: AI 차기출선 패턴 & 예상출선소요 통합판")

if 'log' not in st.session_state:
    st.session_state['log'] = []

# ------------------------------
# ① 장입수지 입력
# ------------------------------
st.sidebar.header("장입수지 입력")
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.5)
charge_speed = st.sidebar.number_input("장입속도 (min/ch)", value=11)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
slag_ratio = st.sidebar.number_input("Slag비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("환원율 (기본 1.0)", value=1.0)
ore_size = st.sidebar.number_input("Ore 입도 (mm)", value=20.0)
coke_size = st.sidebar.number_input("Coke 입도 (mm)", value=60.0)

# ------------------------------
# ② 조업지수 입력
# ------------------------------
st.sidebar.header("조업지수 입력")
rr = st.sidebar.number_input("환원제비 R.R (kg/T-P)", value=499.4)
cr = st.sidebar.number_input("탄소비 C.R (kg/T-P)", value=338.9)
pcr = st.sidebar.number_input("PCR (kg/T-P)", value=167.6)
blast_volume = st.sidebar.number_input("풍량 (Nm³/min)", value=7189)
blast_pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=3.978)
nose_pressure = st.sidebar.number_input("노정압 (kg/cm²)", value=2.320)
oxygen_enrichment = st.sidebar.number_input("산소부화량 (Nm³/hr)", value=36926)
humidification = st.sidebar.number_input("조습 (g/Nm³)", value=12)
lower_k = st.sidebar.number_input("하부K", value=0.0025)

# ------------------------------
# ③ 출선구 상태입력
# ------------------------------
st.sidebar.header("출선구 상태")
lead_tap = st.sidebar.number_input("선행 출선구 번호", min_value=1, value=1)
follow_tap = st.sidebar.number_input("후행 출선구 번호", min_value=1, value=3)
idle_raw = st.sidebar.text_input("대기출선구 번호 (콤마구분)", "2,4")
idle_taps = [int(x.strip()) for x in idle_raw.split(",") if x.strip()]

# ------------------------------
# ④ 출선시각 입력
# ------------------------------
st.sidebar.header("출선시각 입력")
today = datetime.date.today()
start_time = st.sidebar.time_input("선행출선 시작시각", value=datetime.time(8, 0))
lead_start_dt = datetime.datetime.combine(today, start_time)
follow_time = st.sidebar.time_input("후행출선 시작시각", value=datetime.time(10, 30))
follow_start_dt = datetime.datetime.combine(today, follow_time)

# ------------------------------
# ⑤ 출선속도 및 비트경
# ------------------------------
st.sidebar.header("출선속도 / 비트경")
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.8)
follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.8)
lead_phi = st.sidebar.number_input("선행 Φ 비트경 (mm)", value=45.0)
follow_phi = st.sidebar.number_input("후행 Φ 비트경 (mm)", value=45.0)

# ------------------------------
# ⑥ 누적출선실적 입력
# ------------------------------
st.sidebar.header("출선실적")
tap_data = st.sidebar.text_area("출선량 리스트 (콤마)", "1186,1186,1096,1194,1194,1287,1287,988")
tap_list = [float(x.strip()) for x in tap_data.split(",") if x.strip()]
total_tapped = sum(tap_list)

# ------------------------------
# 🔧 AI 수지계산
# ------------------------------
minutes_per_charge = charge_speed
total_charges = 240 / minutes_per_charge
total_ore = ore_per_charge * total_charges
total_coke = coke_per_charge * total_charges
total_fe = total_ore * (tfe_percent / 100)
size_effect = (20 / ore_size + 60 / coke_size) / 2
reduction_eff_adj = reduction_efficiency * size_effect * 0.9
hot_metal = total_fe * reduction_eff_adj
slag = hot_metal / slag_ratio
total_molten = hot_metal + slag
current_residual = total_molten - total_tapped
residual_rate = (current_residual / total_molten) * 100
if current_residual < 0: current_residual = 0

# ------------------------------
# 🔧 AI 공취 & 폐쇄예상
# ------------------------------
follow_150_dt = follow_start_dt + datetime.timedelta(minutes=150)
lead_blow_time = random.randint(120, 160) - (lead_phi - 45)*0.5 - (lead_speed-4.8)*2
lead_blowoff_dt = lead_start_dt + datetime.timedelta(minutes=lead_blow_time)
follow_blow_time = random.randint(130, 150) - (follow_phi - 45)*0.5 - (follow_speed-4.8)*2
follow_blowoff_dt = follow_start_dt + datetime.timedelta(minutes=follow_blow_time)

if random.random() < 0.12:
    failure_minutes = random.randint(80, 140)
    failure_dt = lead_start_dt + datetime.timedelta(minutes=failure_minutes)
else:
    failure_dt = lead_start_dt + datetime.timedelta(days=999)

lead_end_dt = min(follow_150_dt, lead_blowoff_dt, follow_blowoff_dt, failure_dt)

# ------------------------------
# 🔧 AI 대기출선 개시판정
# ------------------------------
early_offset = 0
if residual_rate >= 9: early_offset += 3
if blast_pressure >= 4.0: early_offset += 2
if lower_k >= 0.0027: early_offset += 1
if lead_speed <= 4.5: early_offset += 2
if lead_phi <= 42: early_offset += 1

base_delay = random.randint(10, 15)
final_delay = max(5, base_delay - early_offset)
idle_activation_dt = lead_end_dt + datetime.timedelta(minutes=final_delay)
next_idle = idle_taps[0] if idle_taps else '-'

# ------------------------------
# 🔧 AI 출선소요시간 패턴 추가
# ------------------------------
default_tap_amount = 1215
lead_expected_tap_time = default_tap_amount / lead_speed
follow_expected_tap_time = default_tap_amount / follow_speed

# ------------------------------
# 📊 결과출력
# ------------------------------

st.header("📊 BlastTap 5.8 AI 조업결과")

st.write(f"누적 Charge 수: {total_charges:.1f}")
st.write(f"Ore 장입: {total_ore:.1f} ton, Coke 장입: {total_coke:.1f} ton")
st.write(f"용선: {hot_metal:.1f} ton, 슬래그: {slag:.1f} ton")
st.write(f"누적 생성: {total_molten:.1f} ton, 출선량: {total_tapped:.1f} ton")
st.markdown(f"<h3 style='color:orange'>저선량: {current_residual:.1f} ton</h3>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:green'>저선율: {residual_rate:.2f} %</h3>", unsafe_allow_html=True)

if residual_rate >= 9: status = "⚠ 저선과다 위험"
elif residual_rate >= 7: status = "주의"
else: status = "✅ 정상"
st.markdown(f"<h2 style='color:red'>{status}</h2>", unsafe_allow_html=True)

st.subheader("AI 출선소요시간 예측")
st.write(f"선행출선 예상: {lead_expected_tap_time:.1f} 분")
st.write(f"후행출선 예상: {follow_expected_tap_time:.1f} 분")

st.subheader("AI 출선구 종료 및 공취예측")
st.write(f"후행 150분 도달: {follow_150_dt.strftime('%H:%M:%S')}")
st.write(f"선행공취 예상: {lead_blowoff_dt.strftime('%H:%M:%S')}")
st.write(f"후행공취 예상: {follow_blowoff_dt.strftime('%H:%M:%S')}")
st.write(f"AI폐쇄예상: {lead_end_dt.strftime('%H:%M:%S')}")

st.subheader("AI 차기 출선구 개시예측")
st.write(f"조업지수 보정: -{early_offset}분 → 대기출선({next_idle}번): {idle_activation_dt.strftime('%H:%M:%S')}")

record = {
    "시각": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "선행출선구": lead_tap,
    "후행출선구": follow_tap,
    "AI폐쇄예상": lead_end_dt.strftime('%H:%M:%S'),
    "대기출선개시": idle_activation_dt.strftime('%H:%M:%S'),
    "저선량": current_residual,
    "저선율(%)": residual_rate,
    "조업상태": status
}
st.session_state['log'].append(record)

st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업리포트_5_8.csv", mime='text/csv')
