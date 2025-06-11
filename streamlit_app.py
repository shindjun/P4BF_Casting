import streamlit as st

st.set_page_config(page_title="고로 출선작업 계산기", layout="centered")
st.title("고로 출선작업 계산기 🔥")

# --- ① 출선구 설정 ---
st.header("① 출선구 설정")
lead_phi = st.number_input("선행 출선구 비트경 (Φ, mm)", min_value=30.0, value=45.0, step=1.0)
follow_phi = st.number_input("후행 출선구 비트경 (Φ, mm)", min_value=30.0, value=45.0, step=1.0)

# --- ② 출선 조건 입력 ---
st.header("② 출선 조건 입력")
tap_amount = st.number_input("1회 출선량 (ton)", min_value=0.0, value=1358.0, step=1.0)
wait_time = st.number_input("차기 출선까지 대기 시간 (분)", min_value=0.0, value=15.0, step=1.0)

# --- ③ 현재 출선속도 입력 ---
st.header("③ 현재 출선속도 입력")
lead_current_speed = st.number_input("선행 출선속도 (ton/min)", min_value=0.0, value=8.0)
follow_current_speed = st.number_input("후행 출선속도 (ton/min)", min_value=0.0, value=8.0)

# --- ④ K 계산 ---
calc_K_lead = lead_current_speed / (lead_phi ** 2) if lead_phi > 0 else 0
calc_K_follow = follow_current_speed / (follow_phi ** 2) if follow_phi > 0 else 0

st.markdown(f"📐 **선행 출선구 환산계수 K**: {calc_K_lead:.5f} ton/min·mm²")
st.markdown(f"📐 **후행 출선구 환산계수 K**: {calc_K_follow:.5f} ton/min·mm²")

# --- ⑤ 출선속도 및 시간 예측 ---
lead_speed_est = calc_K_lead * lead_phi ** 2
follow_speed_est = calc_K_follow * follow_phi ** 2
dual_speed_est = lead_speed_est + follow_speed_est

lead_time_est = tap_amount / lead_speed_est if lead_speed_est > 0 else 0
follow_time_est = tap_amount / follow_speed_est if follow_speed_est > 0 else 0
dual_time_est = tap_amount / dual_speed_est if dual_speed_est > 0 else 0

ideal_delay_after_lead = max(3.0, (follow_time_est - lead_time_est) / 2) if follow_time_est > lead_time_est else 3.0

# --- ⑤ 결과 출력 ---
st.header("⑤ 예측 출선시간 결과")
st.write(f"● 선행 출선속도: {lead_speed_est:.2f} ton/min → 출선시간: {lead_time_est:.1f} 분")
with st.expander("🔍 계산 근거 보기 - 선행 출선시간"):
    st.markdown("출선시간 = 출선량 / 출선속도")
    st.markdown("출선속도 = K × Φ²")

st.write(f"● 후행 출선속도: {follow_speed_est:.2f} ton/min → 출선시간: {follow_time_est:.1f} 분")
with st.expander("🔍 계산 근거 보기 - 후행 출선시간"):
    st.markdown("출선시간 = 출선량 / 출선속도")
    st.markdown("출선속도 = K × Φ²")

st.success(f"▶ 2공 동시 출선 예상시간: {dual_time_est:.2f} 분 (출선량 {tap_amount:.0f} ton 기준)")
with st.expander("🔍 계산 근거 보기 - 2공 동시 출선시간"):
    st.markdown("출선속도(총) = 선행속도 + 후행속도")
    st.markdown("출선시간 = 출선량 / 총출선속도")

st.info(f"⏱ **후행 출선은 선행 출선 종료 후 약 {ideal_delay_after_lead:.1f}분 후 시작하는 것이 적정합니다.**")
with st.expander("🔍 계산 근거 보기 - 후행 출선 지연시간"):
    st.markdown("지연시간 = max(3.0분, (후행출선시간 - 선행출선시간)/2)")

# --- ⑧ 자동 계산 결과 ---
daily_ore = ore_charge * daily_charge
daily_coke = coke_charge * daily_charge
hourly_charge = daily_charge / 24
daily_iron = iron_speed * 1440
daily_slag = daily_iron / slag_ratio if slag_ratio else 0
total_radiation = (daily_iron + daily_slag) * 0.05

st.header("⑧ 자동 계산 결과")
st.markdown(f"📊 **Ore/Coke 비율**: {ore_coke_ratio:.2f}")
st.markdown(f"📊 **시간당 Charge 수**: {hourly_charge:.2f} 회/hr")
st.markdown(f"📊 **하루 출선량**: {daily_iron:.0f} ton")
st.markdown(f"📊 **슬래그량 추정**: {daily_slag:.0f} ton")
st.markdown(f"📊 **현재 노내 저선량 예측**: {total_radiation:.1f} ton/day")
with st.expander("🔍 계산 근거 보기 - 저선량 예측"):
    st.markdown("저선량 = (하루 용선 + 슬래그) × 0.05")

# --- ⑨ 장입 + 환원제비 기반 출선 예측 ---
recovery_rate = estimate_recovery_rate(ore_coke_ratio)
if reduction_ratio > 0:
    recovery_rate *= (1 + (1 - reduction_ratio))

estimated_iron = ore_charge * recovery_rate
predicted_speed = calc_K_lead * lead_phi ** 2
predicted_tap_time = estimated_iron / predicted_speed if predicted_speed > 0 else 0

real_time_iron = iron_output_rate * current_charge * (ore_charge / planned_charge)
real_time_slag = real_time_iron / slag_ratio if slag_ratio else 0
real_time_total_output = real_time_iron + real_time_slag
real_time_residual = real_time_total_output * 0.05

st.header("⑨ 장입 + 환원제비 기반 출선 예측")
st.markdown(f"🧮 ORE/COKE 비율: **{ore_coke_ratio:.2f}**")
st.markdown(f"📈 회수율 추정: **{recovery_rate*100:.1f}%**")
st.markdown(f"📦 예상 출선량: **{estimated_iron:.1f} ton**")
st.markdown(f"⏱ 예상 출선시간(선행 기준): **{predicted_tap_time:.1f} 분**")
with st.expander("🔍 계산 근거 보기 - 예상 출선량 및 시간"):
    st.markdown("출선량 = ORE × 회수율 (회수율은 ORE/COKE 비율 + 환원도 기반)")
    st.markdown("출선시간 = 출선량 / (K × Φ²)")

st.markdown(f"📦 누적 용선 생산량(현재 Charge 기준): **{real_time_iron:.1f} ton**")
st.markdown(f"📦 누적 슬래그 포함 생산량: **{real_time_total_output:.1f} ton**")
st.markdown(f"📦 현재 노내 잔류량(5%): **{real_time_residual:.1f} ton**")
with st.expander("🔍 계산 근거 보기 - 누적 생산량 및 저선량"):
    st.markdown("누적 용선량 = 생산속도 × Charge 수 × 단위당 장입량")
    st.markdown("총출선량 = 용선 + 슬래그")
    st.markdown("저선량 = 총출선량 × 0.05")