import streamlit as st
import pandas as pd
import requests
import plotly.graph_objs as go
import time

st.set_page_config(page_title="📈 Multi-Stock Dashboard", layout="wide", initial_sidebar_state="collapsed")

API_KEY = 'e7d4092f2d3a4fda9a037855b95440e9'

# Header and stock selection
st.title("📈 Real-Time Multi-Stock Market Dashboard")

ticker_placeholder = st.empty()

# Sidebar filters
stocks = st.multiselect("🔍 Select Stocks", ["AAPL", "TSLA", "TCS.BSE", "RELIANCE.BSE", "INFY.BSE"], default=["AAPL", "TCS.BSE"])
interval = st.selectbox("📊 Interval", ["5min", "15min", "30min", "1day"])
auto_refresh = st.checkbox("🔁 Auto-refresh every 30 sec")
show_indicators = st.checkbox("📐 Show SMA (10) & RSI")

def fetch_data(symbol, interval):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&apikey={API_KEY}&outputsize=60&format=JSON"
    r = requests.get(url)
    data = r.json()
    if "values" not in data:
        return None
    df = pd.DataFrame(data["values"])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def calc_indicators(df):
    df['SMA_10'] = df['close'].rolling(window=10).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def create_dashboard():
    ticker_text = ""
    for symbol in stocks:
        df = fetch_data(symbol, interval)
        if df is None or df.empty:
            continue
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        change = latest['close'] - prev['close']
        percent = (change / prev['close']) * 100 if prev['close'] != 0 else 0
        ticker_text += f"{symbol}: ₹{latest['close']:.2f} ({percent:+.2f}%) | "
    ticker_placeholder.markdown(f"### 📢 {ticker_text.strip(' | ')}")

    for symbol in stocks:
        st.markdown(f"## {symbol.upper()}")
        df = fetch_data(symbol, interval)
        if df is None or df.empty:
            st.error(f"❌ No data for {symbol}")
            continue

        if show_indicators:
            df = calc_indicators(df)

        # Line Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['close'], name="Close"))
        if show_indicators:
            fig.add_trace(go.Scatter(x=df['datetime'], y=df['SMA_10'], name="SMA 10", line=dict(dash='dash')))
        fig.update_layout(title=f"{symbol.upper()} Price", xaxis_title="Time", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

        # Volume Chart
        vol_fig = go.Figure()
        vol_fig.add_trace(go.Bar(x=df['datetime'], y=df['volume'], name="Volume"))
        vol_fig.update_layout(title="Volume Traded", xaxis_title="Time", yaxis_title="Volume")
        st.plotly_chart(vol_fig, use_container_width=True)

        # RSI Chart
        if show_indicators:
            rsi_fig = go.Figure()
            rsi_fig.add_trace(go.Scatter(x=df['datetime'], y=df['RSI'], name="RSI", line=dict(color='orange')))
            rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
            rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")
            rsi_fig.update_layout(title="RSI Indicator", xaxis_title="Time", yaxis_title="RSI")
            st.plotly_chart(rsi_fig, use_container_width=True)

        # CSV Download
        st.download_button(f"📥 Download {symbol} CSV", df.to_csv(index=False), file_name=f"{symbol}_{interval}.csv", mime="text/csv")

while True:
    create_dashboard()
    if not auto_refresh:
        break
    time.sleep(30)
