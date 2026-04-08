import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ===== HEADER =====
col1, col2 = st.columns([5,1])

with col1:
    st.title("📊 Interactive Algo Trading Dashboard")

with col2:
    st.markdown(
        "<p style='text-align:right; font-size:12px; color:gray;'>Author: M Nagesh KLH</p>",
        unsafe_allow_html=True
    )

# ===== STOCK LIST =====
nifty50 = [
"TCS.NS","INFY.NS","RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS",
"HINDUNILVR.NS","ITC.NS","LT.NS","SBIN.NS","BHARTIARTL.NS",
"KOTAKBANK.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS",
"TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS","NESTLEIND.NS",
"POWERGRID.NS","NTPC.NS","BAJFINANCE.NS","BAJAJFINSV.NS",
"ONGC.NS","WIPRO.NS","TECHM.NS","HCLTECH.NS","JSWSTEEL.NS",
"TATASTEEL.NS","ADANIENT.NS","ADANIPORTS.NS","COALINDIA.NS",
"GRASIM.NS","HEROMOTOCO.NS","CIPLA.NS","DRREDDY.NS",
"EICHERMOT.NS","INDUSINDBK.NS","BRITANNIA.NS","APOLLOHOSP.NS",
"DIVISLAB.NS","BPCL.NS","SHREECEM.NS","SBILIFE.NS",
"HDFCLIFE.NS","UPL.NS","BAJAJ-AUTO.NS","TATAMOTORS.NS"
]

us_stocks = ["AAPL","GOOG","MSFT","TSLA","AMZN"]
all_stocks = nifty50 + us_stocks

# ===== SIDEBAR =====
st.sidebar.header("⚙️ Settings")

stock = st.sidebar.selectbox("Select Stock", all_stocks)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-12-31"))

ma_short = st.sidebar.slider("Short MA Window", 10, 100, 50)
ma_long = st.sidebar.slider("Long MA Window", 100, 300, 200)

# ===== DATA =====
data = yf.download(stock, start=start_date, end=end_date)

if data.empty:
    st.error("No data found")
else:
    # Moving averages
    data['MA_Short'] = data['Close'].rolling(ma_short).mean()
    data['MA_Long'] = data['Close'].rolling(ma_long).mean()

    # Signals
    data['Signal'] = (data['MA_Short'] > data['MA_Long']).astype(int)
    data['Position'] = data['Signal'].diff()

    # ===== CURRENT SIGNAL =====
    latest_ma_short = data['MA_Short'].iloc[-1]
    latest_ma_long = data['MA_Long'].iloc[-1]

    if latest_ma_short > latest_ma_long:
        signal_text = "🟢 BUY"
    elif latest_ma_short < latest_ma_long:
        signal_text = "🔴 SELL"
    else:
        signal_text = "🟡 HOLD"

    # Returns
    data['Returns'] = data['Close'].pct_change().fillna(0)
    data['Strategy_Returns'] = data['Returns'] * data['Signal'].shift(1).fillna(0)

    # Cumulative
    data['Cumulative_Market'] = (1 + data['Returns']).cumprod()
    data['Cumulative_Strategy'] = (1 + data['Strategy_Returns']).cumprod()

    # ===== METRICS =====
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📈 Market Return", f"{(data['Cumulative_Market'].iloc[-1]-1)*100:.2f}%")
    col2.metric("🤖 Strategy Return", f"{(data['Cumulative_Strategy'].iloc[-1]-1)*100:.2f}%")
    col3.metric("📊 Data Points", len(data))

    # Small signal badge
    if signal_text == "🟢 BUY":
        color = "#28a745"
    elif signal_text == "🔴 SELL":
        color = "#dc3545"
    else:
        color = "#ffc107"

    col4.markdown(
        f"""
        <div style="
            text-align:center;
            padding:6px;
            border-radius:8px;
            background-color:{color};
            color:white;
            font-size:12px;
            font-weight:bold;">
            {signal_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    # ===== PRICE CHART =====
    st.subheader("📉 Price & Signals")

    fig, ax = plt.subplots(figsize=(12,5))

    ax.plot(data['Close'], label='Close Price')
    ax.plot(data['MA_Short'], label='MA Short')
    ax.plot(data['MA_Long'], label='MA Long')

    # BUY signals
    buy_signals = data[data['Position'] == 1]
    ax.scatter(buy_signals.index, buy_signals['Close'],
               color='green', s=100, label='BUY', marker='^')

    # SELL signals
    sell_signals = data[data['Position'] == -1]
    ax.scatter(sell_signals.index, sell_signals['Close'],
               color='red', s=100, label='SELL', marker='v')

    # SAFE annotation (no crash)
    try:
        if not buy_signals.empty:
            last_buy = buy_signals.iloc[-1]
            y_val = float(last_buy['Close'])
            ax.annotate('BUY',
                        (last_buy.name, y_val),
                        xytext=(0,10),
                        textcoords='offset points',
                        ha='center',
                        color='green')
    except:
        pass

    try:
        if not sell_signals.empty:
            last_sell = sell_signals.iloc[-1]
            y_val = float(last_sell['Close'])
            ax.annotate('SELL',
                        (last_sell.name, y_val),
                        xytext=(0,-15),
                        textcoords='offset points',
                        ha='center',
                        color='red')
    except:
        pass

    # Current price highlight
    ax.scatter(data.index[-1], data['Close'].iloc[-1],
               color='blue', s=150, label='Current')

    ax.legend()
    st.pyplot(fig)

    # ===== PERFORMANCE =====
    st.subheader("📊 Performance Comparison")

    fig2, ax2 = plt.subplots(figsize=(12,5))
    ax2.plot(data['Cumulative_Market'], label='Market')
    ax2.plot(data['Cumulative_Strategy'], label='Strategy')
    ax2.legend()

    st.pyplot(fig2)

    # ===== TABLE =====
    st.subheader("📋 Data Table")
    st.dataframe(data.tail(50))
