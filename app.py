import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 基本設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 專業自選股與 AASTOCKS 聯動 App")

# 初始化數據
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'selected_stock_div' not in st.session_state:
    st.session_state.selected_stock_div = None

# --- 側邊欄導航 ---
if st.session_state.selected_stock_div:
    if st.sidebar.button("⬅️ 返回持倉列表"):
        st.session_state.selected_stock_div = None
        st.rerun()

page = st.sidebar.radio("功能導航", ["持倉管理", "全功能外幣換算"])

# --- 情況 A: 全功能外幣換算 ---
if page == "全功能外幣換算":
    st.session_state.selected_stock_div = None
    st.subheader("💱 全球貨幣任意互換")
    cur_list = ["HKD", "USD", "JPY", "GBP", "CNY", "EUR", "AUD", "TWD"]
    c1, c2, c3 = st.columns([4, 1, 4])
    with c1:
        f_curr = st.selectbox("賣出貨幣", cur_list, index=1)
        amt = st.number_input("金額", min_value=0.0, value=100.0)
    with c2: st.markdown("<h2 style='text-align: center;'>➡️</h2>", unsafe_allow_html=True)
    with c3:
        t_curr = st.selectbox("買入貨幣", cur_list, index=0)
    
    try:
        rate = yf.Ticker(f"{f_curr}{t_curr}=X").history(period="1d")['Close'].iloc[-1]
        st.divider()
        st.metric(f"換算結果 ({t_curr})", f"{(amt * rate):,.2f}")
        st.caption(f"匯率: 1 {f_curr} = {rate:.4f} {t_curr}")
    except: st.error("匯率抓取失敗")

# --- 情況 B: 派息詳情 (結合 AASTOCKS 連結) ---
elif page == "持倉管理" and st.session_state.selected_stock_div:
    sym = st.session_state.selected_stock_div
    pure_sym = sym.replace(".HK", "").zfill(5) if ".HK" in sym else sym
    
    st.subheader(f"📅 {sym} 派息追蹤詳情")
    
    # 🔗 AASTOCKS 外部連結按鈕
    aastocks_url = f"https://www.aastocks.com/tc/stocks/analysis/dividend.aspx?symbol={pure_sym}"
    st.success(f"🔗 [點此開啟 AASTOCKS 查看官方準確派息數據]({aastocks_url})")
    
    ticker = yf.Ticker(sym)
    info = ticker.info
    
    # 顯示 8 個欄位 (增加手動修正提示)
    st.write("### 📝 派息紀錄表")
    div_rows = [
        {"資訊項": "公司名稱", "內容": info.get('longName') or info.get('shortName') or sym},
        {"資訊項": "公佈日期", "內容": "請參考 AASTOCKS 官網"},
        {"資訊項": "年度 / 截至", "內容": "2025-2026 年度"},
        {"資訊項": "派息內容", "內容": f"每股約 ${info.get('dividendRate', 'N/A')}"},
        {"資訊項": "方式", "內容": "現金派息"},
        {"資訊項": "除淨日", "內容": datetime.fromtimestamp(info.get('exDividendDate')).strftime('%Y-%m-%d') if info.get('exDividendDate') else "待定"},
        {"資訊項": "派息日", "內容": datetime.fromtimestamp(info.get('lastDividendDate')).strftime('%Y-%m-%d') if info.get('lastDividendDate') else "待定"}
    ]
    st.table(pd.DataFrame(div_rows))
    
    st.info("💡 由於 Yahoo 數據可能不準，建議點擊上方連結對照 AASTOCKS 資訊。")

# --- 情況 C: 持倉管理主列表 ---
elif page == "持倉管理":
    st.subheader("📊 持倉列表")
    
    with st.expander("➕ 新增股票持倉"):
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            with c1: new_sym = st.text_input("代號 (例: 0005.HK)").upper().strip()
            with c2: new_p = st.number_input("買入價", min_value=0.0)
            with c3: new_q = st.number_input("股數", min_value=1)
            if st.form_submit_button("確認加入"):
                st.session_state.portfolio.append({"symbol": new_sym, "buy_price": new_p, "shares": new_q})
                st.rerun()

    if st.session_state.portfolio:
        for idx, item in enumerate(st.session_state.portfolio):
            try:
                t = yf.Ticker(item['symbol'])
                p = t.history(period="5d")['Close'].iloc[-1]
                profit = (p - item['buy_price']) * item['shares']
                
                col1, col2, col3, col4 = st.columns([3, 2, 2.5, 2.5])
                with col1:
                    st.write(f"**{t.info.get('shortName', item['symbol'])}**")
                    st.caption(item['symbol'])
                with col2:
                    st.write(f"現價: **${p:.2f}**")
                with col3:
                    st.write(f"盈虧: :{'green' if profit>=0 else 'red'}[${profit:,.2f}]")
                with col4:
                    if st.button("📅 派息", key=f"d_{idx}"):
                        st.session_state.selected_stock_div = item['symbol']
                        st.rerun()
                    if st.button("🗑️ 刪除", key=f"del_{idx}"):
                        st.session_state.portfolio.pop(idx)
                        st.rerun()
                st.write("---")
            except: st.error(f"數據抓取失敗: {item['symbol']}")
