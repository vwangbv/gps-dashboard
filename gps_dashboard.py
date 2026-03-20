"""
投资GPS仪表盘 - Final v10.0
修复: 贝叶斯公式 / 去重逻辑 / 输入验证 / 异常处理 / 动态市值显示
作者: Production-Grade Refactor
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import logging

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ==================== 数据类 ====================
@dataclass(frozen=True)
class SignalConfig:
    name: str
    weight: float
    description: str = ""


@dataclass(frozen=True)
class PortfolioConfig:
    name: str
    ticker: str
    weight: float
    description: str = ""


# ==================== 配置中心 ====================
class Config:
    """所有魔法数字/常量集中管理"""

    # 信号配置（权重之和 = 1.00，已验证）
    SIGNALS: Dict[str, SignalConfig] = {
        "油价":    SignalConfig("油价强度",      0.25, "Brent原油强度"),
        "PPI":     SignalConfig("PPI强度",       0.20, "生产者物价指数"),
        "霍尔木兹": SignalConfig("霍尔木兹紧张度", 0.25, "地缘紧张度"),
        "铜价":    SignalConfig("铜价强度",      0.15, "伦敦铜价格"),
        "期货":    SignalConfig("期货曲线强度",   0.15, "期货反向市场"),
    }

    # 投资组合配置
    PORTFOLIO: Dict[str, PortfolioConfig] = {
        "红利": PortfolioConfig("515180 红利ETF", "515180", 0.55, "底仓现金流"),
        "黄金": PortfolioConfig("518850 黄金ETF", "518850", 0.17, "避险对冲"),
        "油气": PortfolioConfig("561360 油气ETF", "561360", 0.28, "进攻弹性"),
    }

    # 默认信号值
    DEFAULT_SIGNALS: Dict[str, int] = {
        "油价": 90, "PPI": 76, "霍尔木兹": 80, "铜价": 70, "期货": 83,
    }

    # ✅ 贝叶斯参数（正确语义化命名）
    # PRIOR:      先验概率 P(A)，即无信号时市场基础胜率
    # LK_WEIGHT:  似然权重，控制信号对先验的「修正力度」
    BAYESIAN_PRIOR: float = 0.65      # 先验：65%基础胜率
    BAYESIAN_LK_WEIGHT: float = 0.75  # 似然权重：信号占75%，先验占25%

    # 退出条件阈值
    EXIT_OIL: int = 70
    EXIT_HORMUZ: int = 65
    EXIT_FUTURES: int = 60
    WARN_OIL: int = 85

    # 市值验证范围
    MV_MIN: float = 0.01
    MV_MAX: float = 100_000.0

    # 持久化路径
    DATA_DIR: Path = Path("data")
    HISTORY_FILE: Path = DATA_DIR / "portfolio_history.csv"

    # 历史数据表列名（单一真相来源）
    HISTORY_COLS: Tuple[str, ...] = (
        "日期", "总市值(万元)", "信号总分", "贝叶斯概率"
    )

    @classmethod
    def validate_weights(cls) -> bool:
        """启动时校验权重是否精确等于1.0"""
        total = sum(s.weight for s in cls.SIGNALS.values())
        if not abs(total - 1.0) < 1e-9:
            logger.error(f"信号权重之和异常: {total:.4f}，应为 1.0")
            return False
        return True


# ==================== 数据管理 ====================
class DataManager:
    """负责所有 IO 操作，带完整异常处理"""

    @staticmethod
    def _empty_df() -> pd.DataFrame:
        return pd.DataFrame(columns=list(Config.HISTORY_COLS))

    @staticmethod
    def ensure_dir() -> None:
        try:
            Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"创建数据目录失败: {e}")
            raise

    @staticmethod
    def load_history() -> pd.DataFrame:
        """加载历史数据；文件不存在或损坏时优雅降级"""
        DataManager.ensure_dir()
        if not Config.HISTORY_FILE.exists():
            logger.info("历史文件不存在，初始化空表")
            return DataManager._empty_df()
        try:
            df = pd.read_csv(Config.HISTORY_FILE)
            df["日期"] = pd.to_datetime(df["日期"])
            # 强制列顺序，防止列缺失
            for col in Config.HISTORY_COLS:
                if col not in df.columns:
                    df[col] = None
            logger.info(f"加载 {len(df)} 条历史记录")
            return df[list(Config.HISTORY_COLS)].sort_values("日期").reset_index(drop=True)
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            st.warning("⚠️ 历史数据文件损坏，已重置为空表")
            return DataManager._empty_df()

    @staticmethod
    def save_history(df: pd.DataFrame) -> bool:
        """持久化保存；返回成功/失败布尔值"""
        try:
            DataManager.ensure_dir()
            df.to_csv(Config.HISTORY_FILE, index=False, encoding="utf-8-sig")
            logger.info(f"已保存 {len(df)} 条记录")
            return True
        except (OSError, PermissionError) as e:
            logger.error(f"保存失败: {e}")
            return False


# ==================== 输入验证 ====================
class InputValidator:
    """独立验证层，职责单一"""

    @staticmethod
    def validate(
        input_date: date,
        input_value: float,
    ) -> Tuple[bool, str]:
        """
        返回 (is_valid, error_message)
        is_valid=True 表示通过
        """
        if input_date > date.today():
            return False, "日期不能晚于今天"
        if input_value < Config.MV_MIN:
            return False, f"总市值不能小于 {Config.MV_MIN} 万元"
        if input_value > Config.MV_MAX:
            return False, f"总市值不能超过 {Config.MV_MAX:,.0f} 万元"
        return True, ""


# ==================== 信号计算器 ====================
class SignalCalculator:

    @staticmethod
    def calculate_total_score(signals: Dict[str, int]) -> float:
        """加权求和，结果范围 [0, 100]"""
        return round(
            sum(signals[k] * Config.SIGNALS[k].weight for k in signals),
            1,
        )

    @staticmethod
    def calculate_bayesian(total_score: float) -> float:
        """
        ✅ 修正后的贝叶斯后验概率
        
        公式（离散贝叶斯更新的线性近似）:
            P_posterior = w_L * L(s) + (1 - w_L) * P_prior
        其中:
            L(s) = total_score / 100   ← 归一化似然
            P_prior = Config.BAYESIAN_PRIOR
            w_L = Config.BAYESIAN_LK_WEIGHT
        
        数学保证:
            total_score=100  → posterior = w_L * 1 + (1-w_L) * P_prior
            total_score=0    → posterior = (1-w_L) * P_prior  (非零但接近0)
            total_score=P_prior*100 → posterior ≈ P_prior (信号无效时回归先验)
        """
        likelihood = total_score / 100.0
        posterior = (
            Config.BAYESIAN_LK_WEIGHT * likelihood
            + (1 - Config.BAYESIAN_LK_WEIGHT) * Config.BAYESIAN_PRIOR
        )
        # 强制约束到 [0, 1]
        posterior = max(0.0, min(1.0, posterior))
        return round(posterior * 100, 1)

    @staticmethod
    def exit_status(signals: Dict[str, int]) -> Tuple[str, str]:
        """返回 (severity, message): severity ∈ {error, warning, success}"""
        if (
            signals["油价"] < Config.EXIT_OIL
            and signals["霍尔木兹"] < Config.EXIT_HORMUZ
            and signals["期货"] < Config.EXIT_FUTURES
        ):
            return "error", "🔴 油气已进入退出窗口 → 建议分批减仓"
        if signals["油价"] < Config.WARN_OIL:
            return "warning", "🟡 油价接近退出阈值，保持关注"
        return "success", "🟢 尚未进入退出窗口"


# ==================== UI 组件 ====================
class UI:
    """纯渲染层，不含业务逻辑"""

    @staticmethod
    def portfolio_overview(history: pd.DataFrame) -> None:
        st.subheader("📊 当前组合资产配置概览")
        # 3 个 ETF + 1 个动态市值 = 4 列
        cols = st.columns(4)
        for i, (_, v) in enumerate(Config.PORTFOLIO.items()):
            with cols[i]:
                st.metric(v.name, f"{int(v.weight * 100)}%", v.description)

        # ✅ 第4列：动态显示最新市值，而非硬编码
        with cols[3]:
            if not history.empty:
                latest = history.iloc[-1]
                ref_date = pd.Timestamp(latest["日期"]).strftime("%m月%d日")
                st.metric(
                    "参考市值",
                    f"{float(latest['总市值(万元)']):.2f} 万元",
                    f"{ref_date} 参考",
                )
            else:
                st.metric("参考市值", "暂无数据", "请先录入")

    @staticmethod
    def signal_sidebar() -> Dict[str, int]:
        """侧边栏信号滑块，返回当前值字典"""
        st.sidebar.header("5大信号实时监测")
        return {
            k: st.sidebar.slider(
                cfg.name,
                min_value=0,
                max_value=100,
                value=Config.DEFAULT_SIGNALS[k],
                help=cfg.description,
                key=f"sig_{k}",
            )
            for k, cfg in Config.SIGNALS.items()
        }

    @staticmethod
    def signal_table(
        signals: Dict[str, int],
        total_score: float,
        bayesian: float,
    ) -> None:
        st.subheader("📡 5大信号实时监测")

        # 构建表格
        df = pd.DataFrame(
            {
                "信号": list(signals.keys()),
                "描述": [Config.SIGNALS[k].description for k in signals],
                "强度评分": list(signals.values()),
                "权重": [
                    f"{int(Config.SIGNALS[k].weight * 100)}%" for k in signals
                ],
            }
        )
        st.dataframe(
            df.style.bar(
                subset=["强度评分"],
                color=["#f46d43", "#a6d96a"],
                vmin=0,
                vmax=100,
            ),
            use_container_width=True,
            hide_index=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            prior_score = Config.BAYESIAN_PRIOR * 100
            st.metric(
                "总信号分",
                f"{total_score} / 100",
                delta=(
                    f"+{total_score - prior_score:.1f} vs 先验"
                    if total_score >= prior_score
                    else f"{total_score - prior_score:.1f} vs 先验"
                ),
            )
        with col2:
            st.metric(
                "贝叶斯后验概率",
                f"{bayesian}%",
                delta=f"{bayesian - Config.BAYESIAN_PRIOR * 100:+.1f}%",
            )

    @staticmethod
    def exit_window(signals: Dict[str, int]) -> None:
        st.subheader("🚪 退出窗口提醒")
        severity, msg = SignalCalculator.exit_status(signals)
        getattr(st, severity)(msg)

    @staticmethod
    def data_input_panel(
        total_score: float,
        bayesian: float,
    ) -> None:
        """历史数据录入面板（含完整验证）"""
        with st.expander("➕ 添加 / 修改历史数据", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                input_date: date = st.date_input(
                    "日期", value=date.today(), key="input_date"
                )
            with col2:
                input_value: float = st.number_input(
                    "总市值（万元）",
                    value=97.14,
                    min_value=Config.MV_MIN,
                    max_value=Config.MV_MAX,
                    format="%.4f",
                    key="input_value",
                )

            if st.button("💾 保存数据", type="primary", key="save_btn"):
                # --- 验证 ---
                ok, err = InputValidator.validate(input_date, input_value)
                if not ok:
                    st.error(f"❌ {err}")
                    return

                try:
                    history: pd.DataFrame = st.session_state.history.copy()

                    # ✅ 正确去重：先显式删除同日期行，再追加新行
                    history = history[
                        history["日期"].dt.date != input_date
                    ]

                    new_row = pd.DataFrame(
                        {
                            "日期": [pd.Timestamp(input_date)],
                            "总市值(万元)": [input_value],
                            "信号总分": [total_score],
                            "贝叶斯概率": [bayesian],
                        }
                    )

                    updated = (
                        pd.concat([history, new_row], ignore_index=True)
                        .sort_values("日期")
                        .reset_index(drop=True)
                    )

                    if DataManager.save_history(updated):
                        st.session_state.history = updated
                        st.success(f"✅ {input_date} 数据已保存")
                        st.rerun()
                    else:
                        st.error("❌ 文件保存失败，请检查磁盘权限")

                except Exception as exc:
                    logger.error(f"保存异常: {exc}", exc_info=True)
                    st.error(f"❌ 保存过程出现异常: {exc}")

    @staticmethod
    def history_chart(history: pd.DataFrame) -> None:
        """渲染趋势图 + 数据表 + 下载按钮"""
        st.subheader("📈 组合市值历史趋势")

        if history.empty:
            st.info("📭 暂无历史数据，请在上方录入")
            return

        try:
            fig = px.line(
                history,
                x="日期",
                y="总市值(万元)",
                title="组合市值历史趋势",
                markers=True,
                template="plotly_white",
                hover_data={
                    "信号总分": ":.1f",
                    "贝叶斯概率": ":.1f",
                    "总市值(万元)": ":.4f",
                },
            )
            fig.update_layout(
                hovermode="x unified",
                height=420,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

            # 格式化表格
            st.dataframe(
                history.style.format(
                    {
                        "总市值(万元)": "{:.4f}",
                        "信号总分": "{:.1f}",
                        "贝叶斯概率": "{:.1f}%",
                    }
                ).background_gradient(
                    subset=["信号总分"],
                    cmap="RdYlGn",
                    vmin=0,
                    vmax=100,
                ),
                use_container_width=True,
                hide_index=True,
            )

            # 统计摘要
            mv = history["总市值(万元)"]
            st.caption(
                f"📊 共 {len(history)} 条记录 ｜ "
                f"最高 {mv.max():.2f} 万 ｜ "
                f"最低 {mv.min():.2f} 万 ｜ "
                f"均值 {mv.mean():.2f} 万 ｜ "
                f"最新 {mv.iloc[-1]:.2f} 万"
            )

            # 下载按钮
            csv_bytes = history.to_csv(index=False, encoding="utf-8-sig").encode(
                "utf-8-sig"
            )
            st.download_button(
                "📥 下载历史数据 (CSV)",
                data=csv_bytes,
                file_name=f"gps_history_{date.today()}.csv",
                mime="text/csv",
                key="download_csv",
            )

        except Exception as exc:
            logger.error(f"图表渲染异常: {exc}", exc_info=True)
            st.error(f"❌ 图表渲染失败: {exc}")


# ==================== 主程序入口 ====================
def main() -> None:
    st.set_page_config(
        page_title="投资GPS仪表盘",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🚀 投资GPS仪表盘 — 实物信用扩张主线")

    # 启动校验
    if not Config.validate_weights():
        st.error("⚠️ 配置错误：信号权重之和不等于1.0，请检查 Config.SIGNALS")
        st.stop()

    # Session State 初始化（只在首次加载时读取文件）
    if "history" not in st.session_state:
        st.session_state.history = DataManager.load_history()

    # ① 读取 Session State 的最新引用（每次都刷新）
    history: pd.DataFrame = st.session_state.history

    # ② 渲染组合概览
    UI.portfolio_overview(history)

    st.divider()

    # ③ 信号输入 & 计算
    signals = UI.signal_sidebar()
    total_score = SignalCalculator.calculate_total_score(signals)
    bayesian = SignalCalculator.calculate_bayesian(total_score)

    # ④ 信号表 & 指标
    UI.signal_table(signals, total_score, bayesian)

    st.divider()

    # ⑤ 退出窗口提醒
    UI.exit_window(signals)

    st.divider()

    # ⑥ 历史数据管理
    UI.data_input_panel(total_score, bayesian)
    UI.history_chart(history)

    st.divider()

    # ⑦ 页脚
    c1, c2, c3 = st.columns(3)
    c1.caption("📊 仪表盘 v10.0 Final")
    c2.caption(f"🕐 {date.today().strftime('%Y-%m-%d')}")
    c3.caption("⚠️ 仅供参考，非投资建议")


if __name__ == "__main__":
    main()
