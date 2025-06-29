import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import openai
from datetime import datetime

# --- Config ---
st.set_page_config(page_title="📊 AI Trading Assistant", layout="wide")
st.title("📈 AI Momentum & Pattern Screener")

client = openai.OpenAI(api_key=st.secrets.get("openai_api_key", "your-openai-key-here"))

@st.cache_data
def fetch_top_100_crypto():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1}
    response = requests.get(url, params=params)
    coins = response.json()
    return [coin['id'] for coin in coins]

@st.cache_data
def fetch_top_stocks_free():
    fmp_api_key = "HDWZ0wWqWSQ2eFbafEAzxTPk7UbO0Oaw"
    url = f"https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={fmp_api_key}"
    response = requests.get(url)
    stocks = response.json()
    return [stock['symbol'] for stock in stocks if 'symbol' in stock][:100]

@st.cache_data
def validate_symbol(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="1h")
        return not df.empty and "Close" in df.columns
    except:
        return False

raw_crypto = fetch_top_100_crypto()
raw_stocks = fetch_top_stocks_free()
stock_list = [s for s in raw_stocks if validate_symbol(s)]

@st.cache_data
def fetch_crypto_data(symbol_id):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol_id}/market_chart"
    params = {"vs_currency": "usd", "days": 2, "interval": "hourly"}
    response = requests.get(url, params=params)
    prices = response.json().get("prices", [])
    if not prices:
        return pd.DataFrame()
    df = pd.DataFrame(prices, columns=["timestamp", "Close"])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(window=14).mean() / df['Close'].pct_change().rolling(window=14).std()))
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Upper'] = df['BB_Middle'] + 2 * df['Close'].rolling(window=20).std()
    df['BB_Lower'] = df['BB_Middle'] - 2 * df['Close'].rolling(window=20).std()
    return df.dropna()

@st.cache_data
def load_data(symbol):
    for period, interval in [("2d", "1h"), ("5d", "1h"), ("1d", "30m")]:
        try:
            data = yf.download(symbol, period=period, interval=interval)
            if data.empty or 'Close' not in data.columns:
                continue
            data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
            data['RSI'] = 100 - (100 / (1 + data['Close'].pct_change().rolling(window=14).mean() / data['Close'].pct_change().rolling(window=14).std()))
            data['BB_Middle'] = data['Close'].rolling(window=20).mean()
            data['BB_Upper'] = data['BB_Middle'] + 2 * data['Close'].rolling(window=20).std()
            data['BB_Lower'] = data['BB_Middle'] - 2 * data['Close'].rolling(window=20).std()
            return data.dropna()
        except:
            continue
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
