import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 頁面基本設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 專業自選股與派息追蹤 App")

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 側邊欄：導航 ---
page = st.sidebar.radio("功能導航", ["持倉管理", "全功能外幣換算"])

# --- 頁面 1：持倉管理 ---
if page == "持倉管理":
    st.subheader("📊 持倉細節與派息日曆")
    
    with st.expander("➕ 新增股票持倉"):
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                sym = st.text_input("股票代號 (例: 0005.HK, AAPL)").upper().strip()
            with col2:
                price = st.number_input("買入價", min_value=0.0, step=0.01)
            with col3:
                qty = st.number_input("持有股數", min_value=1, step=1)
            if st.form_submit_button("確認加入"):
                if sym:
                    st.session_state.portfolio.append({"symbol": sym, "buy_price": price, "shares": qty})
                    st.rerun()

    if st.session_state.portfolio:
        st.write("---")
        h1, h2, h3, h4, h5 = st.columns([2.5, 2, 2.5, 0.8, 0.8])
        h1.write("**公司名稱 (中/英)**")
        h2.write("**報價 / 成本**")
        h3.write("**盈虧 & 派息追蹤**")
        h4.write("**修改**")
        h5.write("**刪除**")
        st.write("---")

        for index, item in enumerate(st.session_state.portfolio):
            try:
                ticker = yf.Ticker(item['symbol'])
                info = ticker.info
                full_name = info.get('shortName', 'Unknown')
                
                div_rate = info.get('dividendRate') or 0.0
                div_yield = (info.get('dividendYield') or 0.0) * 100
                ex_date_timestamp = info.get('exDividendDate')
                ex_date_str = datetime.fromtimestamp(ex_date_timestamp).strftime('%Y-%m-%d') if ex_date_timestamp else "N/A"
                
                hist = ticker.history(period="5d")
                curr_p = hist['Close'].iloc[-1] if not hist.empty else 0.0
                
                market_val = round(curr_p * item['shares'], 2)
                total_cost = round(item['buy_price'] * item['shares'], 2)
                profit = round(market_val - total_cost, 2)
                p_pct = (profit / total_cost * 100) if total_cost != 0 else 0
                
                c1, c2, c3, c4, c5 = st.columns([2.5, 2, 2.5, 0.8, 0.8])
                with c1:
                    st.write(f"**{full_name}**")
                    st.caption(f"{item['symbol']} | {item['shares']} 股")
                with c2:
                    st.write(f"現價: **${curr_p:.2f}**")
                    st.caption(f"成本: ${item['buy_price']:.2f}")
                with c3:
                    color = "green" if profit >= 0 else "red"
                    st.markdown(f":{color}[**${profit:,.2f}** ({p_pct:+.2f}%)]")
                    if div_rate > 0:
                        st.caption(f"📅 除淨日: {ex_date_str}")
                        st.caption(f"💰 派息: 每股約 ${div_rate:.4f} (年率 {div_yield:.1f}%)")
                    else:
                        st.caption("🚫 無近期派息數據")
                with c4:
                    if st.button("✏️", key=f"ed_{index}"):
                        st.session_state.edit_index = index
                        st.rerun()
                with c5:
                    if st.button("🗑️", key=f"de_{index}"):
                        st.session_state.portfolio.pop(index)
                        st.rerun()
                st.write("---")
            except:
                st.error(f"數據加載錯誤 ({item['symbol']})")

        if 'edit_index' in st.session_state:
            idx = st.session_state.edit_index
            if idx < len(st.session_state.portfolio):
                edit_item = st.session_state.portfolio[idx]
                with st.sidebar:
                    st.write(f"### ✏️ 修改: {edit_item['symbol']}")
                    with st.form("edit_f"):
                        p = st.number_input("新成本", value=float(edit_item['buy_price']))
                        q = st.number_input("新股數", value=int(edit_item['shares']))
                        if st.form_submit_button("儲存"):
                            st.session_state.portfolio[idx]['buy_price'] = p
                            st.session_state.portfolio[idx]['shares'] = q
                            del st.session_state.edit_index
                            st.rerun()
                    if st.button("❌ 取消"):
                        del st.session_state.edit_index
                        st.rerun()
    else:
        st.info("目前尚無持倉數據。")

# --- 頁面 2：全功能外幣換算機 ---
elif page == "全功能外幣換算":
    st.subheader("💱 全球貨幣任意互換計算機")
    cur_list = ["HKD", "USD", "JPY", "GBP", "CNY", "EUR", "AUD", "CAD", "TWD"]
    col_in, col_mid, col_out = st.columns([2, 1, 2])
    with col_in:
        from_curr = st.selectbox("賣出貨幣", cur_list, index=1)
        amt = st.number_input("輸入金額", min_value=0.0, value=100.0)
    with col_mid:
        st.write("## ➡️")
    with col_out:
        to_curr = st.selectbox("買入貨幣", cur_list, index=0)
        
    if from_curr == to_curr:
        result, rate = amt, 1.0
    else:
        try:
            pair = f"{from_curr}{to_curr}=X"
            rate_data = yf.Ticker(pair).history(period="1d")
            rate = rate_data['Close'].iloc[-1]
            result = amt * rate
        except:
            st.error("暫時無法獲取該匯率組合")
            rate, result = 0, 0

    st.divider()
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(f"換算結果 ({to_curr})", f"{result:,.2f}")
    with res_col2:
        st.write(f"**當前匯率：** 1 {from_curr} = {rate:.4f} {to_curr}")
