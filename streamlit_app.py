import streamlit as st
import pandas as pd
import datetime
import random

# 페이지 설정
st.set_page_config(page_title="BlastTap 5.2", layout="centered")
st.title("🔥 BlastTap 5.2: 출선구 상태 직접입력판")

# 세션 상태 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# ----------------------
# 출선구 상태 직접 입력
# ----------------------
st.sidebar.header("출선구 상태 입력")

lead_tap = st.sidebar.number_input("현재 선행출선구 번호", min_value=1, value=1)
follow_tap = st.sidebar.number_input("현재 후행출선구 번호", min_value=1, value=3)

idle_raw = st.sidebar.text_input("대기출선구 번호 (콤마구분)", "2,4")
idle_taps = [int(x.strip()) for x in idle_raw.split(",") if x.strip()]

st.write(f"선행출선구: {lead_tap}번 | 후행출선구: {follow_tap}번 | 대기출선구: {idle_taps}")

# 조업 시작시각 입력
start_time = st.sidebar.time_input("선행출선 시작 시각", value=datetime.time(8, 0))
today = datetime.date.today()
lead_start_dt = datetime.datetime.combine(today, start_time)

# 대기출선구 지연시간
wait_after_lead_close = st.sidebar.slider("대기출선구 출선지연 (분)", 10, 20, 15)

# ----------------------
# 장입 및 수지계산 입력
# ----------------------
st.sidebar.header("장입 및 수지 입력")

elapsed_time = st.sidebar.number_input("경과 시간 (분)", min_value=0, value=240)
ore_per_charge = st.sidebar.number_input("Ore 장입 per Charge (ton)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입 per Charge (ton)", value=33.5)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
slag_ratio = st.sidebar.number_input("슬래그비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("환원율 (%)", value=1.0)

# ----------------------
# 출선실적 입력
# ----------------------
st.sidebar.header("출선실적 (누적)")

tap_data = st.sidebar.text_area("출선량 리스트 (콤마구분)", "1186, 1186, 1096, 1194, 1194, 1287, 1287, 988")
tap_list = [float(x.strip()) for x in tap_data.split(",") if x.strip()]
total_tapped = sum(tap_list)

# ----------------------
# 수지계산
# ----------------------
charge_per_hour = 3
minutes_per_charge = 60 / charge_per_hour
total_charges = elapsed_time / minutes_per_charge

total_ore = ore_per_charge * total_charges
total_coke = coke_per_charge * total_charges
total_fe = total_ore * (tfe_percent / 100)
theoretical_hot_metal = total_fe * reduction_efficiency
slag_amount = theoretical_hot_metal / slag_ratio
total_molten_generation = theoretical_hot_metal + slag_amount

current_residual = total_molten_generation - total_tapped
residual_rate = (current_residual / total_molten_generation) * 100

# ----------------------
# AI 선행출선종료 판정
# ----------------------

st.header("⚙ AI 출선종료 판정")

follow_theory_time = 150  # 후행출선 150분 이론

# 공취 시뮬 (130~150분)
blowoff_time = random.randint(130, 150)
follow_actual_time = min(follow_theory_time, blowoff_time)

# 출선구상태불량 시뮬 (15% 확률)
tap_failure_prob = 0.15
if random.random() < tap_failure_prob:
    failure_time = random.randint(80, 140)
    st.warning(f"출선구상태불량 발생! 조기종료: {failure_time}분")
else:
    failure_time = 9999

lead_total_time = min(follow_actual_time, failure_time)
lead_end_dt = lead_start_dt + datetime.timedelta(minutes=lead_total_time)
st.write(f"선행출선 종료예상시각: **{lead_end_dt.strftime('%H:%M:%S')}**")

# 대기출선구 활성화 시각
idle_activation_dt = lead_end_dt + datetime.timedelta(minutes=wait_after_lead_close)
idle_next = idle_taps[0] if idle_taps else '-'
st.write(f"대기출선구({idle_next}번) 개시예상시각: **{idle_activation_dt.strftime('%H:%M:%S')}**")

# ----------------------
# 저선 상태평가
# ----------------------

st.header("📊 누적 수지 및 저선량")

st.write(f"누적 Charge 수: {total_charges:.1f} charge")
st.write(f"누적 Ore 장입: {total_ore:.1f} ton")
st.write(f"이론 용선: {theoretical_hot_metal:.1f} ton")
st.write(f"슬래그 생성: {slag_amount:.1f} ton")
st.write(f"누적 생성량: {total_molten_generation:.1f} ton")
st.write(f"누적 출선량: {total_tapped:.1f} ton")

st.markdown(f"<h3 style='color:orange'>현재 저선량: {current_residual:.1f} ton</h3>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:green'>저선율: {residual_rate:.2f} %</h3>", unsafe_allow_html=True)

if residual_rate >= 9:
    status = "⚠ 용융물 배출 불량 경향"
elif residual_rate >= 7:
    status = "주의: 배출상태 점검 필요"
else:
    status = "✅ 용융물 배출 양호"

st.markdown(f"<h2 style='color:red'>{status}</h2>", unsafe_allow_html=True)

# ----------------------
# 누적 기록 저장
# ----------------------

record = {
    "시각": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "선행출선구": lead_tap,
    "후행출선구": follow_tap,
    "선행종료시각": lead_end_dt.strftime('%H:%M:%S'),
    "대기출선개시시각": idle_activation_dt.strftime('%H:%M:%S'),
    "누적생성량": total_molten_generation,
    "누적배출량": total_tapped,
    "현재저선량": current_residual,
    "저선율(%)": residual_rate,
    "배출상태": status
}
st.session_state['log'].append(record)

st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업리포트.csv", mime='text/csv')
