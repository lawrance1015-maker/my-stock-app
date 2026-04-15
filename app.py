import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 介面設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 專業自選股與外幣管理系統")

# 初始化數據 (使用 session_state 確保在瀏覽器中持久存在)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["symbol", "buy_price", "shares"])

# 導航狀態管理
if 'current_page' not in st.session_state:
    st.session_state.current_page = "持倉管理"
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None

# --- 側邊欄：功能導航 ---
st.sidebar.title("功能選單")
if st.sidebar.button("📊 持倉管理"):
    st.session_state.current_page = "持倉管理"
    st.session_state.selected_stock = None
    st.rerun()

if st.sidebar.button("💱 全功能外幣換算"):
    st.session_state.current_page = "外幣換算"
    st.session_state.selected_stock = None
    st.rerun()

# --- 分頁邏輯 ---

# 1. 持倉管理頁面
if st.session_state.current_page == "持倉管理" and not st.session_state.selected_stock:
    st.subheader("📊 我的持倉清單")
    st.info("💡 提示：點擊表格底部的 [+] 新增行，直接在單格內輸入數據，按 Enter 確認。")
    
    # 使用數據編輯器，直接在 App 裡管理股票
    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        key="main_editor"
    )
    st.session_state.portfolio = edited_df

    if not st.session_state.portfolio.empty:
        st.divider()
        st.write("### 實時行情與操作")
        for idx, row in st.session_state.portfolio.iterrows():
            if not row['symbol']: continue
            try:
                ticker = yf.Ticker(str(row['symbol']).upper())
                # 抓取名稱與價格
                info = ticker.info
                name = info.get('longName') or info.get('shortName') or row['symbol']
                hist = ticker.history(period="1d")
                curr_p = hist['Close'].iloc[-1] if not hist.empty else 0.0
                
                # 計算
                cost = float(row['buy_price'] or 0) * float(row['shares'] or 0)
                market_val = curr_p * float(row['shares'] or 0)
                profit = market_val - cost
                p_pct = (profit / cost * 100) if cost != 0 else 0
                
                c1, c2, c3, c4 = st.columns([3, 2, 2.5, 2.5])
                with c1:
                    st.write(f"**{name}**")
                    st.caption(f"{row['symbol']}")
                with c2:
                    st.write(f"現價: **${curr_p:.2f}**")
                    st.caption(f"成本: ${row['buy_price']}")
                with c3:
                    color = "green" if profit >= 0 else "red"
                    st.markdown(f":{color}[**${profit:,.2f}** ({p_pct:+.2f}%)]")
                with c4:
                    if st.button("📅 派息詳情", key=f"div_{idx}"):
                        st.session_state.selected_stock = row['symbol']
                        st.rerun()
                st.write("---")
            except:
                st.error(f"無法讀取代號: {row['symbol']}")

# 2. 派息詳情頁面
elif st.session_state.selected_stock:
    sym = st.session_state.selected_stock
    st.subheader(f"📅 {sym} 派息追蹤與 AASTOCKS 聯動")
    
    # AASTOCKS 連結
    pure_sym = str(sym).replace(".HK", "").zfill(5)
    url = f"https://aastocks.com{pure_sym}"
    st.success(f"🔗 [點此打開 AASTOCKS 查看官方準確派息數據]({url})")
    
    try:
        ticker = yf.Ticker(str(sym))
        info = ticker.info
        calendar = ticker.calendar
        def fmt_d(ts):
            try: return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            except: return "N/A"

        div_data = [
            {"資訊項": "公司名稱", "內容": info.get('longName') or info.get('shortName') or sym},
            {"資訊項": "公佈日期", "內容": calendar.get('Earnings Date', ["N/A"]) if isinstance(calendar, dict) else "N/A"},
            {"資訊項": "派息內容", "內容": f"每股約 ${info.get('dividendRate', 'N/A')}"},
            {"資訊項": "除淨日", "內容": fmt_d(info.get('exDividendDate'))},
            {"資訊項": "派息日", "內容": fmt_d(info.get('lastDividendDate'))},
            {"資訊項": "數據來源", "內容": "Yahoo Finance (僅供參考)"}
        ]
        st.table(pd.DataFrame(div_data))
    except:
        st.warning("⚠️ 暫時無法從 Yahoo 獲取詳細派息數據，請使用上方 AASTOCKS 連結。")
    
    if st.button("⬅️ 返回持倉列表"):
        st.session_state.selected_stock = None
        st.rerun()

# 3. 外幣換算頁面
elif st.session_state.current_page == "外幣換算":
    st.subheader("💱 全球貨幣任意互換計算機")
    cur_list = ["HKD", "USD", "JPY", "GBP", "CNY", "EUR", "AUD", "CAD", "TWD"]
    
    col1, col2, col3 = st.columns([4, 1, 4])
    with col1:
        from_c = st.selectbox("賣出貨幣", cur_list, index=1)
        amt = st.number_input("金額", min_value=0.0, value=100.0)
    with col2:
        st.write("## ➡️")
    with col3:
        to_c = st.selectbox("買入貨幣", cur_list, index=0)
    
    if from_c != to_c:
        try:
            rate = yf.Ticker(f"{from_c}{to_c}=X").history(period="1d")['Close'].iloc[-1]
            st.divider()
            st.metric(f"換算結果 ({to_c})", f"{(amt * rate):,.2f}")
            st.caption(f"即時匯率: 1 {from_c} = {rate:.4f} {to_c}")
        except:
            st.error("匯率抓取失敗")
