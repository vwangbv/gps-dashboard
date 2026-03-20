import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

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

st.sidebar.header("5大信号实时监测")
oil = st.sidebar.slider("油价强度", 0, 100, 90)
ppi = st.sidebar.slider("PPI强度", 0, 100, 76)
hormuz = st.sidebar.slider("霍尔木兹紧张度", 0, 100, 80)
copper = st.sidebar.slider("铜价强度", 0, 100, 70)
futures = st.sidebar.slider("期货曲线强度", 0, 100, 83)

total_score = round(oil*0.25 + ppi*0.20 + hormuz*0.25 + copper*0.15 + futures*0.15, 1)
bayesian = round(total_score * 0.85 + 80 * 0.15, 1)

st.subheader("5大信号表")
data = {
    "信号": ["油价", "PPI", "霍尔木兹", "铜价", "期货曲线"],
    "强度评分": [oil, ppi, hormuz, copper, futures],
    "权重": ["25%", "20%", "25%", "15%", "15%"]
}
st.dataframe(pd.DataFrame(data), use_container_width=True)

st.metric("总信号分", f"{total_score} / 100")
st.metric("贝叶斯概率", f"{bayesian}%")

st.subheader("🚪 退出窗口提醒")
if oil < 70 and hormuz < 65 and futures < 60:
    st.error("油气已进入退出窗口 → 建议分批减仓")
else:
    st.success("尚未进入退出窗口")

st.caption("仪表盘 v8.0 极简测试版")

if st.button("测试按钮"):
    st.balloons()
    st.success("仪表盘正常运行！🎉")