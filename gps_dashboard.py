import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

# ================== 输入区 ==================
st.sidebar.header("每日更新")
date_today = st.sidebar.date_input("日期", date.today())
current_value = st.sidebar.number_input("今日组合总市值（元）", value=985500, step=1000)

# 5大信号打分
st.sidebar.subheader("5大信号打分")
oil = st.sidebar.slider("油价", 0, 100, 92)
ppi = st.sidebar.slider("PPI", 0, 100, 79)
hormuz = st.sidebar.slider("霍尔木兹", 0, 100, 89)
copper = st.sidebar.slider("铜价", 0, 100, 73)
futures = st.sidebar.slider("期货曲线", 0, 100, 87)

total_score = round(oil*0.25 + ppi*0.20 + hormuz*0.25 + copper*0.15 + futures*0.15, 1)
bayesian = round(total_score * 0.85 + 86 * 0.15, 1)   # 上期概率86

# ================== 主页面 ==================
col1, col2, col3 = st.columns(3)
col1.metric("组合总市值", f"{current_value:,} 元", f"{((current_value-1000000)/1000000*100):+.2f}%")
col2.metric("贝叶斯后验概率", f"{bayesian}%", "实物信用扩张")
col3.metric("5大信号总分", f"{total_score}/100")

# 雷达图
df = pd.DataFrame({"信号": ["油价","PPI","霍尔木兹","铜价","期货曲线"], "分数": [oil,ppi,hormuz,copper,futures]})
fig = px.line_polar(df, r="分数", theta="信号", line_close=True, range_r=[0,100])
st.plotly_chart(fig, use_container_width=True)

# 应然建议
st.subheader("🧭 今日应然建议")
if bayesian >= 85:
    st.success("**信号极强** → 可执行小幅加仓油气（黄金转1%）")
elif bayesian >= 75:
    st.info("**信号较强** → 继续观察，维持当前比例")
else:
    st.warning("**信号偏弱** → 防守优先，观察为主")

st.caption("投资GPS外挂 v6.0 | 5大信号 + 贝叶斯 + 应然建议 | 仅供参考")