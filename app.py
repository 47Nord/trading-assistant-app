import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import openai
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="📊 AI Trading Assistant", layout="wide")
st.title("📈 AI-Powered Trading Assistant")

openai.api_key = st.secrets.get("openai_api_key", "your-openai-key-here")

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
    fmp_api_key = "HDWZ0wWqWSQ2eFbafEAzxTPk7UbO0Oaw"  # Your real FMP API key
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

# --- GPT-4o Pattern Detector ---
def ask_gpt_for_pattern(ohlc_data):
    prompt = f"""
    Analyze the following OHLC chart data and detect known chart patterns (cup and handle, double bottom, etc.).
    Respond with the pattern name, confidence level (1-100%), and a trade suggestion (entry, stop loss, take profit).

    OHLC Data:
    {ohlc_data}
    """
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- Manual Asset Analysis ---
st.subheader("🔍 Check a Specific Asset")
asset_type = st.selectbox("Choose Asset Type", ["Crypto", "Stocks"])
symbols = crypto_list if asset_type == "Crypto" else stock_list
selected_symbol = st.selectbox("Select Asset", symbols)

data = load_data(selected_symbol)

st.subheader(f"Price Chart for {selected_symbol}")
st.line_chart(data['Close'])

if not data.empty:
    ohlc_input = data.tail(50).reset_index().to_dict(orient="records")
    if st.button("🔎 Let GPT-4o Analyze the Pattern"):
        analysis_result = ask_gpt_for_pattern(ohlc_input)
        st.text_area("📊 GPT-4o Pattern Detection Result", analysis_result, height=300)
else:
    st.warning("No data found for this symbol.")
