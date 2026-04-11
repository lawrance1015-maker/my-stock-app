import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 我的資產管理 App (Python 穩定版)")

# 初始化數據儲存空間
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 側邊欄：導航功能 ---
page = st.sidebar.radio("功能導航", ["資產管理", "外幣換算計算機"])

# --- 頁面 1：資產管理 ---
if page == "資產管理":
    st.subheader("📊 持倉概況")
    
    # 新增持倉表單
    with st.expander("➕ 新增股票持倉"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sym = st.text_input("股票代號 (例: 0700.HK, AAPL)").upper().strip()
        with col2:
            buy_price = st.number_input("買入價", min_value=0.0, step=0.01)
        with col3:
            shares = st.number_input("持有股數", min_value=1, step=1)
        
        if st.button("確認加入持倉"):
            if sym:
                st.session_state.portfolio.append({
                    "symbol": sym, 
                    "buy_price": buy_price, 
                    "shares": shares
                })
                st.success(f"成功加入 {sym}")
            else:
                st.error("請輸入有效代號")

    # 持倉列表與數據抓取
    if st.session_state.portfolio:
        data_list = []
        with st.spinner('正在從 Yahoo Finance 抓取即時數據...'):
            for s in st.session_state.portfolio:
                try:
                    ticker = yf.Ticker(s['symbol'])
                    
                    # 抓取最近 5 天數據以確保拿到最新的收盤價
                    hist = ticker.history(period="5d")
                    
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    else:
                        # 如果 history 沒數據，嘗試從 info 獲取 (備用)
                        current_price = ticker.info.get('regularMarketPrice') or \
                                        ticker.info.get('previousClose') or 0.0
                    
                    currency = ticker.info.get('currency', 'HKD')
                    
                    # 計算各項數值
                    market_value = current_price * s['shares']
                    total_cost = s['buy_price'] * s['shares']
                    profit = market_value - total_cost
                    profit_pct = (profit / total_cost * 100) if total_cost != 0 else 0
                    
                    data_list.append({
                        "代號": s['symbol'],
                        "貨幣": currency,
                        "現價": round(current_price, 2),
                        "成本": s['buy_price'],
                        "股數": s['shares'],
                        "市值": round(market_value, 2),
                        "盈虧 ($)": round(profit, 2),
                        "盈虧 (%)": round(profit_pct, 2)
                    })
                except Exception as e:
                    st.error(f"代號 {s['symbol']} 數據抓取失敗: {e}")

        if data_list:
            df = pd.DataFrame(data_list)
            
            # 總覽卡片 (計算總盈虧)
            total_profit = df['盈虧 ($)'].sum()
            st.metric("估計總盈虧 (綜合幣種)", f"${total_profit:,.2f}")
            
            # 格式化盈虧百分比顯示
            df['盈虧 (%)'] = df['盈虧 (%)'].apply(lambda x: f"{x:+.2f}%")
            
            # 顯示表格並根據盈虧著色
            st.dataframe(df, use_container_width=True)
            
            if st.button("🗑️ 清空所有持倉"):
                st.session_state.portfolio = []
                st.rerun()
    else:
        st.info("目前尚無持倉數據，請點擊上方展開按鈕新增。")

# --- 頁面 2：外幣換算計算機 ---
elif page == "外幣換算計算機":
    st.subheader("🔢 外幣即時換算")
    
    col_a, col_b = st.columns(2)
    currencies = ["USD", "JPY", "GBP", "CNY", "EUR", "AUD", "CAD"]
    
    with col_a:
        target_curr = st.selectbox("選擇外幣", currencies)
        amount = st.number_input(f"輸入 {target_curr} 金額", min_value=0.0, value=100.0, step=10.0)
    
    try:
        # 抓取即時匯率
        rate_ticker = yf.Ticker(f"{target_curr}HKD=X")
        rate_hist = rate_ticker.history(period="5d")
        
        if not rate_hist.empty:
            rate = rate_hist['Close'].iloc[-1]
            result = amount * rate
            
            with col_b:
                st.write(f"### 當前 {target_curr}/HKD 匯率")
                st.title(f"{rate:.4f}")
                st.metric("折合港幣 (HKD)", f"${result:,.2f}")
        else:
            st.error("暫時無法獲取匯率數據，請稍後再試。")
    except Exception as e:
        st.error(f"匯率查詢出錯: {e}")

    st.info("💡 數據來源：Yahoo Finance (數據可能會有 15 分鐘延遲)")
