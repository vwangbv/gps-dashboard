import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

# ==================== 当前组合资产配置概览 ====================
st.subheader("📊 当前组合资产配置概览")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("515180 红利ETF", "55%", "底仓现金流")
with col2:
    st.metric("518850 黄金ETF", "17%", "避险对冲")
with col3:
    st.metric("561360 油气ETF", "28%", "进攻弹性")
with col4:
    st.metric("总市值", "97.14万元", "3月19日收盘参考")

# ==================== 侧边栏 - 5大信号实时输入 ====================
st.sidebar.header("5大信号实时监测")
oil = st.sidebar.slider("油价强度 (Brent)", 0, 100, 91, help="越高越利好")
ppi = st.sidebar.slider("PPI强度", 0, 100, 78)
hormuz = st.sidebar.slider("霍尔木兹紧张度", 0, 100, 82)
copper = st.sidebar.slider("铜价强度", 0, 100, 72)
futures = st.sidebar.slider("期货曲线强度", 0, 100, 85)

# 计算
total_score = round(oil*0.25 + ppi*0.20 + hormuz*0.25 + copper*0.15 + futures*0.15, 1)
bayesian = round(total_score * 0.85 + 80 * 0.15, 1)

# ==================== 5大信号表 ====================
st.subheader("5大信号表")
data = {
    "信号": ["油价", "PPI", "霍尔木兹", "铜价", "期货曲线"],
    "强度评分": [oil, ppi, hormuz, copper, futures],
    "权重": ["25%", "20%", "25%", "15%", "15%"]
}
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)

st.metric("总信号分", f"{total_score} / 500")
st.metric("贝叶斯后验概率", f"{bayesian}%（实物信用扩张主线）")

# ==================== 应然建议 ====================
st.subheader("应然建议")
if bayesian >= 88:
    st.success("**信号极强** → 可小幅加仓油气（不超过2%）")
elif bayesian >= 82:
    st.info("**信号中强** → 维持当前比例，继续观察")
else:
    st.warning("**信号减弱** → 考虑逐步减仓油气，保护利润")

# ==================== 今日市值更新工具 ====================
st.subheader("今日市值更新工具")
st.caption("输入今天三大标的实际场内涨跌幅，即可实时计算最新市值")
col_a, col_b, col_c = st.columns(3)
with col_a:
    red = st.number_input("515180 今日涨跌幅 (%)", value=-0.5, format="%.2f")
with col_b:
    gold = st.number_input("518850 今日涨跌幅 (%)", value=-1.0, format="%.2f")
with col_c:
    oilgas = st.number_input("561360 今日涨跌幅 (%)", value=0.5, format="%.2f")

if st.button("计算今日市值"):
    prev = 97.1365
    new_value = prev * (1 + red/100*0.55 + gold/100*0.17 + oilgas/100*0.28)
    st.success(f"**今日收盘市值：{new_value:.4f} 万元**")
    st.info(f"单日盈亏：{(new_value - prev):.4f} 万元")

st.caption("仪表盘 v6.2 | 实物信用扩张主线 | 按你的节奏更新")