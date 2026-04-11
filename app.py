import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 介面設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 我的自選股專業管理")

# 初始化 Session State
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 側邊欄 ---
page = st.sidebar.radio("功能導航", ["持倉管理", "外幣計算機"])

if page == "持倉管理":
    st.subheader("📊 實時持倉細節")
    
    # --- 新增股票表單 ---
    with st.expander("➕ 新增股票持倉"):
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                sym = st.text_input("股票代號 (例: 6655.HK)").upper().strip()
            with col2:
                price = st.number_input("買入價", min_value=0.0, step=0.01)
            with col3:
                qty = st.number_input("持有股數", min_value=1, step=1)
            
            if st.form_submit_button("確認加入"):
                if sym:
                    st.session_state.portfolio.append({"symbol": sym, "buy_price": price, "shares": qty})
                    st.rerun()

    # --- 顯示與操作列表 ---
    if st.session_state.portfolio:
        display_data = []
        
        # 逐一抓取數據
        for index, item in enumerate(st.session_state.portfolio):
            try:
                ticker = yf.Ticker(item['symbol'])
                # 獲取名稱與現價
                info = ticker.info
                name = info.get('shortName', '未知名稱')
                
                # 抓取現價 (5天備援機制)
                hist = ticker.history(period="5d")
                current_price = hist['Close'].iloc[-1] if not hist.empty else 0.0
                
                # 計算
                market_value = round(current_price * item['shares'], 2)
                total_cost = round(item['buy_price'] * item['shares'], 2)
                profit = round(market_value - total_cost, 2)
                profit_pct = (profit / total_cost * 100) if total_cost != 0 else 0
                
                # 建立顯示列
                col_a, col_b, col_c, col_d, col_e = st.columns([2, 2, 2, 1, 1])
                
                with col_a:
                    st.write(f"**{item['symbol']}**\n{name}")
                with col_b:
                    st.write(f"現價: {current_price:.2f}\n成本: {item['buy_price']:.2f}")
                with col_c:
                    color = "green" if profit >= 0 else "red"
                    st.markdown(f"盈虧: :{color}[${profit:,.2f}]\n({profit_pct:+.2f}%)")
                
                # --- 修改功能 ---
                with col_d:
                    if st.button("修改", key=f"edit_{index}"):
                        st.session_state.edit_index = index
                
                # --- 刪除功能 ---
                with col_e:
                    if st.button("刪除", key=f"del_{index}"):
                        st.session_state.portfolio.pop(index)
                        st.rerun()
                
                st.divider()

            except Exception as e:
                st.error(f"數據加載錯誤 ({item['symbol']}): {e}")

        # --- 修改對話框 ---
        if 'edit_index' in st.session_state:
            idx = st.session_state.edit_index
            edit_item = st.session_state.portfolio[idx]
            with st.sidebar.form("edit_form"):
                st.write(f"### 修改 {edit_item['symbol']}")
                new_price = st.number_input("新買入價", value=edit_item['buy_price'])
                new_qty = st.number_input("新股數", value=edit_item['shares'])
                if st.form_submit_button("儲存修改"):
                    st.session_state.portfolio[idx]['buy_price'] = new_price
                    st.session_state.portfolio[idx]['shares'] = new_qty
                    del st.session_state.edit_index
                    st.rerun()
                if st.button("取消"):
                    del st.session_state.edit_index
                    st.rerun()

    else:
        st.info("目前沒有持倉。")

# 外幣計算機部分 (略，保持不變)
