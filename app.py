import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="📊 AI Trading Assistant", layout="wide")
st.title("📈 AI-Powered Trading Assistant")

# --- Asset Lists ---
crypto_list = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD", "TRX-USD", "DOT-USD"]
stock_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "JPM", "UNH"]

asset_type = st.selectbox("Choose Asset Type", ["Crypto", "Stocks"])
symbols = crypto_list if asset_type == "Crypto" else stock_list

selected_symbol = st.selectbox("Select Asset", symbols)

# --- Fetch Price Data ---
@st.cache_data
def load_data(symbol):
    data = yf.download(symbol, period="60d", interval="1h")
    return data[['Close']].dropna()

data = load_data(selected_symbol)

# --- Pattern Detection Placeholder ---
def detect_cup_and_handle(prices):
    prices = prices.values.flatten()
    if len(prices) < 30:
        return False, None, None, None
    low = min(prices)
    high = max(prices)
    midpoint = (high + low) / 2
    left = prices[:len(prices)//2]
    right = prices[len(prices)//2:]
    if min(left) < midpoint and min(right) > midpoint:
        entry = prices[-1]
        stop = entry - (high - low) * 0.3
        target = entry + (entry - stop) * 2
        return True, entry, stop, target
    return False, None, None, None

# --- Analyze ---
found, entry, stop_loss, take_profit = detect_cup_and_handle(data['Close'])

# --- Display Chart ---
st.subheader(f"Price Chart for {selected_symbol}")
st.line_chart(data['Close'])

# --- Display Signal ---
if found:
    st.success(f"🟢 Pattern Detected: Cup & Handle")
    st.write(f"**Entry**: {entry:.2f}")
    st.write(f"**Stop Loss**: {stop_loss:.2f}")
    st.write(f"**Take Profit**: {take_profit:.2f}")
    rr = (take_profit - entry) / (entry - stop_loss)
    st.write(f"**Risk/Reward**: {rr:.2f}")
    st.markdown("### ✅ Suggested Action: BUY")
else:
    st.warning("No profitable pattern found right now. ⏳")

# --- Optional: Top Setup Table Preview ---
if st.checkbox("Show Top 10 Opportunities (Example)"):
    symbols_all = crypto_list + stock_list
    data_preview = []
    for sym in symbols_all:
        data_preview.append({
            "Symbol": sym,
            "Pattern": "Cup & Handle",
            "Entry": 100,
            "SL": 95,
            "TP": 110,
            "R:R": 2.0,
            "Signal": "BUY"
        })
    df = pd.DataFrame(data_preview)
    st.dataframe(df)
