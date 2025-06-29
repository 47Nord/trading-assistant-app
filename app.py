
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import openai
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="📊 AI Trading Assistant", layout="wide")
st.title("📈 Analyze ETH and AAPL")

client = openai.OpenAI(api_key=st.secrets["openai_api_key"])
COINAPI_KEY = st.secrets["coinapi_key"]

@st.cache_data
def fetch_crypto_data(symbol_id="BITSTAMP_SPOT_ETH_USD"):
    url = f"https://rest.coinapi.io/v1/ohlcv/{symbol_id}/history"
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=2)
    params = {
        "period_id": "1HRS",
        "time_start": start_time.strftime('%Y-%m-%dT%H:%M:%S'),
        "limit": 48
    }
    headers = {"X-CoinAPI-Key": COINAPI_KEY}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return pd.DataFrame()
    data = response.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['time_period_start'])
    df.set_index('timestamp', inplace=True)
    df = df.rename(columns={"price_close": "Close"})
    return df[["Close"]]

@st.cache_data
def load_stock_data(symbol):
    data = yf.download(symbol, period="2d", interval="1h")
    if data.empty or 'Close' not in data.columns:
        return pd.DataFrame()
    return data

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
    - 🌟 Entry level
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
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- Analysis ---
st.subheader("🔍 ETH (Crypto) and AAPL (Stock) Analysis")

if st.button("Run ETH & AAPL Analysis"):
    with st.spinner("Fetching and analyzing data..."):
        crypto_symbol = "BINANCE_SPOT_ETH_USDT"
        stock_symbol = "AAPL"

        crypto_df = fetch_crypto_data(crypto_symbol)
        stock_df = load_stock_data(stock_symbol)

        if crypto_df.empty:
            st.error(f"No data for crypto: {crypto_symbol}")
        else:
            st.markdown(f"### 📊 ETH Analysis")
            crypto_input = crypto_df.tail(50).reset_index().to_dict(orient="records")
            result = ask_gpt_for_pattern("ETH", crypto_input)
            st.text_area("ETH Analysis Result", result, height=300)

        if stock_df.empty:
            st.error(f"No data for stock: {stock_symbol}")
        else:
            st.markdown(f"### 📈 {stock_symbol.upper()} Analysis")
            stock_input = stock_df.tail(50).reset_index().to_dict(orient="records")
            result = ask_gpt_for_pattern(stock_symbol, stock_input)
            st.text_area("AAPL Analysis Result", result, height=300)

st.markdown("---")
st.caption("Note: This demo focuses on ETH and AAPL only to reduce API cost and improve performance.")
