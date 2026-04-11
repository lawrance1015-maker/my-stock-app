import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 介面設定 (仿 Yahoo Finance 簡潔風格)
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("?? 我的資產管理 App (Python 版)")

# 初始化 Session State (用來儲存持倉數據)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 側邊欄：功能導航 ---
page = st.sidebar.radio("導航", ["資產管理", "外幣換算計算機"])

# --- 頁面 1：資產管理 ---
if page == "資產管理":
    st.subheader("?? 持倉概況")
    
    # 新增股票表單
    with st.expander("? 新增股票持倉"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sym = st.text_input("代號 (例: 0700.HK, AAPL)").upper()
        with col2:
            buy_price = st.number_input("買入價", min_value=0.0)
        with col3:
            shares = st.number_input("股數", min_value=1)
        
        if st.button("確認加入"):
            st.session_state.portfolio.append({"symbol": sym, "buy_price": buy_price, "shares": shares})
            st.success(f"已加入 {sym}")

    # 顯示持倉列表與實時計算
    if st.session_state.portfolio:
        data_list = []
        for s in st.session_state.portfolio:
            # 抓取實時數據
            ticker = yf.Ticker(s['symbol'])
            # 獲取最近 1 天的歷史數據，取最後一筆收盤價
price_history = ticker.history(period="1d")
if not price_history.empty:
    current_price = price_history['Close'].iloc[-1]
else:
    current_price = 0.0  # 如果抓不到數據，給個預設值
            currency = ticker.info.get('currency', 'HKD')
            
            market_value = current_price * s['shares']
            profit = (current_price - s['buy_price']) * s['shares']
            profit_pct = (profit / (s['buy_price'] * s['shares'])) * 100
            
            data_list.append({
                "代號": s['symbol'],
                "貨幣": currency,
                "現價": round(current_price, 2),
                "成本": s['buy_price'],
                "股數": s['shares'],
                "市值": round(market_value, 2),
                "盈虧 ($)": round(profit, 2),
                "盈虧 (%)": f"{profit_pct:.2f}%"
            })
        
        df = pd.DataFrame(data_list)
        
        # 顯示總覽卡片
        total_profit = df[df['貨幣'] == 'HKD']['盈虧 ($)'].sum() # 簡化計算
        st.metric("估計總盈虧 (HKD)", f"${total_profit:,.2,f}", f"{total_profit/1000:.2f}%")
        
        # 顯示清單
        st.dataframe(df.style.applymap(lambda x: 'color: green' if '+' in str(x) or (isinstance(x, (int, float)) and x > 0) else 'color: red', subset=['盈虧 ($)', '盈虧 (%)']), use_container_width=True)
    else:
        st.info("目前尚無持倉，請點擊上方展開按鈕新增。")

# --- 頁面 2：外幣換算計算機 ---
elif page == "外幣換算計算機":
    st.subheader("?? 外幣換算器")
    
    col_a, col_b = st.columns(2)
    
    currencies = ["USD", "JPY", "GBP", "CNY", "EUR", "AUD"]
    with col_a:
        target_curr = st.selectbox("選擇外幣", currencies)
        amount = st.number_input(f"輸入 {target_curr} 金額", min_value=0.0, value=100.0)
    
    # 抓取實時匯率
    rate_ticker = yf.Ticker(f"{target_curr}HKD=X")
    rate = rate_ticker.fast_info['lastPrice']
    
    result = amount * rate
    
    with col_b:
        st.write(f"### 當前匯率: {rate:.4f}")
        st.metric(f"折合港幣 (HKD)", f"${result:,.2f}")
    
    st.info(f"數據來源：Yahoo Finance 實時匯率 ({target_curr}/HKD)")

