import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

# ==================== 会话状态 ====================
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["日期", "总市值(万元)", "信号总分", "贝叶斯概率"])
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {"红利": 0.55, "黄金": 0.17, "油气": 0.28}

# ==================== 当前组合概览 ====================
st.subheader("📊 当前组合资产配置概览")
cols = st.columns(4)
for i, (name, weight) in enumerate(st.session_state.portfolio.items()):
    with cols[i]:
        st.metric(name + "ETF", f"{int(weight*100)}%", "当前比例")

# ==================== 5大信号 ====================
st.sidebar.header("5大信号实时监测")
oil = st.sidebar.slider("油价强度", 0, 100, 90)
ppi = st.sidebar.slider("PPI强度", 0, 100, 76)
hormuz = st.sidebar.slider("霍尔木兹紧张度", 0, 100, 80)
copper = st.sidebar.slider("铜价强度", 0, 100, 70)
futures = st.sidebar.slider("期货曲线强度", 0, 100, 83)

total_score = round(oil*0.25 + ppi*0.20 + hormuz*0.25 + copper*0.15 + futures*0.15, 1)
bayesian = round(total_score * 0.85 + 80 * 0.15, 1)

# ==================== 5大信号表 ====================
st.subheader("5大信号表")
data = {
    "信号": ["油价", "PPI", "霍尔木兹", "铜价", "期货曲线"],
    "强度评分": [oil, ppi, hormuz, copper, futures],
    "权重": ["25%", "20%", "25%", "15%", "15%"]
}
st.dataframe(pd.DataFrame(data), use_container_width=True)

st.metric("总信号分", f"{total_score} / 100")
st.metric("贝叶斯概率", f"{bayesian}%")

# ==================== 动态比例建议 ====================
st.subheader("🔄 动态比例建议")
if bayesian >= 88:
    suggested = {"红利": 0.52, "黄金": 0.15, "油气": 0.33}
    st.success("信号极强 → 建议增加油气仓位")
elif bayesian >= 82:
    suggested = st.session_state.portfolio
    st.info("信号中强 → 维持当前比例")
else:
    suggested = {"红利": 0.58, "黄金": 0.20, "油气": 0.22}
    st.warning("信号减弱 → 建议减少油气仓位")

if st.button("应用建议比例"):
    st.session_state.portfolio = suggested
    st.success("比例已更新！")
    st.rerun()

# ==================== 退出窗口提醒 ====================
st.subheader("🚪 退出窗口提醒")
if oil < 70 and hormuz < 65 and futures < 60:
    st.error("油气已进入退出窗口 → 建议分批减仓")
else:
    st.success("尚未进入退出窗口")

# ==================== 历史趋势图 & 数据管理 ====================
st.subheader("📈 组合市值历史趋势")
with st.expander("➕ 添加/修改历史数据"):
    col_d, col_v = st.columns(2)
    with col_d:
        input_date = st.date_input("日期", value=date.today())
    with col_v:
        input_value = st.number_input("总市值(万元)", value=97.14, format="%.4f")
    
    if st.button("💾 保存历史数据"):
        try:
            history = st.session_state.history.copy()
            history = history[history["日期"] != str(input_date)]
            new_row = pd.DataFrame({
                "日期": [input_date],
                "总市值(万元)": [input_value],
                "信号总分": [total_score],
                "贝叶斯概率": [bayesian]
            })
            history = pd.concat([history, new_row], ignore_index=True)
            st.session_state.history = history.sort_values("日期")
            st.success(f"{input_date} 数据已保存")
            st.rerun()
        except Exception as e:
            st.error(f"保存失败: {e}")

if not st.session_state.history.empty:
    history_sorted = st.session_state.history.sort_values("日期")
    fig = px.line(history_sorted, x="日期", y="总市值(万元)", title="组合市值历史趋势", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(history_sorted, use_container_width=True)
    st.download_button("📥 下载历史数据CSV", history_sorted.to_csv(index=False).encode('utf-8'), "gps_history.csv")

st.caption("仪表盘 v9.3 | 已修复历史数据保存问题")