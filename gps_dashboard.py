import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

# ==================== 历史数据初始化 ====================
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["日期", "总市值(万元)", "信号总分", "贝叶斯概率"])

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
# （表格代码省略以节省篇幅，保持之前版本即可）

st.metric("总信号分", f"{total_score} / 500")
st.metric("贝叶斯后验概率", f"{bayesian}%")

# ==================== 新增：组合市值历史数据管理 ====================
st.subheader("📈 组合市值历史数据")

# 添加历史数据表单
with st.expander("➕ 添加/修改历史市值数据"):
    col_date, col_value = st.columns(2)
    with col_date:
        input_date = st.date_input("日期", value=date.today())
    with col_value:
        input_value = st.number_input("总市值(万元)", value=97.14, format="%.4f")
    
    if st.button("保存到历史记录"):
        new_row = pd.DataFrame({
            "日期": [input_date],
            "总市值(万元)": [input_value],
            "信号总分": [total_score],
            "贝叶斯概率": [bayesian]
        })
        # 删除同一天旧数据（避免重复）
        st.session_state.history = st.session_state.history[st.session_state.history["日期"] != input_date]
        st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)
        st.success(f"{input_date} 数据已保存！")

# 显示历史数据表格
if not st.session_state.history.empty:
    history_sorted = st.session_state.history.sort_values("日期", ascending=False)
    st.dataframe(history_sorted, use_container_width=True)
    
    # 下载按钮
    st.download_button(
        label="📥 下载历史数据CSV",
        data=history_sorted.to_csv(index=False).encode('utf-8'),
        file_name="投资组合历史数据.csv",
        mime="text/csv"
    )
    
    # 历史趋势图（只显示总市值）
    fig = px.line(history_sorted.sort_values("日期"), 
                  x="日期", y="总市值(万元)",
                  title="组合市值历史趋势",
                  markers=True,
                  line_shape="linear")
    fig.update_layout(xaxis_title="日期", yaxis_title="总市值 (万元)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("暂无历史数据，请点击上方“添加历史数据”按钮")

st.caption("仪表盘 v7.0 | 已加入组合市值历史数据管理 | 可手动回填历史数据")

# 市值更新工具（保持）
st.subheader("今日市值快速更新")
# （保持之前版本的实时计算工具）