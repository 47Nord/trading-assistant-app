
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import openai
from datetime import datetime, timedelta

# --- Config ---
st.set_page_config(page_title="📈 AI Trading Assistant", layout="wide")
st.title("📊 Analyze Top Crypto & Stock Trades")

client = openai.OpenAI(api_key=st.secrets.get("openai_api_key", "your-openai-key-here"))
COINAPI_KEY = st.secrets["coinapi_key"]

@st.cache_data
def fetch_crypto_data(symbol_id, timeframe="1HRS"):
    url = f"https://rest.coinapi.io/v1/ohlcv/{symbol_id}/history"
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=2)
    params = {
        "period_id": timeframe,
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

def ask_gpt_batch(crypto_batch, stock_batch):
    prompt = f"""
You are a professional AI-powered trading assistant.

Based on the following asset data (last 48h of OHLC), analyze:
- Which assets show positive momentum
- Which of the top 15 chart patterns are detected (e.g. cup and handle, double bottom, flags, etc.)
Return the top 3 crypto and top 3 stock trade ideas with:
- Symbol
- Pattern name
- Probability
- Entry, Stop Loss, TP1/TP2/TP3
- Brief explanation

Crypto: {crypto_batch}
Stocks: {stock_batch}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def plot_pattern_chart(df, symbol):
    fig, ax = plt.subplots()
    ax.plot(df.index, df['Close'], label='Close', linewidth=2)
    ax.set_title(f"{symbol} – Last 48h")
    ax.grid(True)
    st.pyplot(fig)

st.subheader("🔍 Market-wide Top Trade Recommendations")

timeframe = st.selectbox("Select timeframe for analysis", ["1HRS", "30MIN", "15MIN", "4HRS", "1DAY"], index=0)

if st.button("📈 Analyze Top 100 Crypto & Stocks"):
    with st.spinner("Fetching and analyzing..."):
        crypto_symbols = [
            "BINANCE_SPOT_BTC_USDT", "BINANCE_SPOT_ETH_USDT", "BINANCE_SPOT_BNB_USDT", "BINANCE_SPOT_SOL_USDT", "BINANCE_SPOT_XRP_USDT"
        ] * 20  # Simulate 100

        stock_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX", "INTC", "AMD"
        ] * 10  # Simulate 100

        crypto_data_all = {}
        stock_data_all = {}
        df_lookup = {}

        for sym in crypto_symbols:
            df = fetch_crypto_data(sym, timeframe)
            if not df.empty:
                crypto_data_all[sym] = df.tail(48).reset_index().to_dict(orient="records")
                df_lookup[sym] = df

        for sym in stock_symbols:
            df = load_stock_data(sym)
            if not df.empty:
                stock_data_all[sym] = df.tail(48).reset_index().to_dict(orient="records")
                df_lookup[sym] = df

        all_batches = []
        for i in range(0, 100, 25):
            c_batch = dict(list(crypto_data_all.items())[i:i+25])
            s_batch = dict(list(stock_data_all.items())[i:i+25])
            result = ask_gpt_batch(c_batch, s_batch)
            all_batches.append(result)

        full_result = "\n\n".join(all_batches)
        st.text_area("📋 GPT-4o Trade Ideas", full_result, height=400)

        st.markdown("---")
        st.subheader("📉 Chart Visualizations of Suggested Symbols")

        top_matches = []
        for result in all_batches:
            for line in result.splitlines():
                for sym in df_lookup.keys():
                    if sym in line:
                        top_matches.append(sym)
                        break
            if len(top_matches) >= 6:
                break

        for sym in list(dict.fromkeys(top_matches))[:6]:
            st.markdown(f"### {sym}")
            plot_pattern_chart(df_lookup[sym], sym)

st.caption("Note: Batching avoids GPT token limits. Charts show the top 6 assets visually.")
