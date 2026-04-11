import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# 1. 介面與連接設定
st.set_page_config(page_title="個人雲端股票管家", layout="wide")
st.title("📈 專業自選股 (穩定數據版)")

# 建立 Google Sheets 連接
conn = st.connection("gsheets", type=GSheetsConnection)

# 使用快取讀取雲端數據，減少對 Google 的請求
@st.cache_data(ttl=300)
def load_data():
    return conn.read(ttl="5m")

# 優化抓取價格函數，增加錯誤處理
def get_safe_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # 嘗試抓取 1 天歷史
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        # 如果 history 失敗，嘗試讀取 info
        return float(ticker.info.get('regularMarketPrice', 0.0))
    except Exception:
        return 0.0

if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None

# --- 側邊欄導航 ---
page = st.sidebar.radio("功能導航", ["持倉管理", "全功能外幣換算"])

if st.session_state.selected_stock:
    if st.sidebar.button("⬅️ 返回持倉列表"):
        st.session_state.selected_stock = None
        st.rerun()

# --- 持倉管理主介面 ---
if page == "持倉管理" and not st.session_state.selected_stock:
    try:
        df = load_data()
    except Exception as e:
        st.error("無法讀取 Google 表格，請確認 Secrets 設定與共用權限。")
        st.stop()

    st.subheader("📊 我的雲端持倉")
    
    with st.expander("➕ 新增股票"):
        with st.form("add_f"):
            s = st.text_input("代號 (例: 0005.HK)").upper().strip()
            p = st.number_input("買入價", min_value=0.0)
            q = st.number_input("股數", min_value=1)
            if st.form_submit_button("存入雲端"):
                new_data = pd.DataFrame([{"symbol": s, "buy_price": p, "shares": q, "div_info": "", "ex_date": ""}])
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(data=updated_df)
                st.cache_data.clear() # 清除快取以顯示新數據
                st.success("同步成功！")
                st.rerun()

    if not df.empty:
        # 清洗數據：確保沒有空行
        df = df.dropna(subset=['symbol'])
        
        for idx, row in df.iterrows():
            curr_p = get_safe_price(row['symbol'])
            
            c1, c2, c3, c4 = st.columns([3, 2, 2.5, 2.5])
            with c1:
                st.write(f"**{row['symbol']}**")
                st.caption(f"持倉: {row['shares']} 股")
            with c2:
                if curr_p > 0:
                    st.write(f"現價: **${curr_p:.2f}**")
                else:
                    st.write("現價: :orange[獲取中...]")
            with c3:
                profit = (curr_p - row['buy_price']) * row['shares'] if curr_p > 0 else 0
                st.write(f"盈虧: :{'green' if profit>=0 else 'red'}[${profit:,.2f}]")
            with c4:
                b1, b2 = st.columns(2)
                if b1.button("📅 派息", key=f"d_{idx}"):
                    st.session_state.selected_stock = row['symbol']
                    st.session_state.current_idx = idx
                    st.rerun()
                if b2.button("🗑️", key=f"del_{idx}"):
                    updated_df = df.drop(idx)
                    conn.update(data=updated_df)
                    st.cache_data.clear()
                    st.rerun()
            st.divider()
            time.sleep(0.1) # 增加微小延遲，防止被 Yahoo 判定為爬蟲
    else:
        st.info("雲端目前沒有數據。")

# --- 派息紀錄頁面 (略) 與 外幣換算 (略) ---
