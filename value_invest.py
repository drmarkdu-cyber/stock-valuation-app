import streamlit as st
import pandas as pd
import numpy as np

# --- 页面配置 ---
st.set_page_config(page_title="价值锚点计算器 V3.5 (三段式增长版)", layout="wide")

# --- CSS 样式注入 ---
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
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .metric-label {
        font-size: 16px;
        font-weight: 600;
        color: #444;
    }
    
    .formula-tag {
        font-size: 12px;
        color: #666;
        background-color: #e2e6ea;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: monospace;
    }
    
    .metric-body {
        display: flex;
        align-items: baseline;
        gap: 10px;
        margin-bottom: 5px;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #212529;
        line-height: 1;
    }
    
    .metric-delta {
        font-size: 18px;
        font-weight: 600;
    }
    .up { color: #28a745; }
    .down { color: #dc3545; }
    
    /* 2. 收益率标签样式 */
    .yield-container {
        display: flex;
        flex-direction: column;
        gap: 5px;
        margin-top: 8px;
    }

    .yield-row {
        font-size: 13px;
        font-weight: 500;
        color: #555;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        flex-wrap: wrap; 
    }

    .yield-badge-purple {
        background-color: #f3d9fa;
        color: #5f3dc4;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
        margin-left: 8px;
        font-size: 13px;
    }

    .yield-badge-green {
        background-color: #d3f9d8;
        color: #2b8a3e;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
        margin-left: 8px;
        font-size: 13px;
    }
    
    .tax-note {
        font-size: 11px;
        color: #999;
        margin-left: 5px;
    }

    /* 3. 策略表格样式 */
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
    
    /* 锚点行高亮 */
    .anchor-row td {
        border-top: 3px solid #ff4b4b !important;
        border-bottom: 3px solid #ff4b4b !important;
        color: #d63384 !important;
        font-weight: 900 !important;
    }
    .anchor-row td:first-child { border-left: 3px solid #ff4b4b !important; }
    .anchor-row td:last-child { border-right: 3px solid #ff4b4b !important; }

</style>
""", unsafe_allow_html=True)

# --- 预设公司数据 (基于2024年报/预告整理) ---
COMPANY_DB = {
    "自定义": {"eps": 0.0, "div": 0.0, "market": "A+H股"},
    "青岛港": {"eps": 0.81, "div": 0.3141, "market": "A+H股"},
    "格力电器": {"eps": 2.60, "div": 2.997, "market": "仅A股"},
    "国投电力": {"eps": 0.8669, "div": 0.4565, "market": "仅A股"},
    "海尔智家": {"eps": 2.02, "div": 0.965, "market": "仅A股"},
    "贵州茅台": {"eps": 68.64, "div": 51.555, "market": "仅A股"},
    "上港集团": {"eps": 0.64, "div": 0.195, "market": "仅A股"},
    "中国移动": {"eps": 6.45, "div": 4.671, "market": "A+H股"},
}

# --- Session State 初始化 ---
if 'selected_company' not in st.session_state:
    st.session_state.selected_company = "青岛港"
if 'form_eps' not in st.session_state:
    st.session_state.form_eps = COMPANY_DB["青岛港"]["eps"]
if 'form_div' not in st.session_state:
    st.session_state.form_div = COMPANY_DB["青岛港"]["div"]
if 'form_market' not in st.session_state:
    st.session_state.form_market = COMPANY_DB["青岛港"]["market"]
if 'form_name' not in st.session_state:
    st.session_state.form_name = "青岛港"

# 回调函数
def update_company_data():
    selected = st.session_state.company_selector
    if selected != "自定义":
        data = COMPANY_DB[selected]
        st.session_state.form_name = selected
        st.session_state.form_eps = data["eps"]
        st.session_state.form_div = data["div"]
        st.session_state.form_market = data["market"]

# --- 标题与核心说明区 ---
st.title("💰 心智升级价值投资锚点计算器 1.0")

st.markdown("""
<div style="background-color: #f1f3f5; padding: 15px; border-radius: 8px; font-size: 14px; color: #495057; line-height: 1.6; border-left: 5px solid #0068c9; margin-bottom: 25px;">
    <strong>核心逻辑：</strong>买股票就是买公司，以10年预期净利润作为评估公司价值的关键基准。根据“性价比”（预期收益率）分档建仓：
    <ul style="margin-top: 5px; margin-bottom: 5px; padding-left: 20px;">
        <li>越便宜（预期收益率越高），买得越多（主战区、博弈区）；</li>
        <li>越贵（预期收益率越低），越要减仓（退出区）。</li>
    </ul>
    <span style="color: #d63384; font-weight: 500;">* 本模型只适合当前已明确盈利的成长股或红利股，不适合尚未盈利的公司。</span>
</div>
""", unsafe_allow_html=True)

# --- 侧边栏：输入参数 ---
with st.sidebar:
    # 快速选择模块
    st.header("⚡ 快速选择公司")
    st.selectbox(
        "选择常见公司 (自动填入基本面)",
        options=list(COMPANY_DB.keys()),
        index=1,
        key="company_selector",
        on_change=update_company_data
    )
    
    st.markdown("---")
    st.header("1. 输入行情数据")
    
    market_type = st.radio(
        "上市类型", 
        ["A+H股", "仅A股", "仅港股"], 
        horizontal=True,
        key="form_market"
    )
    
    stock_name = st.text_input("股票名称", key="form_name")
    
    col_price1, col_price2 = st.columns(2)
    current_price_rmb = 0.0
    current_price_hk = 0.0
    
    if market_type in ["A+H股", "仅A股"]:
        with col_price1:
            current_price_rmb = st.number_input("🅰️ A股股价 (¥)", value=8.66, format="%.2f")
    
    if market_type in ["A+H股", "仅港股"]:
        with col_price2:
            current_price_hk = st.number_input("🇭🇰 港股股价 ($)", value=7.20, format="%.2f")
    
    st.header("2. 输入基本面数据")
    col_fund1, col_fund2 = st.columns(2)
    with col_fund1:
        current_eps = st.number_input(
            "当前每股净利润 (¥)", 
            format="%.4f", 
            step=0.0001,
            key="form_eps"
        )
    with col_fund2:
        current_dividend = st.number_input(
            "当前股息 (¥)", 
            format="%.4f", 
            step=0.0001,
            help="请输入每股年度分红总额 (税前)",
            key="form_div"
        )
    
    exchange_rate = 1.0
    if market_type != "仅A股": 
        st.markdown("---")
        st.write("💱 **汇率设置**")
        exchange_rate = st.number_input(
            "港币汇率 (1 HKD = ? RMB)", value=0.8839, format="%.4f", step=0.0001
        )

    st.header("3. 设定未来增长 (三段式)")
    
    # 【核心修改】将原来的一个输入框拆分为三个
    col_g1, col_g2, col_g3 = st.columns(3)
    
    with col_g1:
        g1 = st.number_input("第1年增长 (%)", value=5.0, step=0.5, format="%.1f") / 100
    with col_g2:
        g2 = st.number_input("第2年增长 (%)", value=4.0, step=0.5, format="%.1f") / 100
    with col_g3:
        g3_10 = st.number_input("3-10年增长 (%)", value=3.0, step=0.5, format="%.1f") / 100
    
    st.write("⚓ **安全边际折扣**")
    
    discount_rate_rmb = 0.9
    discount_rate_hk = 0.8
    
    if market_type in ["A+H股", "仅A股"]:
        discount_rate_rmb = st.slider("🇨🇳 A股折扣 (%)", 50, 120, 90, 5) / 100
        
    if market_type in ["A+H股", "仅港股"]:
        discount_rate_hk = st.slider("🇭🇰 H股折扣 (%)", 30, 100, 80, 5) / 100
    
    calc_btn = st.button("开始计算", type="primary")

    st.markdown("---")
    st.caption("Designed by **Dr.Du**")

# --- 核心计算逻辑 ---
if calc_btn:
    # 1. 10年利润累积 (三段式算法)
    total_profit = 0
    
    # 初始化
    year_eps = current_eps
    
    # 第1年
    year_eps = current_eps * (1 + g1)
    total_profit += year_eps
    
    # 第2年
    year_eps = year_eps * (1 + g2)
    total_profit += year_eps
    
    # 第3-10年 (循环8次)
    for i in range(8):
        year_eps = year_eps * (1 + g3_10)
        total_profit += year_eps
        
    ten_year_total = total_profit
    
    # 2. 锚点与收益率计算
    
    # --- A股 ---
    anchor_price_rmb = 0
    margin_rmb = 0
    expected_yield_rmb = 0
    dividend_yield_rmb = 0
    
    if market_type in ["A+H股", "仅A股"]:
        anchor_price_rmb = ten_year_total * discount_rate_rmb 
        if current_price_rmb > 0:
            margin_rmb = (anchor_price_rmb - current_price_rmb) / current_price_rmb 
            expected_yield_rmb = (anchor_price_rmb / current_price_rmb) / 10
            dividend_yield_rmb = current_dividend / current_price_rmb
    
    # --- 港股 ---
    anchor_price_hk_val = 0
    margin_hk = 0
    expected_yield_hk = 0
    dividend_yield_hk = 0
    
    if market_type in ["A+H股", "仅港股"]:
        profit_in_hkd_base = 0
        if market_type == "A+H股":
            profit_in_hkd_base = anchor_price_rmb / exchange_rate
        else:
            profit_in_hkd_base = ten_year_total / exchange_rate
            
        anchor_price_hk_val = profit_in_hkd_base * discount_rate_hk
        
        if current_price_hk > 0 and exchange_rate > 0:
            margin_hk = (anchor_price_hk_val - current_price_hk) / current_price_hk
            expected_yield_hk = (anchor_price_hk_val / current_price_hk) / 10
            
            # 【港股通税后股息率】
            raw_dividend_yield = current_dividend / (current_price_hk * exchange_rate)
            dividend_yield_hk = raw_dividend_yield * 0.8
    
    # --- 结果展示区 ---
    cols_to_show = [True] 
    if market_type == "A+H股":
        cols_to_show += [True, True]
    elif market_type == "仅A股":
        cols_to_show += [True, False]
    elif market_type == "仅港股":
        cols_to_show += [False, True]
        
    visible_cols = [c for c in cols_to_show if c]
    cols = st.columns(len(visible_cols))
    col_idx = 0
    
    # Col 1: 总利润
    with cols[col_idx]:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-header">
                <span class="metric-label">预计10年每股利润总和 (未折)</span>
            </div>
            <div class="metric-body">
                <span class="metric-value">¥{ten_year_total:.2f}</span>
            </div>
            <div class="yield-container" style="visibility: hidden;">
                 <div class="yield-row">占位</div>
                 <div class="yield-row">占位</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    col_idx += 1

    # Col 2: A股锚点
    if market_type in ["A+H股", "仅A股"]:
        with cols[col_idx]:
            cls_rmb = "up" if margin_rmb > 0 else "down"
            arrow_rmb = "↑" if margin_rmb > 0 else "↓"
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-header">
                    <span class="metric-label">🇨🇳 A股锚点</span>
                </div>
                <div>
                    <div class="metric-body">
                        <span class="metric-value">¥{anchor_price_rmb:.2f}</span>
                        <span class="metric-delta {cls_rmb}">{arrow_rmb} {margin_rmb:.2%}</span>
                    </div>
                    <div class="yield-container">
                        <div class="yield-row">
                            当前预期收益: <span class="yield-badge-purple">{expected_yield_rmb:.2%}</span>
                        </div>
                        <div class="yield-row">
                            当前股息率: <span class="yield-badge-green">{dividend_yield_rmb:.2%}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        col_idx += 1

    # Col 3: 港股锚点
    if market_type in ["A+H股", "仅港股"]:
        with cols[col_idx]:
            cls_hk = "up" if margin_hk > 0 else "down"
            arrow_hk = "↑" if margin_hk > 0 else "↓"
            
            if market_type == "A+H股":
                formula = f"(A股锚点 / 汇率) × {discount_rate_hk*100:.0f}%"
            else:
                formula = f"(总利润 / 汇率) × {discount_rate_hk*100:.0f}%"
                
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-header">
                    <span class="metric-label">🇭🇰 港股锚点</span>
                    <span class="formula-tag">{formula}</span>
                </div>
                <div>
                    <div class="metric-body">
                        <span class="metric-value">HK${anchor_price_hk_val:.2f}</span>
                        <span class="metric-delta {cls_hk}">{arrow_hk} {margin_hk:.2%}</span>
                    </div>
                    <div class="yield-container">
                        <div class="yield-row">
                            当前预期收益: <span class="yield-badge-purple">{expected_yield_hk:.2%}</span>
                        </div>
                        <div class="yield-row">
                            当前股息率 (税后): <span class="yield-badge-green">{dividend_yield_hk:.2%}</span>
                            <span class="tax-note">*(扣除20%红利税)</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    
    # --- 🎯 动态分档策略表 ---
    st.subheader(f"🎯 分档买入策略表 - {stock_name}")
    
    headers = ["区域", "期望收益率"]
    if market_type in ["A+H股", "仅A股"]:
        headers.extend(["A股目标价", "A股目标距离"])
    if market_type in ["A+H股", "仅港股"]:
        headers.extend(["H股目标价", "H股目标距离"])
    headers.append("仓位建议")
    
    html_table = '<table class="strategy-table"><thead><tr>'
    for h in headers:
        html_table += f'<th>{h}</th>'
    html_table += '</tr></thead><tbody>'

    yields = [x / 1000 for x in range(40, 125, 5)] + [x / 100 for x in range(13, 21, 1)]
    
    for y in yields:
        css_class = ""
        position = ""
        zone = ""
        
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

        if is_anchor_row:
            css_class += " anchor-row"
            zone += " (锚点)"

        html_table += f'<tr class="{css_class}">'
        html_table += f'<td>{zone}</td>'
        html_table += f'<td>{y:.1%}</td>'
        
        if market_type in ["A+H股", "仅A股"]:
            t_rmb = anchor_price_rmb / (y * 10)
            d_rmb = (t_rmb - current_price_rmb) / current_price_rmb if current_price_rmb > 0 else 0
            html_table += f'<td>¥{t_rmb:.2f}</td><td>{d_rmb:+.2%}</td>'
            
        if market_type in ["A+H股", "仅港股"]:
            t_hk = anchor_price_hk_val / (y * 10)
            d_hk = (t_hk - current_price_hk) / current_price_hk if current_price_hk > 0 else 0
            html_table += f'<td>HK${t_hk:.2f}</td><td>{d_hk:+.2%}</td>'
            
        html_table += f'<td>{position}</td></tr>'

    html_table += "</tbody></table>"
    
    st.markdown(html_table, unsafe_allow_html=True)
    st.caption("注：红色框选行代表 10.0% 收益率基准（锚点价格），此处建议加重仓位。")

else:
    st.info("👈 点击计算，生成最新策略表")
