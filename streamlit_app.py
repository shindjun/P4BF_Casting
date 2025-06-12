import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="BlastTap 5.9 Pro 실시간 장입속도 보정판", layout="centered")
st.title("🔥 BlastTap 5.9 Pro 실시간 AI조업 수지추적 (장입속도 실시간 보정판)")

if 'log' not in st.session_state:
    st.session_state['log'] = []

# 장입수지 입력
st.sidebar.header("장입수지 입력")
ore_per_charge = st.sidebar.number_input("Ore 장입량 (ton/ch)", value=165.0)
coke_per_charge = st.sidebar.number_input("Coke 장입량 (ton/ch)", value=33.5)
ore_coke_ratio = st.sidebar.number_input("Ore/Coke 비율", value=5.0)
tfe_percent = st.sidebar.number_input("T.Fe (%)", value=58.0)
slag_ratio = st.sidebar.number_input("Slag비율 (용선:슬래그)", value=2.25)
reduction_efficiency = st.sidebar.number_input("환원율 (기본 1.0)", value=1.0)
ore_size = st.sidebar.number_input("Ore 입도 (mm)", value=20.0)
coke_size = st.sidebar.number_input("Coke 입도 (mm)", value=60.0)
charge_rate = st.sidebar.number_input("장입속도 (charge/h)", value=5.5)
hot_metal_temp = st.sidebar.number_input("용선온도 (°C)", value=1530)
melting_capacity = st.sidebar.number_input("용해능력 (°CKN m²/T-P)", value=2800)

# 시간경과
now = datetime.datetime.now()
today_start = datetime.datetime.combine(datetime.date.today(), datetime.time(0, 0))
elapsed_minutes = (now - today_start).total_seconds() / 60
elapsed_minutes = min(elapsed_minutes, 1440)

# 누적 장입 charge 수 계산
elapsed_charges = charge_rate * (elapsed_minutes / 60)

# 출선실적 입력
st.sidebar.header("출선실적 입력")
completed_taps = st.sidebar.number_input("종료된 TAP수", value=6)
default_tap_amount = st.sidebar.number_input("평균 TAP 출선량 (ton)", value=1215.0)
total_tapped = completed_taps * default_tap_amount

# 현재 진행중 출선 실시간 보정 입력
st.sidebar.header("현재 출선중 TAP 실시간 입력")
lead_speed = st.sidebar.number_input("선행 출선속도 (ton/min)", value=4.8)
lead_elapsed = st.sidebar.number_input("선행 출선경과시간 (분)", value=90)
lead_in_progress = lead_speed * lead_elapsed

follow_speed = st.sidebar.number_input("후행 출선속도 (ton/min)", value=4.8)
follow_elapsed = st.sidebar.number_input("후행 출선경과시간 (분)", value=0)
follow_in_progress = follow_speed * follow_elapsed

current_in_progress_tap = lead_in_progress + follow_in_progress
total_real_tapped = total_tapped + current_in_progress_tap

# 생성량 계산 (실시간 장입속도 반영)
total_ore = ore_per_charge * elapsed_charges
total_fe = total_ore * (tfe_percent / 100)

size_effect = (20 / ore_size + 60 / coke_size) / 2
temp_effect = 1 + (hot_metal_temp - 1500) * 0.0005
melting_effect = 1 + ((melting_capacity - 2500) / 500) * 0.05

reduction_base_coeff = 0.9
reduction_eff_adj = reduction_efficiency * size_effect * temp_effect * melting_effect * reduction_base_coeff

hot_metal = total_fe * reduction_eff_adj
slag = hot_metal / slag_ratio
total_molten = hot_metal + slag

# 저선량 계산
current_residual = max(total_molten - total_real_tapped, 0)
residual_rate = (current_residual / total_molten) * 100

# 결과 출력
st.header("📊 실시간 AI 수지분석 결과")
st.write(f"경과시간: {elapsed_minutes:.1f} 분")
st.write(f"누적 장입 Charge 수: {elapsed_charges:.1f} charge")
st.write(f"누적 생성량: {total_molten:.1f} ton")
st.write(f"종료된 TAP 출선량: {total_tapped:.1f} ton")
st.write(f"출선중 진행량 보정: {current_in_progress_tap:.1f} ton")
st.write(f"누적 총 출선량: {total_real_tapped:.1f} ton")
st.markdown(f"<h3 style='color:orange'>현재 저선량: {current_residual:.1f} ton</h3>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:green'>저선율: {residual_rate:.2f} %</h3>", unsafe_allow_html=True)

if residual_rate >= 9:
    status = "⚠ 저선과다 위험"
    status_color = "red"
elif residual_rate >= 7:
    status = "주의"
    status_color = "orange"
else:
    status = "✅ 정상"
    status_color = "green"
st.markdown(f"<h2 style='color:{status_color}'>{status}</h2>", unsafe_allow_html=True)

# 비트경 추천
if current_residual < 100 and residual_rate < 5:
    tap_diameter = 43
elif current_residual < 150 and residual_rate < 7:
    tap_diameter = 45
else:
    tap_diameter = 48

# 차기 출선간격 추천 (0~20분 반영)
if residual_rate < 5:
    next_tap_interval = "15~20 분"
elif residual_rate < 7:
    next_tap_interval = "10~15 분"
elif residual_rate < 9:
    next_tap_interval = "5~10 분"
else:
    next_tap_interval = "0~5 분 (즉시 출선 권고)"

st.header("🛠️ 조업 자동 추천")
st.write(f"추천 출선비트경: **{tap_diameter} Ø**")
st.write(f"추천 차기 출선간격: **{next_tap_interval}**")

# 실시간 수지추적 그래프 (개선본)
st.header("📊 실시간 수지추적 그래프")
time_labels = [i for i in range(0, int(elapsed_minutes)+1, 60)]
gen_series = [(ore_per_charge * charge_rate * (t/60)) * (tfe_percent/100) * reduction_eff_adj * (1+1/slag_ratio) for t in time_labels]
tap_series = [total_real_tapped] * len(time_labels)
residual_series = [max(g - total_real_tapped, 0) for g in gen_series]

plt.figure(figsize=(10, 6))
plt.plot(time_labels, gen_series, label="누적 생성량 (ton)", linewidth=2)
plt.plot(time_labels, tap_series, label="누적 출선량 (ton)", linestyle="--", linewidth=2)
plt.plot(time_labels, residual_series, label="저선량 (ton)", linestyle=":", linewidth=2)
plt.xlabel("경과시간 (분)", fontsize=12)
plt.ylabel("용융물량 (ton)", fontsize=12)
plt.title("실시간 용융물 수지추적 그래프", fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True)
st.pyplot(plt)

# 기록 저장
record = {
    "시각": now.strftime('%Y-%m-%d %H:%M:%S'),
    "경과시간": elapsed_minutes,
    "누적장입수": elapsed_charges,
    "누적생성량": total_molten,
    "누적출선량": total_real_tapped,
    "저선량": current_residual,
    "저선율": residual_rate,
    "조업상태": status,
    "비트경": tap_diameter,
    "차기출선간격": next_tap_interval
}
st.session_state['log'].append(record)

st.header("📋 누적 조업 리포트")
df = pd.DataFrame(st.session_state['log'])
st.dataframe(df)
csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 CSV 다운로드", data=csv, file_name="조업리포트_5_9_pro.csv", mime='text/csv')
