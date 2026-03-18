import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

# ================== 历史记录（自动保存） ==================
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["日期", "总市值", "累计回报"])

# ================== 侧边栏输入 ==================
st.sidebar.header("每日更新")
date_today = st.sidebar.date_input("日期", date.today())
current_value = st.sidebar.number_input("今日组合总市值（元）", value=982300, step=1000)

# 5大信号打分
st.sidebar.subheader("5大信号打分")
oil = st.sidebar.slider("油价信号", 0, 100, 93)
ppi = st.sidebar.slider("PPI信号", 0, 100, 79)
hormuz = st.sidebar.slider("霍尔木兹信号", 0, 100, 84)
copper = st.sidebar.slider("铜价信号", 0, 100, 69)
futures = st.sidebar.slider("期货曲线信号", 0, 100, 87)

total_score = round(oil*0.25 + ppi*0.20 + hormuz*0.25 + copper*0.15 + futures*0.15, 1)
bayesian = round(total_score * 0.85 + 86 * 0.15, 1)

# ================== 计算 ==================
total_return = round((current_value - 1000000) / 1000000 * 100, 2)

# 添加到历史记录
new_row = pd.DataFrame({"日期": [date_today], "总市值": [current_value], "累计回报": [total_return]})
st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)

# ================== 主页面展示 ==================
col1, col2, col3 = st.columns(3)
col1.metric("组合总市值", f"{current_value:,} 元", f"{total_return:+.2f}%")
col2.metric("贝叶斯后验概率", f"{bayesian}%", "实物信用扩张")
col3.metric("5大信号总分", f"{total_score}/100")

# 历史曲线图
if not st.session_state.history.empty:
    fig = px.line(st.session_state.history, x="日期", y="总市值", 
                  title="组合市值历史走势", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# 历史记录表
st.subheader("📈 历史记录")
st.dataframe(st.session_state.history.sort_values("日期", ascending=False), use_container_width=True)

# 应然建议
st.subheader("🧭 今日应然建议")
if bayesian >= 85:
    st.success("**信号极强** → 可执行小幅加仓油气")
elif bayesian >= 75:
    st.info("**信号较强** → 继续观察，维持当前比例")
else:
    st.warning("**信号偏弱** → 防守优先")

st.caption("投资GPS外挂 v6.0 | 历史曲线已添加 | 每天填数据即可自动记录")