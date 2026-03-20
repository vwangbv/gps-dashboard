import streamlit as st
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