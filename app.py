import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 頁面基本設定
st.set_page_config(page_title="個人股票管理", layout="wide")
st.title("📈 專業自選股與派息管理 App")

# 初始化數據儲存
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'selected_stock_div' not in st.session_state:
    st.session_state.selected_stock_div = None

# --- 側邊欄：導航與返回 ---
if st.session_state.selected_stock_div:
    if st.sidebar.button("⬅️ 返回持倉列表"):
        st.session_state.selected_stock_div = None
        st.rerun()

page = st.sidebar.radio("功能導航", ["持倉管理", "全功能外幣換算"])

# --- 頁面 1：持倉管理 ---
if page == "持倉管理" and not st.session_state.selected_stock_div:
    st.subheader("📊 持倉列表")
    
    with st.expander("➕ 新增股票持倉"):
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                sym = st.text_input("股票代號 (例: 6655.HK, 0005.HK)").upper().strip()
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
        h1, h2, h3, h4 = st.columns([3, 2, 2.5, 2.5])
        h1.write("**公司名稱 (中文優先)**")
        h2.write("**報價 / 成本**")
        h3.write("**實時盈虧**")
        h4.write("**功能操作**")
        st.write("---")

        for index, item in enumerate(st.session_state.portfolio):
            try:
                ticker = yf.Ticker(item['symbol'])
                info = ticker.info
                
                # 名稱優化：中文全稱 > 簡稱 > 代號
                display_name = info.get('longName') or info.get('shortName') or item['symbol']
                
                hist = ticker.history(period="5d")
                curr_p = hist['Close'].iloc[-1] if not hist.empty else 0.0
                
                market_val = round(curr_p * item['shares'], 2)
                total_cost = round(item['buy_price'] * item['shares'], 2)
                profit = round(market_val - total_cost, 2)
                p_pct = (profit / total_cost * 100) if total_cost != 0 else 0
                
                c1, c2, c3, c4 = st.columns([3, 2, 2.5, 2.5])
                with c1:
                    st.write(f"**{display_name}**")
                    st.caption(f"{item['symbol']} | {item['shares']} 股")
                with c2:
                    st.write(f"現價: **${curr_p:.2f}**")
                    st.caption(f"成本: ${item['buy_price']:.2f}")
                with c3:
                    color = "green" if profit >= 0 else "red"
                    st.markdown(f":{color}[**${profit:,.2f}** ({p_pct:+.2f}%)]")
                with c4:
                    b1, b2, b3 = st.columns(3)
                    if b1.button("📅", key=f"div_{index}", help="查看派息詳情"):
                        st.session_state.selected_stock_div = item['symbol']
                        st.rerun()
                    if b2.button("✏️", key=f"ed_{index}"):
                        st.session_state.edit_index = index
                        st.rerun()
                    if b3.button("🗑️", key=f"de_{index}"):
                        st.session_state.portfolio.pop(index)
                        st.rerun()
                st.write("---")
            except:
                st.error(f"數據讀取失敗: {item['symbol']}")

        if 'edit_index' in st.session_state:
            idx = st.session_state.edit_index
            if idx < len(st.session_state.portfolio):
                edit_item = st.session_state.portfolio[idx]
                with st.sidebar:
                    st.write(f"### ✏️ 修改: {edit_item['symbol']}")
                    with st.form("edit_f"):
                        p = st.number_input("新成本", value=float(edit_item['buy_price']))
                        q = st.number_input("新股數", value=int(edit_item['shares']))
                        if st.form_submit_button("儲存修改"):
                            st.session_state.portfolio[idx]['buy_price'] = p
                            st.session_state.portfolio[idx]['shares'] = q
                            del st.session_state.edit_index
                            st.rerun()
                    if st.button("❌ 取消"):
                        del st.session_state.edit_index
                        st.rerun()
    else:
        st.info("目前尚無持倉數據。")

# --- 頁面 1.5：派息詳情版面 (獨立頁面) ---
elif st.session_state.selected_stock_div:
    sym = st.session_state.selected_stock_div
    st.subheader(f"📅 {sym} 派息追蹤詳情")
    
    try:
        ticker = yf.Ticker(sym)
        info = ticker.info
        calendar = ticker.calendar
        
        def fmt_date(ts):
            try: return datetime.fromtimestamp(ts).strftime('%Y-%m-%d') if ts > 0 else "N/A"
            except: return "N/A"

        # 嚴格遵循 8 個欄位的表格
        div_data = [
            {"資訊項": "公佈日期", "內容": calendar.get('Earnings Date', ["N/A"])[0] if isinstance(calendar, dict) else "N/A"},
            {"資訊項": "年度 / 截至", "內容": f"{datetime.now().year-1} - {datetime.now().year} 年度"},
            {"資訊項": "派息事項", "內容": "末期 / 中期業績"},
            {"資訊項": "派息內容", "內容": f"每股約 ${info.get('dividendRate', 'N/A')}"},
            {"資訊項": "方式", "內容": "現金派息"},
            {"資訊項": "除淨日", "內容": fmt_date(info.get('exDividendDate'))},
            {"資訊項": "截止過戶日期", "內容": "請參閱官方公告"},
            {"資訊項": "派息日", "內容": fmt_date(info.get('lastDividendDate'))}
        ]
        
        st.table(pd.DataFrame(div_data))
        
        # 顯示歷史紀錄
        st.write("### 📜 歷史派息記錄")
        divs = ticker.dividends.tail(5).sort_index(ascending=False)
        if not divs.empty:
            st.dataframe(divs)
        else:
            st.write("該股票目前無歷史派息紀錄。")
            
    except Exception:
        st.warning("⚠️ 該股票目前在數據庫中無完整的派息日曆資訊。")

# --- 頁面 2：全功能外幣換算機 ---
elif page == "全功能外幣換算":
    st.subheader("💱 全球貨幣任意互換")
    cur_list = ["HKD", "USD", "JPY", "GBP", "CNY", "EUR", "AUD", "CAD", "TWD"]
    col_in, col_mid, col_out = st.columns()
    with col_in:
        from_curr = st.selectbox("賣出貨幣", cur_list, index=1)
        amt = st.number_input("金額", min_value=0.0, value=100.0)
    with col_mid: st.write("## ➡️")
    with col_out:
        to_curr = st.selectbox("買入貨幣", cur_list, index=0)
    
    try:
        pair = f"{from_curr}{to_curr}=X"
        rate = yf.Ticker(pair).history(period="1d")['Close'].iloc[-1]
        st.metric(f"結果 ({to_curr})", f"{(amt * rate):,.2f}")
        st.caption(f"即時匯率: 1 {from_curr} = {rate:.4f} {to_curr}")
    except:
        st.error("匯率獲取失敗。")
