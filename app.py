import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 頁面基本設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 我的自選股專業管理 App")

# 初始化數據儲存
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 側邊欄：導航與修改功能 ---
page = st.sidebar.radio("功能導航", ["持倉管理", "外幣換算計算機"])

# --- 頁面 1：持倉管理 ---
if page == "持倉管理":
    st.subheader("📊 實時持倉細節")
    
    # --- A. 新增股票表單 ---
    with st.expander("➕ 新增股票持倉"):
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                sym = st.text_input("股票代號 (例: 6655.HK, AAPL)").upper().strip()
            with col2:
                price = st.number_input("買入價", min_value=0.0, step=0.01)
            with col3:
                qty = st.number_input("持有股數", min_value=1, step=1)
            
            if st.form_submit_button("確認加入"):
                if sym:
                    st.session_state.portfolio.append({
                        "symbol": sym, 
                        "buy_price": price, 
                        "shares": qty
                    })
                    st.rerun()

    # --- B. 顯示持倉列表 ---
    if st.session_state.portfolio:
        st.write("---")
        # 標題行
        h1, h2, h3, h4, h5 = st.columns([2, 2, 2, 1, 1])
        h1.write("**股票名稱 / 代號**")
        h2.write("**報價 / 成本**")
        h3.write("**盈虧 (實時)**")
        h4.write("**修改**")
        h5.write("**刪除**")
        st.write("---")

        for index, item in enumerate(st.session_state.portfolio):
            try:
                ticker = yf.Ticker(item['symbol'])
                
                # 獲取名稱與現價 (使用 5 天歷史確保數據穩定)
                info = ticker.info
                name = info.get('shortName', '未知名稱')
                
                hist = ticker.history(period="5d")
                current_price = hist['Close'].iloc[-1] if not hist.empty else 0.0
                
                # 計算數值
                market_value = round(current_price * item['shares'], 2)
                total_cost = round(item['buy_price'] * item['shares'], 2)
                profit = round(market_value - total_cost, 2)
                profit_pct = (profit / total_cost * 100) if total_cost != 0 else 0
                
                # 建立顯示列
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
                
                with c1:
                    st.write(f"**{name}**")
                    st.caption(f"{item['symbol']} | {item['shares']} 股")
                
                with c2:
                    st.write(f"現價: **${current_price:.2f}**")
                    st.caption(f"成本: ${item['buy_price']:.2f}")
                
                with c3:
                    color = "green" if profit >= 0 else "red"
                    st.markdown(f":{color}[**${profit:,.2f}**]")
                    st.markdown(f":{color}[({profit_pct:+.2f}%)]")
                
                with c4:
                    if st.button("✏️", key=f"edit_{index}"):
                        st.session_state.edit_index = index
                        st.rerun()
                
                with c5:
                    if st.button("🗑️", key=f"del_{index}"):
                        st.session_state.portfolio.pop(index)
                        st.rerun()
                
                st.write("---")

            except Exception as e:
                st.error(f"數據加載錯誤 ({item['symbol']}): {e}")

        # --- C. 側邊欄修改對話框 (已修復 st.form 報錯問題) ---
        if 'edit_index' in st.session_state:
            idx = st.session_state.edit_index
            # 確保索引沒超限
            if idx < len(st.session_state.portfolio):
                edit_item = st.session_state.portfolio[idx]
                
                with st.sidebar:
                    st.write(f"### ✏️ 修改持倉: {edit_item['symbol']}")
                    
                    with st.form("edit_form"):
                        new_price = st.number_input("修正買入價", value=float(edit_item['buy_price']), step=0.01)
                        new_qty = st.number_input("修正股數", value=int(edit_item['shares']), step=1)
                        save_btn = st.form_submit_button("💾 儲存修改")
                        
                        if save_btn:
                            st.session_state.portfolio[idx]['buy_price'] = new_price
                            st.session_state.portfolio[idx]['shares'] = new_qty
                            del st.session_state.edit_index
                            st.rerun()
                    
                    # 取消按鈕必須在 st.form 之外
                    if st.button("❌ 取消修改"):
                        del st.session_state.edit_index
                        st.rerun()
            else:
                del st.session_state.edit_index
    else:
        st.info("目前尚無持倉數據。")

# --- 頁面 2：外幣換算計算機 ---
elif page == "外幣換算計算機":
    st.subheader("🔢 外幣即時換算")
    
    c_a, c_b = st.columns(2)
    currencies = ["USD", "JPY", "GBP", "CNY", "EUR", "AUD", "CAD"]
    
    with c_a:
        target = st.selectbox("選擇外幣", currencies)
        amt = st.number_input(f"輸入 {target} 金額", min_value=0.0, value=100.0, step=10.0)
    
    try:
        rate_ticker = yf.Ticker(f"{target}HKD=X")
        rate_hist = rate_ticker.history(period="5d")
        if not rate_hist.empty:
            current_rate = rate_hist['Close'].iloc[-1]
            result_hkd = amt * current_rate
            
            with c_b:
                st.write(f"### 當前 {target}/HKD 匯率")
                st.title(f"{current_rate:.4f}")
                st.metric("折合港幣 (HKD)", f"${result_hkd:,.2f}")
    except:
        st.error("匯率數據抓取失敗")

    st.info("💡 數據來源：Yahoo Finance 實時數據")
