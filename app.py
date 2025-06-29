import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import openai
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="📊 AI Trading Assistant", layout="wide")
st.title("📈 AI Momentum & Pattern Screener")

client = openai.OpenAI(api_key=st.secrets.get("openai_api_key", "your-openai-key-here"))

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
    return [stock['symbol'] for stock in stocks if 'symbol' in stock][:100]

crypto_list = fetch_top_100_crypto()
stock_list = fetch_top_stocks_free()

@st.cache_data
def load_data(symbol):
    try:
        data = yf.download(symbol, period="60d", interval="1h")
        data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
        data['RSI'] = 100 - (100 / (1 + data['Close'].pct_change().rolling(window=14).mean() / data['Close'].pct_change().rolling(window=14).std()))
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        data['BB_Upper'] = data['BB_Middle'] + 2 * data['Close'].rolling(window=20).std()
        data['BB_Lower'] = data['BB_Middle'] - 2 * data['Close'].rolling(window=20).std()
        return data.dropna()
    except:
        return pd.DataFrame()

analysis_log = []

def ask_gpt_for_pattern(symbol, ohlc_data):
    prompt = f"""
    You are a highly skilled trading assistant working with a top-performing professional day trader.
    Analyze the following OHLC data for the asset {symbol} using expert-level technical analysis.
    Your goal is to detect the presence of any of the 15 most reliable and high-probability chart patterns—
    such as cup and handle, double bottom, inverse head and shoulders, ascending triangle, symmetrical triangle,
    falling wedge, bull flag, bullish pennant, triple bottom, rounded bottom, and others.

    Assess whether there is clear positive momentum in the recent price action.

    Return the following:
    - 📌 Pattern name (if found)
    - 📈 Probability of pattern success (0–100%)
    - 📊 Momentum assessment
    - 🎯 Entry level
    - 🛡️ Stop loss level
    - 💰 Take profit 1, 2, and 3 targets (TP1/TP2/TP3)

    Now let’s deeply analyze this chart:
    - What pattern(s) do you see?
    - Which one is the most likely to play out?
    - What are the exact trading levels?

    Additionally, create a simple visual representation (a sketch or diagram in markdown or text) showing the pattern on the price data so the trader can recognize it immediately.

    OHLC Data:
    {ohlc_data}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        analysis_log.append({"symbol": symbol, "timestamp": datetime.utcnow(), "result": result})
        return result
    except Exception as e:
        return f"Error: {e}"

def analyze_top_setups(symbols):
    results = []
    for symbol in symbols:
        data = load_data(symbol)
        if data.empty or len(data) < 50:
            continue
        ohlc_input = data.tail(50).reset_index().to_dict(orient="records")
        analysis = ask_gpt_for_pattern(symbol, ohlc_input)
        results.append((symbol, analysis))
    return results

# --- Show Top 3 Crypto and Top 3 Stocks ---
st.subheader("🚀 Top 3 Crypto & Stock Trade Ideas")
if st.button("Run Screener"):
    with st.spinner("Analyzing market data... this may take a minute"):
        crypto_results = analyze_top_setups(crypto_list)
        stock_results = analyze_top_setups(stock_list)

        st.markdown("## 📈 Top 3 Crypto Setups")
        for symbol, analysis in crypto_results[:3]:
            st.markdown(f"### {symbol}")
            st.text_area("Pattern & Momentum Analysis", analysis, height=300)

        st.markdown("## 📊 Top 3 Stock Setups")
        for symbol, analysis in stock_results[:3]:
            st.markdown(f"### {symbol}")
            st.text_area("Pattern & Momentum Analysis", analysis, height=300)

# --- Log Analysis ---
st.subheader("📝 Analysis Log")
if analysis_log:
    for log in analysis_log[-10:][::-1]:
        st.markdown(f"**{log['timestamp']} - {log['symbol']}**")
        st.code(log['result'], language="text")

# --- Manual Check ---
st.subheader("🔍 Analyze Specific Asset")
asset_type = st.selectbox("Choose Asset Type", ["Crypto", "Stocks"])
symbols = crypto_list if asset_type == "Crypto" else stock_list
selected_symbol = st.selectbox("Select Asset", symbols)

data = load_data(selected_symbol)

st.subheader(f"📉 Chart: {selected_symbol}")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(data.index, data['Close'], label="Close Price", linewidth=1.5)
if 'EMA20' in data.columns:
    ax.plot(data.index, data['EMA20'], label="EMA 20", linestyle='--', alpha=0.7)
if 'BB_Lower' in data.columns and 'BB_Upper' in data.columns:
    ax.fill_between(data.index, data['BB_Lower'], data['BB_Upper'], color='gray', alpha=0.1, label="Bollinger Bands")

# Highlight the last 50 candles (pattern zone)
if len(data) >= 50:
    pattern_zone = data.tail(50)
    ax.axvspan(pattern_zone.index[0], pattern_zone.index[-1], color='yellow', alpha=0.1, label='Pattern Zone')

ax.set_title(f"{selected_symbol} - Last 60 Days")
ax.legend()
st.pyplot(fig)

# Export chart as image
img_path = f"{selected_symbol}_chart.png"
fig.savefig(img_path)
st.download_button("📥 Download Chart Image", open(img_path, "rb"), file_name=img_path)

if not data.empty:
    ohlc_input = data.tail(50).reset_index().to_dict(orient="records")
    if st.button("🔎 Analyze This Asset"):
        analysis_result = ask_gpt_for_pattern(selected_symbol, ohlc_input)
        st.text_area("📊 Pattern & Momentum Detection", analysis_result, height=300)
else:
    st.warning("No data found for this symbol.")
