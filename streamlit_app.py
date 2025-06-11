import streamlit as st
import pandas as pd
import datetime
import random

# 페이지 설정
st.set_page_config(page_title="BlastTap 5.6", layout="centered")
st.title("🔥 BlastTap 5.6: 예상공취시각 출력판")

if 'log' not in st.session_state:
    st.session_state['log'] = []

# ---------------------
# 출선구 상태 입력
# ---------------------
st.sidebar.header("출선구 상태 입력")

lead_tap = st.sidebar.number_input("선행출선구 번호", min_value=1, value=1)
follow_tap = st.sidebar.number_input("후행출선구 번호", min_value=1, value=3)
idle_raw = st.sidebar.text_input("대기출선구 번호 (콤마구분)", "2,4")
idle_taps = [int(x.strip()) for x in idle_raw.split(",") if x.strip()]

start_time = st.sidebar.time_input("선행출선 시작시각", value=datetime.time(8, 0))
today = datetime.date.today()
lead_start_dt = datetime.datetime.combine(today, start_time)

follow_time = st.sidebar.time_input("후행출선 시작시각", value=datetime.time(10, 30))
follow_start_dt = datetime.datetime.combine(today, follow_time)

wait_after_lead_close = st.sidebar.slider("기본 대기출선구 지연 (분)", 10, 20, 15)

# ---------------------
# 장입 및 수지 입력
# ---------------------
st.sidebar.header("장입 수지입력")

elapsed_time = st.sidebar.number_input("경과 시간 (분)", min_value=0, value=240)
ore_per_charge = st.sidebar.number_input("Ore per Charge (ton)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke per Charge (ton)", value=33.5)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("환원율", value=1.0)

# ---------------------
# 조업지수 입력
# ---------------------
st.sidebar.header("조업지수 영향 (AI판정용)")

pressure = st.sidebar.number_input("풍압 (kg/cm²)", value=2.2)
lower_k = st.sidebar.number_input("하부 K", value=0.0025)
tap_speed = st.sidebar.number_input("출선속도 (ton/min)", value=4.8)
bit_diameter = st.sidebar.number_input("출선구 비트경 (mm)", value=45.0)

# ---------------------
# 출선실적 입력
# ---------------------
st.sidebar.header("출선실적")

tap_data = st.sidebar.text_area("출선량 리스트 (콤마구분)", "1186,1186,1096,1194,1194,1287,1287,988")
tap_list = [float(x.strip()) for x in tap_data.split(",") if x.strip()]
total_tapped = sum(tap_list)

# ---------------------
# 수지계산
# ---------------------
charge_per_hour = 3
minutes_per_charge = 60 / charge_per_hour
total_charges = elapsed_time / minutes_per_charge

total_ore = ore_per_charge * total_charges
total_coke = coke_per_charge * total_charges
total_fe = total_ore * (tfe_percent / 100)
hot_metal = total_fe * reduction_efficiency
slag = hot_metal / slag_ratio
total_molten = hot_metal + slag

current_residual = total_molten - total_tapped
residual_rate = (current_residual / total_molten) * 100

# ---------------------
# AI 예상폐쇄시간 계산
# ---------------------
st.header("⚙ AI출선구 예상폐쇄시간")

follow_150_dt = follow_start_dt + datetime.timedelta(minutes=150)
lead_blowoff_dt = lead_start_dt + datetime.timedelta(minutes=random.randint(120, 160))
follow_blowoff_dt = follow_start_dt + datetime.timedelta(minutes=random.randint(130, 150))

if random.random() < 0.15:
    failure_minutes = random.randint(80, 140)
    failure_dt = lead_start_dt + datetime.timedelta(minutes=failure_minutes)
    st.warning(f"출선구상태불량 발생 예상: {failure_dt.strftime('%H:%M:%S')}")
else:
    failure_dt = lead_start_dt + datetime.timedelta(days=999)

lead_end_dt = min(follow_150_dt, lead_blowoff_dt, follow_blowoff_dt, failure_dt)

st.write(f"후행출선 150분 도달시각: {follow_150_dt.strftime('%H:%M:%S')}")
st.write(f"👉 선행공취 예상시각: {lead_blowoff_dt.strftime('%H:%M:%S')}")
st.write(f"👉 후행공취 예상시각: {follow_blowoff_dt.strftime('%H:%M:%S')}")
st.write(f"👉 AI폐쇄예상시각: {lead_end_dt.strftime('%H:%M:%S')}")

# ---------------------
# AI 대기출선 개시판정 (조업지수 확장)
# ---------------------
st.header("⚙ AI 대기출선 개시")

early_offset = 0
if residual_rate >= 9: early_offset += 3
if pressure >= 2.3: early_offset += 2
if lower_k >= 0.0027: early_offset += 1
if tap_speed <= 4.5: early_offset += 2
if bit_diameter <= 42: early_offset += 1

base_delay = random.randint(10, 15)
final_delay = max(5, base_delay - early_offset)

idle_activation_dt = lead_end_dt + datetime.timedelta(minutes=final_delay)
next_idle = idle_taps[0] if idle_taps else '-'

st.write(f"조업지수 보정결과: -{early_offset}분 → 대기출선구({next_idle}번) 개시예상: {idle_activation_dt.strftime('%H:%M:%S')}")

# ---------------------
# 저선 및 수지 상태
# ---------------------
st.header("📊 저선 및 수지")

st.write(f"누적 Charge: {total_charges:.1f}")
st.write(f"Ore: {total_ore:.1f} ton, Coke: {total_coke:.1f} ton")
st.write(f"용선: {hot_metal:.1f} ton, 슬래그: {slag:.1f} ton")
st.write(f"누적 생성: {total_molten:.1f} ton, 누적 출선: {total_tapped:.1f} ton")

st.markdown(f"<h3 style='color:orange'>저선량: {current_residual:.1f} ton</h3>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:green'>저선율: {residual_rate:.2f} %</h3>", unsafe_allow_html=True)

if residual_rate >= 9: status = "⚠ 저선과다"
elif residual_rate >= 7: status = "주의"
else: status = "✅ 정상"

st.markdown(f"<h2 style='color:red'>{status}</h2>", unsafe_allow_html=True)

# ---------------------
# 누적기록 저장
# ---------------------
record = {
    "시각": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "선행출선구": lead_tap,
    "후행출선구": follow_tap,
    "선행공취": lead_blowoff_dt.strftime('%H:%M:%S'),
    "후행공취": follow_blowoff_dt.strftime('%H:%M:%S'),
    "AI폐쇄예상": lead_end_dt.strftime('%H:%M:%S'),
    "대기출선개시": idle_activation_dt.strftime('%H:%M:%S'),
    "저선량": current_residual,
    "저선율(%)": residual_rate,
    "배출상태": status
}
st.session_state['log'].append(record)

st.header("📋 누적 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업리포트.csv", mime='text/csv')
