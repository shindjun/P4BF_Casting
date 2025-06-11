import streamlit as st
import datetime
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="BlastTap 2.0", layout="centered")
st.title("🔥 BlastTap: 고로 출선 매니저 2.0 (공취예상시간 통합판) 🔥")

# 세션 상태 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []
if 'lead_phi' not in st.session_state:
    st.session_state['lead_phi'] = 45.0
if 'follow_phi' not in st.session_state:
    st.session_state['follow_phi'] = 45.0

# 실측 기본값
ol, os = 120.5, 44.6
ore_charge_measured = ol + os
coke_charge_measured = 33.5
daily_production_measured = 12640.5
measured_residual = 100.0

# --------------------------------
# 입력 (사이드바)
# --------------------------------
with st.sidebar:
    st.header("조업 입력")

    st.write(f"이번 선행 출선구 비트경 (Φ): **{st.session_state['lead_phi']} mm**")
    follow_phi_input = st.number_input("후행 출선구 비트경 (Φ, mm)", min_value=30.0, value=st.session_state['follow_phi'])

    lead_tap_amount = st.number_input("선행 출선량 (ton)", value=1150.0)
    follow_tap_amount = st.number_input("후행 출선량 (ton)", value=350.0)
    wait_time = st.number_input("출선 간격 (분)", value=15.0)

    lead_start_time = st.time_input("선행 출선 시작시각", value=datetime.time(10, 0))
    follow_start_time = st.time_input("후행 출선 시작시각", value=datetime.time(10, 10))

    ore_charge = st.number_input("Ore 장입량 (실측)", value=ore_charge_measured)
    coke_charge = st.number_input("Coke 장입량 (실측)", value=coke_charge_measured)
    daily_production = st.number_input("일일생산량 (실측)", value=daily_production_measured)
    slag_ratio = st.number_input("출선비 (용선:슬래그)", value=2.25)
    tfe_percent = st.number_input("T.Fe (%)", value=58.0)

    lead_speed_actual = st.number_input("선행 출선속도 (ton/min)", value=4.8)
    follow_speed_input = st.number_input("후행 출선속도 입력 (ton/min)", value=4.5)
    follow_speed_actual = min(follow_speed_input, 5.0)

    status = st.selectbox("조업 상태", ["정상", "휴풍", "휴풍 후 재송풍", "정전"])

    st.markdown("---")
    st.header("후행 출선 보정계수")

    follow_actual_time = st.number_input("실측 후행 출선시간 (분)", value=0.0)
    if follow_actual_time > 0:
        follow_theory_time = follow_tap_amount / follow_speed_actual
        auto_correction_factor = follow_actual_time / follow_theory_time
        st.write(f"자동계산 보정계수: **{auto_correction_factor:.3f}**")
    else:
        auto_correction_factor = 1.036

    correction_factor = st.number_input("최종 보정계수 설정", value=auto_correction_factor)

# --------------------------------
# 계산
# --------------------------------

if status == '휴풍':
    ore_charge_adj = ore_charge * 0.7
elif status == '정전':
    ore_charge_adj = 0
else:
    ore_charge_adj = ore_charge

initial_ramp_factor = 0.90
lead_speed_corrected = lead_speed_actual * initial_ramp_factor

lead_time_est = lead_tap_amount / lead_speed_corrected
follow_time_est_raw = follow_tap_amount / follow_speed_actual
follow_time_est = follow_time_est_raw * correction_factor

dual_time_est = (lead_tap_amount + follow_tap_amount) / (lead_speed_corrected + follow_speed_actual)

today = datetime.date.today()
lead_end_time = datetime.datetime.combine(today, lead_start_time) + datetime.timedelta(minutes=lead_time_est)
follow_end_time = datetime.datetime.combine(today, follow_start_time) + datetime.timedelta(minutes=follow_time_est)

# 선행 공취예상시간 (95% 지점)
lead_blowoff_time = lead_time_est * 0.95
lead_blowoff_dt = datetime.datetime.combine(today, lead_start_time) + datetime.timedelta(minutes=lead_blowoff_time)

# 수지계산
daily_charge = 126
total_ore = ore_charge_adj * daily_charge
total_fe_input = total_ore * (tfe_percent / 100)
reduction_ratio_calc = daily_production / total_fe_input if total_fe_input > 0 else 0

predicted_iron_output = daily_production
slag_amount = daily_production / slag_ratio
predicted_total_molten = predicted_iron_output + slag_amount
total_tap_amount = lead_tap_amount + follow_tap_amount

current_residual_mass_balance = predicted_total_molten - total_tap_amount
residual_rate = (current_residual_mass_balance / predicted_total_molten) * 100
residual_gap = current_residual_mass_balance - measured_residual

if residual_rate >= 9:
    melting_status = "⚠ 용융물 배출 불량 경향"
elif residual_rate >= 7:
    melting_status = "주의: 배출상태 점검 필요"
else:
    melting_status = "✅ 용융물 배출 양호"

st.session_state['lead_phi'] = follow_phi_input
st.session_state['follow_phi'] = follow_phi_input

# --------------------------------
# 출력
# --------------------------------

st.subheader("⏱ 출선시간 예측")
st.write(f"🟢 선행출선시간: {lead_time_est:.1f}분 → 종료: {lead_end_time.strftime('%H:%M:%S')}")
st.write(f"🟢 후행출선시간: {follow_time_est:.1f}분 → 종료: {follow_end_time.strftime('%H:%M:%S')}")

# 공취예상시간 출력 추가
st.subheader("💨 선행 공취예상 시각")
st.markdown(f"<h3 style='color:blue'>선행 공취예상: {lead_blowoff_dt.strftime('%H:%M:%S')} (95% 도달 시점)</h3>", unsafe_allow_html=True)

st.subheader("📊 저선량 및 저선율")
st.markdown(f"<h3 style='color:orange'>누적 저선량: {current_residual_mass_balance:.1f} ton</h3>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:green'>저선율: {residual_rate:.2f} %</h3>", unsafe_allow_html=True)
st.write(f"실측 저선량: {measured_residual:.1f} ton (오차 {residual_gap:+.1f} ton)")

st.subheader("🔎 용융물 수지 시각화")
chart_data = pd.DataFrame({
    '구분': ['누적 생성량', '누적 출선량', '예측 저선량'],
    'ton': [predicted_total_molten, total_tap_amount, current_residual_mass_balance]
}).set_index('구분')
st.bar_chart(chart_data, height=400)

st.subheader("⚠ 배출상태 진단")
st.markdown(f"<h2 style='color:red'>{melting_status}</h2>", unsafe_allow_html=True)

# 기록 저장
record = {
    "시각": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "선행출선량": lead_tap_amount,
    "후행출선량": follow_tap_amount,
    "선행시간": lead_time_est,
    "후행시간": follow_time_est,
    "공취예상시각": lead_blowoff_dt.strftime('%H:%M:%S'),
    "누적저선량": current_residual_mass_balance,
    "저선율(%)": residual_rate,
    "저선 오차": residual_gap,
    "배출상태": melting_status
}
st.session_state['log'].append(record)

# 누적 기록 출력
st.subheader("📋 누적 조업 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업기록.csv", mime='text/csv')
