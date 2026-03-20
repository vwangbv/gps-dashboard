"""
投资GPS仪表盘 v11.0
生产级最终版
优化方向：结构模块化 + 注释规范 + UI 分页 + 完整历史管理
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from pathlib import Path

# ====================== 配置区 ======================
st.set_page_config(page_title="投资GPS仪表盘", layout="wide")

class Config:
    """全局配置（所有常量集中管理，便于维护）"""
    APP_TITLE = "🚀 投资GPS仪表盘 - 实物信用扩张主线 v11.0"
    START_DATE = datetime(2026, 3, 16).date()
    INITIAL_VALUE = 100.0
    DATA_FILE = Path("history.csv")


# ====================== 工具函数 ======================
def load_history() -> pd.DataFrame:
    """从CSV加载历史数据（日期安全处理）"""
    if Config.DATA_FILE.exists():
        df = pd.read_csv(Config.DATA_FILE)
        df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
        return df.dropna(subset=["日期"]).sort_values("日期")
    return pd.DataFrame(columns=["日期", "总市值(万元)", "信号总分", "贝叶斯概率"])


def save_history(df: pd.DataFrame):
    """保存历史数据到CSV"""
    df = df.copy()
    df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
    df = df.dropna(subset=["日期"]).sort_values("日期")
    df.to_csv(Config.DATA_FILE, index=False)


@st.cache_data
def calc_score(oil: int, ppi: int, hormuz: int, copper: int, futures: int) -> tuple[float, float]:
    """计算总信号分和贝叶斯概率"""
    total = round(oil*0.25 + ppi*0.20 + hormuz*0.25 + copper*0.15 + futures*0.15, 1)
    bayesian = round(total * 0.85 + 80 * 0.15, 1)
    return total, bayesian


def get_holding_metrics(history: pd.DataFrame) -> tuple[int, float, float, str]:
    """计算持有期回报（包含买入当日）"""
    if history.empty:
        return 0, 0.0, 0.0, "尚未添加数据"
    current_value = history["总市值(万元)"].iloc[-1]
    today = date.today()
    holding_days = (today - Config.START_DATE).days + 1
    cum_return = (current_value - Config.INITIAL_VALUE) / Config.INITIAL_VALUE * 100
    ann_return = (cum_return / holding_days * 252) if holding_days > 0 else 0
    return holding_days, round(cum_return, 2), round(ann_return, 2), f"当前市值 {current_value:.4f}万元"


# ====================== 会话状态 ======================
if 'history' not in st.session_state:
    st.session_state.history = load_history()
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {"红利": 0.55, "黄金": 0.17, "油气": 0.28}

# ====================== 主界面 ======================
st.title(Config.APP_TITLE)

# Tab 分页（更专业）
tab1, tab2, tab3 = st.tabs(["📊 组合概览", "📈 历史趋势", "⚙️ 数据管理"])

with tab1:
    # 当前组合概览
    st.subheader("📊 当前组合资产配置概览")
    cols = st.columns(4)
    for i, (name, weight) in enumerate(st.session_state.portfolio.items()):
        with cols[i]:
            st.metric(name + "ETF", f"{int(weight*100)}%", "当前比例")

    # 持有期回报
    holding_days, cum_return, ann_return, current_note = get_holding_metrics(st.session_state.history)
    st.subheader("📅 持有期回报")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("持有天数", f"{holding_days} 天", "自2026-03-16买入（含买入日）")
    with col2:
        st.metric("累计回报", f"{cum_return}%", current_note)
   

    # 5大信号
    st.subheader("5大信号表")
    oil = st.sidebar.slider("油价强度", 0, 100, 90)
    ppi = st.sidebar.slider("PPI强度", 0, 100, 76)
    hormuz = st.sidebar.slider("霍尔木兹紧张度", 0, 100, 80)
    copper = st.sidebar.slider("铜价强度", 0, 100, 70)
    futures = st.sidebar.slider("期货曲线强度", 0, 100, 83)

    total_score, bayesian = calc_score(oil, ppi, hormuz, copper, futures)
    data = {
        "信号": ["油价", "PPI", "霍尔木兹", "铜价", "期货曲线"],
        "强度评分": [oil, ppi, hormuz, copper, futures],
        "权重": ["25%", "20%", "25%", "15%", "15%"]
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True)
    st.metric("总信号分", f"{total_score} / 100")
    st.metric("贝叶斯概率", f"{bayesian}%")

with tab2:
    # 趋势图
    if not st.session_state.history.empty:
        fig = px.line(st.session_state.history.sort_values("日期"), x="日期", y="总市值(万元)",
                      title="组合市值历史趋势", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无历史数据，请在「数据管理」页添加")

with tab3:
    # 历史数据管理
    st.subheader("📈 历史数据管理")
    st.info("**删除操作**：表格左侧勾选 → 右上角 🗑️ 删除 → 点击下方保存按钮")

    if not st.session_state.history.empty:
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
        
        if st.button("💾 保存所有修改"):
            save_history(edited_df)
            st.session_state.history = edited_df
            st.success("✅ 已保存")
            st.rerun()
    else:
        st.info("暂无历史数据")

    # 添加/覆盖
    with st.expander("➕ 添加或覆盖历史数据"):
        with st.form("add_form"):
            col_d, col_v = st.columns(2)
            with col_d:
                input_date = st.date_input("日期", value=date.today())
            with col_v:
                input_value = st.number_input("总市值(万元)", value=95.7263, min_value=0.0, format="%.4f")
            if st.form_submit_button("添加/覆盖该日期"):
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

st.caption("仪表盘 v11.0 | 结构与注释全面优化完成")