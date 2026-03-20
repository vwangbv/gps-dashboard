import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线 v9.7【最终优化版】")

# ==================== 配置 & 持久化 ====================
DATA_FILE = Path("history.csv")

def load_history() -> pd.DataFrame:
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
        return df.dropna(subset=["日期"]).sort_values("日期")
    return pd.DataFrame(columns=["日期", "总市值(万元)", "信号总分", "贝叶斯概率"])

def save_history(df: pd.DataFrame):
    df = df.copy()
    df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
    df = df.dropna(subset=["日期"]).sort_values("日期")
    df.to_csv(DATA_FILE, index=False)

# ==================== 会话状态 ====================
if 'history' not in st.session_state:
    st.session_state.history = load_history()
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

@st.cache_data
def calc_score(oil, ppi, hormuz, copper, futures):
    total = round(oil*0.25 + ppi*0.20 + hormuz*0.25 + copper*0.15 + futures*0.15, 1)
    bayesian = round(total * 0.85 + 80 * 0.15, 1)
    return total, bayesian

total_score, bayesian = calc_score(oil, ppi, hormuz, copper, futures)

# ==================== 信号表 ====================
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

# ==================== 历史数据管理（最终优化） ====================
st.subheader("📈 组合市值历史趋势")

if not st.session_state.history.empty:
    st.write("**点击单元格直接编辑**（日期、市值等均可改）")
    edited_df = st.data_editor(
        st.session_state.history,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="history_editor",
        column_config={
            "日期": st.column_config.DateColumn("日期", format="YYYY-MM-DD"),
            "总市值(万元)": st.column_config.NumberColumn("总市值(万元)", format="%.4f"),
        }
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 应用表格修改"):
            save_history(edited_df)
            st.session_state.history = edited_df
            st.success("已保存到磁盘")
            st.rerun()
    with col2:
        if st.button("🗑️ 删除选中行"):
            save_history(edited_df)
            st.session_state.history = edited_df
            st.success("选中行已删除")
            st.rerun()

# ==================== 添加/覆盖数据（使用 form 优化） ====================
with st.expander("➕ 添加或覆盖历史数据"):
    with st.form("add_form"):
        col_d, col_v = st.columns(2)
        with col_d:
            input_date = st.date_input("日期", value=date.today())
        with col_v:
            input_value = st.number_input("总市值(万元)", value=95.7263, min_value=0.0, format="%.4f")
        
        submitted = st.form_submit_button("添加/覆盖该日期")
        if submitted:
            try:
                new_row = pd.DataFrame({
                    "日期": [pd.to_datetime(input_date)],
                    "总市值(万元)": [input_value],
                    "信号总分": [total_score],
                    "贝叶斯概率": [bayesian]
                })
                history = st.session_state.history.copy()
                history["日期"] = pd.to_datetime(history["日期"], errors='coerce')
                history = history[history["日期"].dt.date != input_date]
                history = pd.concat([history, new_row], ignore_index=True).sort_values("日期")
                save_history(history)
                st.session_state.history = history
                st.success(f"{input_date} 已覆盖/添加")
                st.rerun()
            except Exception as e:
                st.error(f"保存失败: {str(e)}")

# ==================== 趋势图 ====================
if not st.session_state.history.empty:
    fig = px.line(st.session_state.history.sort_values("日期"), x="日期", y="总市值(万元)",
                  title="组合市值历史趋势", markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.caption("仪表盘 v9.7 | CSV持久化 + data_editor 美化 + form 优化 + 删除更友好")