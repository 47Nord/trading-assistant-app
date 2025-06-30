
# 🧠 AI Trading Assistant (Streamlit App)

This Streamlit app uses OpenAI GPT-4o and real-time market data to recommend the **Top 3 crypto** and **Top 3 stock** trades based on:

- ✅ Chart pattern recognition (Top 15 TA patterns)
- ✅ Positive momentum filtering
- ✅ Entry, Stop Loss, and Take Profit targets
- ✅ Pattern visualization using Matplotlib

## 🔧 Features

- ⏱️ Timeframe selection (e.g. 1H, 15M, 1D)
- 📈 GPT-4o analysis on 100 crypto & 100 stocks
- 📊 Pattern chart visualizations (Top 6)
- ⚙️ Data from CoinAPI and Yahoo Finance
- 🧠 Batching logic to stay within OpenAI token limits

## 🗂️ Folder Structure

```
/Trading_Assistant_Batched_Visualized_WithTimeframe/
├── app.py
├── requirements.txt
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml
```

## 🚀 How to Run Locally

1. Install Python packages:

```bash
pip install -r requirements.txt
```

2. Add your API keys:

Edit `.streamlit/secrets.toml`:

```toml
openai_api_key = "sk-..."
coinapi_key = "your-coinapi-key"
```

3. Run the app:

```bash
streamlit run app.py
```

## 🧪 Notes

- The app fetches 48 candles of OHLC data (by default 1H timeframe)
- Uses GPT-4o to detect profitable setups and summarize them
- Matplotlib used to plot price patterns for visual confirmation

## 📬 Future Add-ons

- Telegram/email alerts
- Scheduled auto-refresh
- Expanded asset coverage (Top 500)

---

Built with ❤️ using GPT-4o + Streamlit + CoinAPI
