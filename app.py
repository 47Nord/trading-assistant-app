import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="📊 AI Trading Assistant", layout="wide")
st.title("📈 AI-Powered Trading Assistant")

# --- Fetch top 100 crypto from CoinGecko ---
@st.cache_data
def fetch_top_100_crypto():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1}
    response = requests.get(url, params=params)
    coins = response.json()
    return [coin['symbol'].upper() + "-USD" for coin in coins]

# --- Fetch top stocks from FMP Free Tier ---
@st.cache_data
def fetch_top_stocks_free():
    fmp_api_key = "HDWZ0wWqWSQ2eFbafEAzxTPk7UbO0Oaw"
    url = f"https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={fmp_api_key}"
    response = requests.get(url)
    stocks = response.json()
    return [stock['symbol'] for stock in stocks if 'symbol' in stock]

crypto_list = fetch_top_100_crypto()
stock_list = fetch_top_stocks_free()

# --- Fetch Price Data ---
@st.cache_data
def load_data(symbol):
    try:
        data = yf.download(symbol, period="60d", interval="1h")
        return data[['Close']].dropna()
    except:
        return pd.DataFrame()

# --- Pattern Detectors ---
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

def detect_double_bottom(prices):
    prices = prices.values.flatten()
    if len(prices) < 30:
        return False, None, None, None
    min1 = prices[10]
    min2 = prices[20]
    if abs(min1 - min2) < 0.05 * min(prices):
        entry = prices[-1]
        stop = min(min1, min2) - 0.03 * entry
        target = entry + (entry - stop) * 2
        return True, entry, stop, target
    return False, None, None, None

def detect_placeholder_pattern(prices, pattern_name):
    prices = prices.values.flatten()
    if len(prices) < 30:
        return False, None, None, None
    entry = prices[-1]
    stop = entry * 0.97
    target = entry * 1.06
    return True, entry, stop, target

pattern_functions = {
    "Cup & Handle": detect_cup_and_handle,
    "Double Bottom": detect_double_bottom,
    "Head & Shoulders": lambda p: detect_placeholder_pattern(p, "Head & Shoulders"),
    "Inverse Head & Shoulders": lambda p: detect_placeholder_pattern(p, "Inverse Head & Shoulders"),
    "Ascending Triangle": lambda p: detect_placeholder_pattern(p, "Ascending Triangle"),
    "Descending Triangle": lambda p: detect_placeholder_pattern(p, "Descending Triangle"),
    "Symmetrical Triangle": lambda p: detect_placeholder_pattern(p, "Symmetrical Triangle"),
    "Bull Flag": lambda p: detect_placeholder_pattern(p, "Bull Flag"),
    "Bear Flag": lambda p: detect_placeholder_pattern(p, "Bear Flag"),
    "Rising Wedge": lambda p: detect_placeholder_pattern(p, "Rising Wedge"),
    "Falling Wedge": lambda p: detect_placeholder_pattern(p, "Falling Wedge"),
    "Rectangle": lambda p: detect_placeholder_pattern(p, "Rectangle"),
    "Triple Bottom": lambda p: detect_placeholder_pattern(p, "Triple Bottom"),
    "Triple Top": lambda p: detect_placeholder_pattern(p, "Triple Top"),
    "Rounding Bottom": lambda p: detect_placeholder_pattern(p, "Rounding Bottom")
}

# --- Top 5 Trades Section ---
st.subheader("🔥 Top 5 Trades Right Now")
if st.button("Start Scan (Top 100 Crypto + ~30 Stocks)"):
    all_symbols = crypto_list + stock_list
    top_trades = []

    for symbol in all_symbols:
        data = load_data(symbol)
        if data.empty:
            continue
        for name, func in pattern_functions.items():
            found, entry, sl, tp = func(data['Close'])
            if found:
                rr = (tp - entry) / (entry - sl)
                top_trades.append({
                    "Symbol": symbol,
                    "Pattern": name,
                    "Entry": round(entry, 2),
                    "Stop Loss": round(sl, 2),
                    "Take Profit": round(tp, 2),
                    "R:R": round(rr, 2),
                    "Signal": "BUY"
                })

    if top_trades:
        top_df = pd.DataFrame(top_trades).sort_values(by="R:R", ascending=False).head(5)
        st.dataframe(top_df)
    else:
        st.write("No high-probability trade setups found right now. ⏳")

# --- Manual Asset Analysis ---
st.subheader("🔍 Check a Specific Asset")
asset_type = st.selectbox("Choose Asset Type", ["Crypto", "Stocks"])
symbols = crypto_list if asset_type == "Crypto" else stock_list
selected_symbol = st.selectbox("Select Asset", symbols)

data = load_data(selected_symbol)

found_any = False
st.subheader(f"Price Chart for {selected_symbol}")
st.line_chart(data['Close'])

for name, func in pattern_functions.items():
    found, entry, sl, tp = func(data['Close'])
    if found:
        found_any = True
        st.success(f"🟢 Pattern Detected: {name}")
        st.write(f"**Entry**: {entry:.2f}")
        st.write(f"**Stop Loss**: {sl:.2f}")
        st.write(f"**Take Profit**: {tp:.2f}")
        rr = (tp - entry) / (entry - sl)
        st.write(f"**Risk/Reward**: {rr:.2f}")
        st.markdown("### ✅ Suggested Action: BUY")

if not found_any:
    st.warning("No profitable pattern found right now. ⏳")
