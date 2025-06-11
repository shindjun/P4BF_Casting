import streamlit as st
import datetime
import pandas as pd

st.set_page_config(page_title="BlastTap: 고로 출선 매니저", layout="centered")
st.title("🔥 BlastTap: 고로 출선 매니저 1.2 (안정배포형) 🔥")

# 세션 상태 초기화
if 'log' not in st.session_state:
    st.session_state['log'] = []

# ① 출선구 설정
st.header("① 출선구 설정")
lead_phi = st.number_input("선행 출선구 비트경 (Φ, mm)", min_value=30.0, value=45.0)
follow_phi = st.number_input("후행 출선구 비트경 (Φ, mm)", min_value=30.0, value=45.0)

# ② 출선조건 입력
st.header("② 출선 조건 입력")
tap_amount = st.number_input("1회 출선량 (ton)", value=1215.0)
wait_time = st.number_input("출선 간격 (분)", value=15.0)

# ③ 출선 시작시각 입력
st.header("③ 출선 시작 시각 입력")
lead_start_time = st.time_input("선행 출선 시작 시각", value=datetime.time(10, 0))
follow_start_time = st.time_input("후행 출선 시작 시각", value=datetime.time(10, 10))

# ④ 조업 데이터 입력
st.header("④ 현장 조업 데이터 입력")
ore_charge = st.number_input("1회 Ore 장입량 (ton)", value=165.1)
coke_charge = st.number_input("1회 Coke 장입량 (ton)", value=33.5)
daily_charge = st.number_input("일일 Charge 수", value=126)
tfe_percent = st.number_input("T.Fe (%)", value=58.0)
daily_production = st.number_input("일일생산량 (ton)", value=12500.0)
reduction_ratio_actual = st.number_input("R.R (풍구앞, kg/T-P)", value=499.4)
carbon_rate_actual = st.number_input("C.R (풍구앞, kg/T-P)", value=338.9)
pcr_actual = st.number_input("PCR (kg/T-P)", value=167.6)
slag_ratio = st.number_input("출선비 (용선:슬래그)", value=2.25)
iron_speed_actual = st.number_input("실측 출선속도 (ton/min)", value=4.80)
air_flow_actual = st.number_input("풍량 (Nm³/min)", value=7189.0)
oxygen_injection_actual = st.number_input("산소부화량 (Nm³/hr)", value=36926.0)

# ⑤ 조업 상태 입력
st.header("⑤ 현재 조업 상태")
status = st.selectbox("조업 상태를 선택하세요", ["정상", "휴풍", "휴풍 후 재송풍", "정전"])

# 풍량 보정
standard_air_flow = 7200
speed_correction = air_flow_actual / standard_air_flow

# 장입량 보정
if status == '휴풍':
    ore_charge_adj = ore_charge * 0.7
elif status == '정전':
    ore_charge_adj = 0
else:
    ore_charge_adj = ore_charge

# 출선속도 계산
k_calibrated = iron_speed_actual / (lead_phi ** 2)
calc_K_lead = k_calibrated
calc_K_follow = k_calibrated

lead_speed_est = calc_K_lead * lead_phi ** 2 * speed_correction
follow_speed_est = calc_K_follow * follow_phi ** 2 * speed_correction
dual_speed_est = lead_speed_est + follow_speed_est

lead_time_est = tap_amount / lead_speed_est
follow_time_est = tap_amount / follow_speed_est
dual_time_est = tap_amount / dual_speed_est

# 종료시각 계산
lead_start_dt = datetime.datetime.combine(datetime.date.today(), lead_start_time)
follow_start_dt = datetime.datetime.combine(datetime.date.today(), follow_start_time)
lead_end_time = lead_start_dt + datetime.timedelta(minutes=lead_time_est)
follow_end_time = follow_start_dt + datetime.timedelta(minutes=150)

# 저선량 계산
total_ore = ore_charge_adj * daily_charge
total_fe_input = total_ore * (tfe_percent / 100)
reduction_ratio_calc = daily_production / total_fe_input if total_fe_input > 0 else 0

slag_amount = daily_production / slag_ratio
furnace_total = daily_production + slag_amount
current_residual_base = furnace_total * 0.05

if status == '정상':
    current_residual = current_residual_base
elif status == '휴풍':
    current_residual = current_residual_base + 10
elif status == '휴풍 후 재송풍':
    current_residual = current_residual_base + 20
elif status == '정전':
    current_residual = current_residual_base + 40

# 저선경보
if current_residual >= 80:
    next_follow_recommend = "⚠ 저선량 심각 → 즉시 후행출선 강력 권장"
elif current_residual >= 60:
    next_follow_recommend = "저선량 과다 → 즉시 후행출선 권장"
else:
    next_follow_recommend = f"선행출선속도 5ton/min 근접시 또는 최소 {wait_time}분 후 진행 권장"

# 용융물 배출상태 평가
if lead_speed_est < 3.5 or current_residual >= 80 or reduction_ratio_calc < 0.75:
    melting_status = "⚠ 용융물 배출 불량 가능성"
elif lead_speed_est < 4.0 or current_residual >= 70:
    melting_status = "주의: 배출상태 점검 필요"
else:
    melting_status = "✅ 용융물 배출 양호"

# 결과 출력
st.header("⑥ 출선 예측 결과")
st.write(f"선행 출선속도: {lead_speed_est:.2f} ton/min (K={calc_K_lead:.5f}, Φ={lead_phi}mm, 풍량보정={speed_correction:.3f}) → 출선시간: {lead_time_est:.1f} 분")
st.write(f"후행 출선속도: {follow_speed_est:.2f} ton/min → 출선시간: {follow_time_est:.1f} 분")
st.write(f"출선 Lap 타임: {dual_time_est:.2f} 분")
st.write(f"선행 종료시각: {lead_end_time.strftime('%H:%M:%S')}")
st.write(f"후행 종료시각: {follow_end_time.strftime('%H:%M:%S')} (150분 고정 기준)")

st.header("⑦ 저선량 및 환원제비 분석")
st.write(f"조업 상태 보정 적용 예상 저선량: {current_residual:.1f} ton (기본:{current_residual_base:.1f} ton, 조업보정:+{current_residual-current_residual_base:.1f} ton)")
st.write(f"예상 용선량: {daily_production:.1f} ton")
st.write(f"예상 슬래그량: {slag_amount:.1f} ton")
st.write(f"계산 환원제비 (R.R): {reduction_ratio_calc:.3f}")
st.write(f"실측 환원제비 (R.R): {reduction_ratio_actual/1000:.3f}")
st.write(f"탄소소비율 (C.R): {carbon_rate_actual/1000:.3f} ton/T-P")
st.write(f"분탄주입율 (PCR): {pcr_actual/1000:.3f} ton/T-P")

st.header("⑧ 용융물 배출상태 평가")
st.write(f"{melting_status} (속도:{lead_speed_est:.2f} ton/min, 저선:{current_residual:.1f} ton, R.R:{reduction_ratio_calc:.3f})")
st.success(next_follow_recommend)

# 누적기록 저장
record = {
    "시각": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "조업상태": status,
    "선행속도": round(lead_speed_est, 2),
    "선행시간": round(lead_time_est, 1),
    "후행속도": round(follow_speed_est, 2),
    "후행시간": round(follow_time_est, 1),
    "저선량": round(current_residual, 1),
    "용선": round(daily_production, 1),
    "슬래그": round(slag_amount, 1),
    "환원제비": round(reduction_ratio_calc, 3),
    "배출상태": melting_status
}
st.session_state['log'].append(record)

# 누적기록 테이블 및 다운로드
st.header("⑨ 누적 조업 기록")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업기록.csv", mime='text/csv')
