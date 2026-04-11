import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 頁面基本設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 專業自選股與派息管理 App")

# 初始化數據
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'selected_stock_div' not in st.session_state:
    st.session_state.selected_stock_div = None

# --- 側邊欄導航 ---
# 如果正在看派息詳情，顯示返回按鈕
if st.session_state.selected_stock_div:
    if st.sidebar.button("⬅️ 返回持倉列表"):
        st.session_state.selected_stock_div = None
        st.rerun()

page = st.sidebar.radio("功能導航", ["持倉管理", "全功能外幣換算"])

# --- 頁面邏輯判斷 ---

# 情況 A: 全功能外幣換算 (優先判斷，確保不被覆蓋)
if page == "全功能外幣換算":
    st.session_state.selected_stock_div = None # 切換頁面時清除派息選取
    st.subheader("💱 全球貨幣任意互換")
    cur_list = ["HKD", "USD", "JPY", "GBP", "CNY", "EUR", "AUD", "CAD", "TWD"]
    col_in, col_mid, col_out = st.columns([2, 1, 2])
    with col_in:
        from_curr = st.selectbox("賣出貨幣", cur_list, index=1)
        amt = st.number_input("金額", min_value=0.0, value=100.0)
    with col_mid: st.markdown("<h2 style='text-align: center;'>➡️</h2>", unsafe_allow_html=True)
    with col_out:
        to_curr = st.selectbox("買入貨幣", cur_list, index=0)
    
    try:
        pair = f"{from_curr}{to_curr}=X"
        rate = yf.Ticker(pair).history(period="1d")['Close'].iloc[-1]
        st.divider()
        res1, res2 = st.columns(2)
        res1.metric(f"換算結果 ({to_curr})", f"{(amt * rate):,.2f}")
        res2.write(f"**即時匯率：**  \n1 {from_curr} = {rate:.4f} {to_curr}")
    except:
        st.error("匯率抓取失敗")

# 情況 B: 查看特定股票的派息詳情 (僅在持倉管理分頁下觸發)
elif page == "持倉管理" and st.session_state.selected_stock_div:
    sym = st.session_state.selected_stock_div
    st.subheader(f"📅 {sym} 派息追蹤詳情")
    
    try:
        ticker = yf.Ticker(sym)
        info = ticker.info
        calendar = ticker.calendar
        def fmt_date(ts):
            try: return datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts > 0 else "N/A"
            except: return "N/A"

        div_rows = [
            {"資訊項": "公司名稱", "內容": info.get('longName') or info.get('shortName') or sym},
            {"資訊項": "公佈日期", "內容": calendar.get('Earnings Date', ["N/A"]) if isinstance(calendar, dict) else "N/A"},
            {"資訊項": "年度 / 截至", "內容": f"{datetime.now().year-1} - {datetime.now().year} 年度"},
            {"資訊項": "派息事項", "內容": "末期 / 中期業績"},
            {"資訊項": "派息內容", "內容": f"每股約 ${info.get('dividendRate', 'N/A')}"},
            {"資訊項": "方式", "內容": "現金派息"},
            {"資訊項": "除淨日", "內容": fmt_date(info.get('exDividendDate'))},
            {"資訊項": "派息日", "內容": fmt_date(info.get('lastDividendDate'))}
        ]
        st.table(pd.DataFrame(div_rows))
        
        st.write("### 📜 歷史派息記錄")
        divs = ticker.dividends.tail(5).sort_index(ascending=False)
        if not divs.empty: st.dataframe(divs)
        else: st.write("暫無歷史紀錄")
    except:
        st.warning("⚠️ 該股票目前無完整派息日曆數據。")

# 情況 C: 持倉管理主列表
elif page == "持倉管理":
    st.subheader("📊 我的持倉列表")
    
    with st.expander("➕ 新增股票持倉"):
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1: sym = st.text_input("股票代號 (例: 0005.HK)").upper().strip()
            with c2: price = st.number_input("買入價", min_value=0.0)
            with c3: qty = st.number_input("持有股數", min_value=1)
            if st.form_submit_button("確認加入"):
                if sym:
                    st.session_state.portfolio.append({"symbol": sym, "buy_price": price, "shares": qty})
                    st.rerun()

    if st.session_state.portfolio:
        st.write("---")
        for index, item in enumerate(st.session_state.portfolio):
            try:
                ticker = yf.Ticker(item['symbol'])
                info = ticker.info
                # 確保 6655.HK 能顯示正確名稱 (華新建材等)
                display_name = info.get('longName') or info.get('shortName') or item['symbol']
                
                curr_p = ticker.history(period="5d")['Close'].iloc[-1]
                market_val = curr_p * item['shares']
                profit = market_val - (item['buy_price'] * item['shares'])
                p_pct = (profit / (item['buy_price'] * item['shares']) * 100) if item['buy_price'] != 0 else 0
                
                col1, col2, col3, col4 = st.columns([3, 2, 2.5, 2.5])
                with col1:
                    st.write(f"**{display_name}**")
                    st.caption(f"{item['symbol']} | {item['shares']} 股")
                with col2:
                    st.write(f"現價: **${curr_p:.2f}**")
                    st.caption(f"成本: ${item['buy_price']:.2f}")
                with col3:
                    color = "green" if profit >= 0 else "red"
                    st.markdown(f":{color}[**${profit:,.2f}** ({p_pct:+.2f}%)]")
                with col4:
                    b1, b2, b3 = st.columns(3)
                    if b1.button("📅", key=f"div_{index}"):
                        st.session_state.selected_stock_div = item['symbol']
                        st.rerun()
                    if b2.button("✏️", key=f"ed_{index}"):
                        st.session_state.edit_index = index
                        st.rerun()
                    if b3.button("🗑️", key=f"de_{index}"):
                        st.session_state.portfolio.pop(index)
                        st.rerun()
                st.write("---")
            except: st.error(f"讀取失敗: {item['symbol']}")
    else:
        st.info("目前尚無持倉。")
