import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --- 页面配置 ---
st.set_page_config(page_title="价值锚点计算器 V2.2 (精细策略版)", layout="wide")

st.title("💰 心智升级价值投资锚点计算器 (高精度策略网格)")
st.markdown("核心逻辑：**港股锚点 = (A股锚点 / 汇率) × 港股折扣**。")

# --- 侧边栏：输入参数 ---
with st.sidebar:
    st.header("1. 输入行情数据")
    stock_name = st.text_input("股票名称", value="青岛港")
    
    col_price1, col_price2 = st.columns(2)
    with col_price1:
        current_price_rmb = st.number_input("🅰️ A股股价 (¥)", value=8.66, format="%.2f")
    with col_price2:
        current_price_hk = st.number_input("🇭🇰 港股股价 ($)", value=7.20, format="%.2f")
    
    st.header("2. 输入基本面数据")
    col_fund1, col_fund2 = st.columns(2)
    with col_fund1:
        current_eps = st.number_input("当前EPS (RMB)", value=0.81, format="%.2f")
    with col_fund2:
        dividend_per_share = st.number_input("每股分红 (RMB)", value=0.31, format="%.2f")
    
    st.markdown("---")
    st.write("💱 **汇率设置**")
    exchange_rate = st.number_input(
        "港币汇率 (1 HKD = ? RMB)", 
        value=0.8839, 
        format="%.4f",
        step=0.0001
    )

    st.header("3. 设定增长与折扣")
    growth_rate = st.number_input("未来10年增长率 (%)", value=3.0, step=0.1, format="%.1f") / 100
    
    st.write("⚓ **安全边际折扣**")
    discount_rate_rmb = st.slider("🇨🇳 A股折扣 (%)", 50, 120, 90, 5) / 100
    discount_rate_hk = st.slider("🇭🇰 H股折扣 (%)", 30, 100, 80, 5) / 100
    
    calc_btn = st.button("开始计算", type="primary")

# --- 核心计算逻辑 ---
if calc_btn:
    # 1. 10年利润累积
    total_profit = 0
    for i in range(10):
        year_eps = current_eps * ((1 + growth_rate) ** i)
        total_profit += year_eps
    ten_year_total = total_profit
    
    # 2. 基础锚点计算
    # A股锚点
    anchor_price_rmb = ten_year_total * discount_rate_rmb 
    margin_rmb = (anchor_price_rmb - current_price_rmb) / current_price_rmb 
    
    # H股锚点 (折上折逻辑)
    anchor_price_hk_val = (anchor_price_rmb / exchange_rate) * discount_rate_hk
    margin_hk = (anchor_price_hk_val - current_price_hk) / current_price_hk
    
    # --- 结果展示区 ---
    result_container = st.container()
    
    with result_container:
        # 第一行：大数展示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("10年利润总和 (未折)", f"¥{ten_year_total:.2f}")
        with col2:
            st.metric("🇨🇳 A股锚点", f"¥{anchor_price_rmb:.2f}", delta=f"{margin_rmb:.2%}", delta_color="normal" if margin_rmb > 0 else "inverse")
        with col3:
            st.metric("🇭🇰 港股锚点", f"HK${anchor_price_hk_val:.2f}", delta=f"{margin_hk:.2%}", delta_color="normal" if margin_hk > 0 else "inverse")
            st.caption(f"计算公式：(¥{anchor_price_rmb:.2f} / {exchange_rate}) × {discount_rate_hk*100:.0f}%")

        st.divider()
        
        # --- 🎯 动态分档策略表 (V2.2 新增逻辑) ---
        st.subheader("🎯 分档买入策略表 (高精度网格)")
        
        # 1. 自动生成收益率列表
        # 第一阶段：3.5% 到 12.0%，步长 0.5%
        yields_phase1 = [x / 1000 for x in range(35, 125, 5)] 
        # 第二阶段：13.0% 到 20.0%，步长 1.0%
        yields_phase2 = [x / 100 for x in range(13, 21, 1)]
        
        all_yields = yields_phase1 + yields_phase2
        
        strategy_data = []

        # 2. 遍历并计算每一行
        for target_yield in all_yields:
            # 自动判断区域和仓位建议
            if target_yield <= 0.055:
                zone = "🚫 退出/减仓区"
                position = "卖出"
                action_type = "Sell"
            elif target_yield <= 0.075:
                zone = "😐 平庸/持有区"
                position = "持有"
                action_type = "Hold"
            elif target_yield <= 0.085:
                zone = "👀 观察区"
                position = "5%"
                action_type = "Buy_Small"
            elif target_yield <= 0.100:
                zone = "⚔️ 主战区"
                position = "10%"
                action_type = "Buy_Mid"
            elif target_yield <= 12.0:
                zone = "⚔️ 主战区"
                position = "15%" # 收益率破10%后，仓位加重
                action_type = "Buy_Big"
            else:
                zone = "💰 博弈/捡钱区"
                position = "15%+"
                action_type = "Buy_Super"

            # 核心公式：目标价 = 锚点价 / (收益率 * 10)
            # 含义：锚点本身对应 10% 收益率。
            
            target_price_rmb = anchor_price_rmb / (target_yield * 10)
            dist_rmb = (target_price_rmb - current_price_rmb) / current_price_rmb
            
            target_price_hk = anchor_price_hk_val / (target_yield * 10)
            dist_hk = (target_price_hk - current_price_hk) / current_price_hk
            
            strategy_data.append({
                "区域": zone,
                "期望收益": f"{target_yield:.1%}",
                "A股目标价": target_price_rmb,
                "A股距离": dist_rmb,
                "H股目标价": target_price_hk,
                "H股距离": dist_hk,
                "仓位建议": position,
                "Type": action_type 
            })
            
        df_strategy = pd.DataFrame(strategy_data)

        # 3. 表格样式
        def highlight_row(row):
            action = row["Type"]
            style = [''] * len(row)
            if action == "Buy_Super":
                return ['background-color: #ffcccc; color: black'] * len(row) # 深红
            elif action == "Buy_Big":
                return ['background-color: #ffebcc; color: black'] * len(row) # 橙色
            elif action == "Buy_Mid":
                return ['background-color: #ffffcc; color: black'] * len(row) # 黄色
            elif action == "Buy_Small":
                return ['background-color: #e6f7ff; color: black'] * len(row) # 浅蓝
            elif action == "Sell":
                return ['background-color: #f0f0f0; color: #888888'] * len(row) # 灰色
            return style

        st.dataframe(
            df_strategy.style.apply(highlight_row, axis=1)
            .format({
                "A股目标价": "¥{:.2f}",
                "H股目标价": "HK${:.2f}",
                "A股距离": "{:+.2%}",
                "H股距离": "{:+.2%}"
            })
            .hide(axis="index")
            .hide(subset=["Type"], axis="columns"),
            use_container_width=True,
            height=600 # 增加高度以容纳更多行
        )
        
        st.info("📊 **高精度表格说明**：\n"
                "1. **3.5% - 12.0%**：每 0.5% 一档，覆盖了从减仓到重仓的所有细节。\n"
                "2. **13.0% - 20.0%**：每 1.0% 一档，用于捕捉极端的市场恐慌机会。\n"
                "3. **锚点对齐**：表中 **10.0%** 收益率的价格等于锚点价格。")

else:
    st.info("👈 点击计算，生成高精度策略网格")