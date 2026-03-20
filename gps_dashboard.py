import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

# ==================== 历史数据初始化 ====================
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["日期", "总市值(万元)", "信号总分", "贝叶斯概率"])

# ==================== 当前组合概览 ====================
st.subheader("📊 当前组合资产配置概览")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("515180 红利ETF", "55%", "底仓现金流")
with col2:
    st.metric("518850 黄金ETF", "17%", "避险对冲")
with col3:
    st.metric("561360 油气ETF", "28%", "进攻弹性")
with col4:
    st.metric("参考市值", "97.14万元", "3月19日")

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

# ==================== 退出窗口提醒 ====================
st.subheader("🚪 退出窗口提醒")
col_exit1, col_exit2, col_exit3 = st.columns(3)
with col_exit1:
    st.write("**561360 油气**")
    if oil < 70 and hormuz < 65 and futures < 60:
        st.error("已进入退出窗口 → 建议分批减仓")
    else:
        st.success("尚未进入")

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
            # 删除同日期旧数据
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

# 显示历史趋势图
if not st.session_state.history.empty:
    history_sorted = st.session_state.history.sort_values("日期")
    fig = px.line(history_sorted, x="日期", y="总市值(万元)", 
                  title="组合市值历史趋势", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(history_sorted, use_container_width=True)
    st.download_button("📥 下载历史数据CSV", 
                       history_sorted.to_csv(index=False).encode('utf-8'),
                       "gps_history.csv")
else:
    st.info("暂无历史数据，请在上方添加")

st.caption("仪表盘 v9.1 | 已修复历史数据保存问题")