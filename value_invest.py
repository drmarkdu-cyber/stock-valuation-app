import streamlit as st
import pandas as pd
import numpy as np

# --- 页面配置 ---
st.set_page_config(page_title="价值锚点计算器 V2.8.1 (完美修复版)", layout="wide")

# --- CSS 样式注入 (核心排版引擎) ---
st.markdown("""
<style>
    /* 1. 指标卡片样式 */
    .metric-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .metric-label {
        font-size: 16px;
        font-weight: 600;
        color: #444;
    }
    
    .formula-tag {
        font-size: 13px;
        color: #666;
        background-color: #e2e6ea;
        padding: 4px 8px;
        border-radius: 6px;
        font-family: monospace;
    }
    
    .metric-body {
        display: flex;
        align-items: baseline;
        gap: 15px;
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: 800;
        color: #212529;
        line-height: 1;
    }
    
    .metric-delta {
        font-size: 20px;
        font-weight: 600;
    }
    .up { color: #28a745; }
    .down { color: #dc3545; }

    /* 2. 策略表格样式 */
    .strategy-table {
        width: 100%;
        border-collapse: collapse; 
        margin-top: 10px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .strategy-table th {
        background-color: #f1f3f5;
        color: #333;
        font-weight: bold;
        font-size: 20px !important;
        text-align: center !important;
        padding: 15px;
        border: 1px solid #dee2e6;
    }
    
    .strategy-table td {
        font-size: 18px !important;
        text-align: center !important;
        padding: 12px;
        border: 1px solid #dee2e6;
        vertical-align: middle;
    }
    
    /* 区域颜色类 */
    .bg-super { background-color: #ffc9c9 !important; color: #000; font-weight: bold; }
    .bg-big { background-color: #ffe8cc !important; color: #000; font-weight: bold; }
    .bg-mid { background-color: #fff9db !important; color: #000; font-weight: bold; }
    .bg-small { background-color: #e7f5ff !important; color: #000; }
    .bg-hold { background-color: #ffffff !important; color: #333; }
    .bg-sell { background-color: #e9ecef !important; color: #868e96; }
    
    /* 3. 锚点行高亮样式 (红框) */
    .anchor-row td {
        border-top: 3px solid #ff4b4b !important;
        border-bottom: 3px solid #ff4b4b !important;
        color: #d63384 !important;
        font-weight: 900 !important;
    }
    .anchor-row td:first-child {
        border-left: 3px solid #ff4b4b !important;
    }
    .anchor-row td:last-child {
        border-right: 3px solid #ff4b4b !important;
    }

</style>
""", unsafe_allow_html=True)

st.title("💰 心智升级价值投资锚点计算器 (高精度策略) -核心逻辑：买股票就是买公司，以10年预期净利润作为评估公司价值的关键基准。根据“性价比”（预期收益率）分档建仓，越便宜（预期收益率越高），买得越多（主战区、博弈区）；越贵（预期收益率越低），越要减仓（退出区）。本模型只适合当前已明确盈利的成长股或红利股，不适合尚未盈利的公司")

# --- 侧边栏：输入参数 ---
with st.sidebar:
    st.header("1. 输入行情数据")
    
    # 【修复点】找回了消失的股票名称字段
    stock_name = st.text_input("股票名称", value="青岛港")
    
    col_price1, col_price2 = st.columns(2)
    with col_price1:
        current_price_rmb = st.number_input("🅰️ A股股价 (¥)", value=8.66, format="%.2f")
    with col_price2:
        current_price_hk = st.number_input("🇭🇰 港股股价 ($)", value=7.20, format="%.2f")
    
    st.header("2. 输入基本面数据")
    col_fund1, col_fund2 = st.columns(2)
    with col_fund1:
        current_eps = st.number_input("当前每股净利润 (¥)", value=0.81, format="%.2f")
    with col_fund2:
        dividend_per_share = st.number_input("每股分红 (¥)", value=0.31, format="%.2f")
    
    st.markdown("---")
    st.write("💱 **汇率设置**")
    exchange_rate = st.number_input(
        "港币汇率 (1 HKD = ? RMB)", value=0.8839, format="%.4f", step=0.0001
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
    anchor_price_rmb = ten_year_total * discount_rate_rmb 
    margin_rmb = (anchor_price_rmb - current_price_rmb) / current_price_rmb 
    
    # H股锚点
    anchor_price_hk_val = (anchor_price_rmb / exchange_rate) * discount_rate_hk
    margin_hk = (anchor_price_hk_val - current_price_hk) / current_price_hk
    
    # --- 结果展示区 (HTML 渲染) ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-header">
                <span class="metric-label">预计10年每股利润总和 (未折，2024-2033)</span>
            </div>
            <div class="metric-body">
                <span class="metric-value">¥{ten_year_total:.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        cls_rmb = "up" if margin_rmb > 0 else "down"
        arrow_rmb = "↑" if margin_rmb > 0 else "↓"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-header">
                <span class="metric-label">🇨🇳 A股锚点</span>
            </div>
            <div class="metric-body">
                <span class="metric-value">¥{anchor_price_rmb:.2f}</span>
                <span class="metric-delta {cls_rmb}">{arrow_rmb} {margin_rmb:.2%}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        cls_hk = "up" if margin_hk > 0 else "down"
        arrow_hk = "↑" if margin_hk > 0 else "↓"
        formula = f"(¥{anchor_price_rmb:.2f} / {exchange_rate}) × {discount_rate_hk*100:.0f}%"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-header">
                <span class="metric-label">🇭🇰 港股锚点</span>
                <span class="formula-tag">{formula}</span>
            </div>
            <div class="metric-body">
                <span class="metric-value">HK${anchor_price_hk_val:.2f}</span>
                <span class="metric-delta {cls_hk}">{arrow_hk} {margin_hk:.2%}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # --- 🎯 动态分档策略表 (HTML 生成) ---
    st.subheader(f"🎯 分档买入策略表 - {stock_name}") # 这里也把股票名字加上去了
    
    # 1. 生成数据
    yields = [x / 1000 for x in range(40, 125, 5)] + [x / 100 for x in range(13, 21, 1)]
    
    # 2. 构建 HTML 表格字符串
    html_table = """<table class="strategy-table">
<thead>
<tr>
<th>区域</th>
<th>期望收益率</th>
<th>A股目标价</th>
<th>A股目标距离</th>
<th>H股目标价</th>
<th>H股目标距离</th>
<th>仓位建议</th>
</tr>
</thead>
<tbody>"""

    for y in yields:
        # 逻辑判断
        css_class = ""
        position = ""
        zone = ""
        
        # 判断 10.0% 锚点行
        is_anchor_row = abs(y - 0.100) < 0.0001
        
        if y < 0.041:
            zone = "🚫 减仓区"
            position = "卖出10%"
            css_class = "bg-sell"
        elif y < 0.056:
            zone = "🚫 减仓区"
            position = "卖出30%"
            css_class = "bg-sell"
        elif y <= 0.075:
            zone = "😐 持有区"
            position = "持有"
            css_class = "bg-hold"
        elif y <= 0.085:
            zone = "👀 观察区"
            position = "买入5%"
            css_class = "bg-small"
        elif y <= 0.100:
            zone = "⚔️ 主战区"
            if is_anchor_row:
                position = "买入15%"
            else:
                position = "买入10%"
            css_class = "bg-mid"
        elif y <= 0.120:
            zone = "⚔️ 主战区"
            position = "买入15%"
            css_class = "bg-big"
        else:
            zone = "💰 捡钱区"
            position = "买入15%+"
            css_class = "bg-super"

        # 锚点行特殊处理
        if is_anchor_row:
            css_class += " anchor-row"
            zone += " (锚点)"

        # 计算数值
        t_rmb = anchor_price_rmb / (y * 10)
        d_rmb = (t_rmb - current_price_rmb) / current_price_rmb
        t_hk = anchor_price_hk_val / (y * 10)
        d_hk = (t_hk - current_price_hk) / current_price_hk

        html_table += f"""<tr class="{css_class}">
<td>{zone}</td>
<td>{y:.1%}</td>
<td>¥{t_rmb:.2f}</td>
<td>{d_rmb:+.2%}</td>
<td>HK${t_hk:.2f}</td>
<td>{d_hk:+.2%}</td>
<td>{position}</td>
</tr>"""

    html_table += "</tbody></table>"
    
    # 3. 渲染表格
    st.markdown(html_table, unsafe_allow_html=True)
    st.caption("注：红色框选行代表 10.0% 收益率基准（锚点价格），此处建议加重仓位。")

else:
    st.info("👈 点击计算，生成最新策略表")