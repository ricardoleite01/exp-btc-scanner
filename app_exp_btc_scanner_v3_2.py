# app_exp_btc_scanner_v3_2.py

# pip install streamlit python-binance pandas matplotlib

import streamlit as st
from binance.client import Client
import pandas as pd
import time
import matplotlib.pyplot as plt

# Initialize client
client = Client()

# Function to get open price
def get_open_price(symbol: str, interval: str, lookback_str: str):
    klines = client.get_historical_klines(symbol, interval, lookback_str + " UTC")
    if not klines:
        raise ValueError(f"No data for {symbol} at {interval}")
    return float(klines[0][1])

# EXP BTC Calculation
def exp_btc(symbol: str, base='USDT'):
    tf_map = {
        '1d': '1 day ago',
        '4h': '4 hours ago',
        '1h': '1 hour ago',
        '30m': '30 minutes ago',
        '15m': '15 minutes ago',
        '5m': '5 minutes ago',
        '1m': '1 minute ago'
    }
    results = {}
    
    ticker_now = lambda s: float(client.get_symbol_ticker(symbol=f"{s}{base}")['price'])
    
    price_now = ticker_now(symbol)
    btc_now   = ticker_now('BTC')
    
    for label, lookback in tf_map.items():
        o_price = get_open_price(symbol+base, label, lookback)
        o_btc   = get_open_price('BTC'+base, label, lookback)
        ratio_now = price_now / btc_now
        ratio_past = o_price / o_btc
        expbtc = (ratio_now / ratio_past - 1) * 100
        results[label] = expbtc
    
    return results

# Plot mini chart (simulate trend — using static example here as Binance API does not give historical ratio directly!)
def plot_mini_chart(symbol: str, expbtc_dict: dict):
    tf_labels = list(expbtc_dict.keys())
    tf_values = list(expbtc_dict.values())

    fig, ax = plt.subplots()
    ax.plot(tf_labels, tf_values, marker='o')
    ax.set_title(f"{symbol} EXP BTC Trend")
    ax.set_ylabel("%")
    ax.grid(True)
    st.pyplot(fig)

# Streamlit UI
st.set_page_config(page_title="EXP BTC Multi-Symbol Scanner v3.2", page_icon="📈", layout="wide")
st.title("🚀 EXP BTC Multi-Symbol Scanner v3.2")

# User input
default_symbols = "COMP,ETH,SOL,MATIC,XRP,DOGE,OP,LINK,ADA,AVAX"
symbols_input = st.text_input("Enter comma-separated list of symbols:", value=default_symbols)
symbols_list = [s.strip().upper() for s in symbols_input.split(",")]

# Auto-refresh settings
refresh_rate = st.slider("Auto-refresh interval (seconds):", min_value=10, max_value=300, value=60, step=10)

# Sorting settings
sort_tf = st.selectbox("Sort by timeframe:", options=['1d', '4h', '1h', '30m', '15m', '5m', '1m'], index=0)

# Run loop
run_auto = st.checkbox("Auto-refresh mode (loop)", value=True)

# Scanner button
if st.button("Run Scanner") or run_auto:
    placeholder = st.empty()

    while True:
        with placeholder.container():
            st.info("Fetching data from Binance... Please wait ⏳")
            results_df = pd.DataFrame()
            mini_charts = {}

            for symbol in symbols_list:
                try:
                    st.write(f"Fetching {symbol}...")
                    data = exp_btc(symbol)
                    df_row = pd.DataFrame(data, index=[symbol])
                    results_df = pd.concat([results_df, df_row])
                    mini_charts[symbol] = data  # Save for mini chart
                    time.sleep(0.2)  # To avoid API rate limit
                except Exception as e:
                    st.warning(f"Error fetching {symbol}: {str(e)}")
            
            st.success("Scan complete!")

            # Sort
            results_df_sorted = results_df.sort_values(by=sort_tf, ascending=False)

            # Color formatting + alerts
            def highlight(val):
                if val > 5:
                    color = 'lime'
                elif val < -5:
                    color = 'red'
                else:
                    color = 'gray'
                return f'color: {color}; font-weight: bold'

            st.dataframe(results_df_sorted.style.applymap(highlight))

            # CSV export
            csv = results_df_sorted.to_csv().encode('utf-8')
            st.download_button(label="📥 Download CSV", data=csv, file_name='exp_btc_scan.csv', mime='text/csv')

            # Mini charts section
            st.subheader("Mini Charts (simulated trend)")
            for symbol in symbols_list:
                plot_mini_chart(symbol, mini_charts[symbol])

        if not run_auto:
            break
        st.info(f"Waiting {refresh_rate} seconds for next auto-refresh...")
        time.sleep(refresh_rate)
