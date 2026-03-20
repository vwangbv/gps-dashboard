import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")

# ==================== 当前组合 ====================
st.subheader("📊 当前组合资产配置")
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

st.subheader("5大信号表")
data = {
    "信号": ["油价", "PPI", "霍尔木兹", "铜价", "期货曲线"],
    "强度评分": [oil, ppi, hormuz, copper, futures],
    "权重": ["25%", "20%", "25%", "15%", "15%"]
}
st.dataframe(pd.DataFrame(data), use_container_width=True)

st.metric("总信号分", f"{total_score} / 100")
st.metric("贝叶斯后验概率", f"{bayesian}%")

# ==================== 退出窗口提醒 ====================
st.subheader("🚪 退出窗口提醒")
if oil < 70 and hormuz < 65 and futures < 60:
    st.error("油气已进入退出窗口 → 建议分批减仓")
else:
    st.success("尚未进入退出窗口")

st.caption("仪表盘 v8.0 精简测试版 | 如果正常，请告诉我，我再逐步加回历史趋势图")

# 测试按钮
if st.button("测试按钮"):
    st.balloons()
    st.success("仪表盘正常运行！")import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Dict
import logging

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置类 ====================
@dataclass
class SignalConfig:
    name: str
    weight: float
    description: str = ""

@dataclass
class PortfolioConfig:
    name: str
    ticker: str
    weight: float
    description: str = ""

class Config:
    SIGNALS = {
        "油价": SignalConfig(name="油价强度", weight=0.25, description="Brent原油强度"),
        "PPI": SignalConfig(name="PPI强度", weight=0.20, description="生产者物价指数"),
        "霍尔木兹": SignalConfig(name="霍尔木兹紧张度", weight=0.25, description="地缘紧张度"),
        "铜价": SignalConfig(name="铜价强度", weight=0.15, description="伦敦铜价格"),
        "期货": SignalConfig(name="期货曲线强度", weight=0.15, description="期货反向市场"),
    }
    
    PORTFOLIO = {
        "红利": PortfolioConfig(name="515180 红利ETF", ticker="515180", weight=0.55, description="底仓现金流"),
        "黄金": PortfolioConfig(name="518850 黄金ETF", ticker="518850", weight=0.17, description="避险对冲"),
        "油气": PortfolioConfig(name="561360 油气ETF", ticker="561360", weight=0.28, description="进攻弹性"),
    }
    
    BAYESIAN_PRIOR = 0.80
    BAYESIAN_LIKELIHOOD = 0.85
    DATA_DIR = Path("data")
    HISTORY_FILE = DATA_DIR / "portfolio_history.csv"

# ==================== 数据管理（已修复 .dt 错误） ====================
class DataManager:
    @staticmethod
    def ensure_dir():
        Config.DATA_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def load_history() -> pd.DataFrame:
        try:
            DataManager.ensure_dir()
            if Config.HISTORY_FILE.exists():
                df = pd.read_csv(Config.HISTORY_FILE)
                df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
                df = df.dropna(subset=["日期"])
                return df.sort_values("日期")
            return pd.DataFrame(columns=["日期", "总市值(万元)", "信号总分", "贝叶斯概率"])
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return pd.DataFrame(columns=["日期", "总市值(万元)", "信号总分", "贝叶斯概率"])
    
    @staticmethod
    def save_history(df: pd.DataFrame) -> bool:
        try:
            DataManager.ensure_dir()
            df = df.copy()
            df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
            df = df.dropna(subset=["日期"])
            df = df.sort_values("日期")
            df.to_csv(Config.HISTORY_FILE, index=False)
            return True
        except Exception as e:
            logger.error(f"保存历史数据失败: {e}")
            return False

# ==================== 计算器 ====================
class SignalCalculator:
    @staticmethod
    def calculate_total_score(signals: Dict) -> float:
        return round(sum(signals[k] * Config.SIGNALS[k].weight for k in signals), 1)
    
    @staticmethod
    def calculate_bayesian(total_score: float) -> float:
        return round(total_score * Config.BAYESIAN_LIKELIHOOD + Config.BAYESIAN_PRIOR * 100 * (1 - Config.BAYESIAN_LIKELIHOOD), 1)

# ==================== 主程序 ====================
def main():
    st.set_page_config(page_title="投资GPS仪表盘", layout="wide")
    st.title("🚀 投资GPS仪表盘 - 实物信用扩张主线")
    
    if 'history' not in st.session_state:
        st.session_state.history = DataManager.load_history