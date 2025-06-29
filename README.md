
# 📊 AI Trading Assistant (ETH + AAPL Demo)

This Streamlit app analyzes the top chart patterns using OpenAI GPT-4o and real-time market data from CoinAPI and Yahoo Finance.

---

## 🔧 Features
- Analyze ETH (crypto) and AAPL (stock) hourly chart
- Auto-detect top 15 profitable chart patterns
- GPT-4o-powered technical analysis summary
- Entry / Stop Loss / Take Profit (TP1, TP2, TP3)
- Supports CoinAPI and OpenAI APIs
- Easily expandable to support more assets

---

## 📦 Tech Stack
- Python
- Streamlit
- CoinAPI (crypto OHLC)
- Yahoo Finance (stocks)
- OpenAI GPT-4o

---

## 🚀 Setup Instructions

1. Clone this repo or upload to [Streamlit Cloud](https://streamlit.io/cloud).
2. Set up **secrets** in Streamlit preferences:

```toml
openai_api_key = "sk-...your-key"
coinapi_key = "eb1d8a5a-cd25-4155-8359-aeb6310cdc2b"
```

3. Install requirements:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
streamlit run app.py
```

---

## 💡 Customization

To add more symbols (like BTC, TSLA, etc.), modify the `symbol` list in `app.py` and call:
- `fetch_crypto_data(symbol_id)`
- `load_stock_data(symbol)`

---

## 📈 Supported Patterns
- Cup and Handle
- Inverse Head and Shoulders
- Bull Flag
- Pennant
- Double/Triple Bottom
- Ascending Triangle
- Falling Wedge
- and 8+ more

---

## 📩 Credits
Built with ❤️ using OpenAI and CoinAPI.
