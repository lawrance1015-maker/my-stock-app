import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. 介面與連接設定
st.set_page_config(page_title="個人雲端股票管家", layout="wide")
st.title("📈 專業自選股 (雲端同步版)")

# 建立 Google Sheets 連接
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取雲端數據 (快取 10 分鐘)
def load_data():
    return conn.read(ttl="10m")

if 'selected_stock_div' not in st.session_state:
    st.session_state.selected_stock_div = None

# --- 側邊欄導航 ---
page = st.sidebar.radio("功能導航", ["持倉管理", "全功能外幣換算"])

# --- 頁面：持倉管理 ---
if page == "持倉管理" and not st.session_state.selected_stock_div:
    df = load_data()
    st.subheader("📊 我的持倉列表")
    
    # 新增股票表單 (同步到雲端)
    with st.expander("➕ 新增股票到雲端"):
        with st.form("add_form"):
            s_sym = st.text_input("代號 (例: 0005.HK)").upper().strip()
            s_price = st.number_input("買入價", min_value=0.0)
            s_qty = st.number_input("股數", min_value=1)
            if st.form_submit_button("確認存入雲端"):
                new_row = pd.DataFrame([{"symbol": s_sym, "buy_price": s_price, "shares": s_qty}])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("已同步至 Google Sheets！")
                st.rerun()

    if not df.empty:
        for idx, row in df.iterrows():
            ticker = yf.Ticker(row['symbol'])
            p = ticker.history(period="5d")['Close'].iloc[-1] if not ticker.history(period="5d").empty else 0.0
            
            c1, c2, c3, c4 = st.columns([3, 2, 2.5, 2.5])
            with c1:
                st.write(f"**{row['symbol']}**")
                st.caption(f"持倉: {row['shares']} 股")
            with c2:
                st.write(f"現價: **${p:.2f}**")
            with c3:
                profit = (p - row['buy_price']) * row['shares']
                st.write(f"盈虧: :{'green' if profit>=0 else 'red'}[${profit:,.2f}]")
            with c4:
                if st.button("📅 派息紀錄", key=f"d_{idx}"):
                    st.session_state.selected_stock_div = row['symbol']
                    st.rerun()
                if st.button("🗑️ 刪除", key=f"del_{idx}"):
                    updated_df = df.drop(idx)
                    conn.update(data=updated_df)
                    st.rerun()
            st.divider()

# --- 頁面：派息詳情 (支援手動存入 AASTOCKS 數據) ---
elif st.session_state.selected_stock_div:
    sym = st.session_state.selected_stock_div
    st.subheader(f"📅 {sym} 派息追蹤與修正")
    
    # 🔗 AASTOCKS 聯動
    pure_sym = sym.replace(".HK", "").zfill(5) if ".HK" in sym else sym
    url = f"https://aastocks.com{pure_sym}"
    st.info(f"🔗 [請在此對照 AASTOCKS 準確數據]({url})")

    # 手動錄入準確資訊
    with st.form("div_edit"):
        st.write("### ✍️ 錄入 AASTOCKS 正確資訊")
        note = st.text_input("派息事項 (例: 2024末期息 $0.5)")
        ex_date = st.date_input("除淨日")
        pay_date = st.date_input("派息日")
        
        if st.form_submit_button("儲存正確派息資料"):
            # 這裡可以擴展邏輯：將派息資訊更新到 Google Sheets 的對應行
            st.success("已記錄！(此功能需配合 Sheets 擴展欄位)")

    if st.button("返回列表"):
        st.session_state.selected_stock_div = None
        st.rerun()

# --- 外幣換算部分保持不變 ---
