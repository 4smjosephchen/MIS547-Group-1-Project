import yfinance as yf
import pandas as pd
import datetime
import os

# --- Configuration ---
# Docker maps this to /root/earthquake_data on the host
OUTPUT_DIR = "/app/output"
TICKERS = ['AAPL', 'AMD', 'NVDA', 'QCOM', 'TSM']

def run_collection():
    print(f"Starting Bi-Weekly collection. Saving to: {OUTPUT_DIR}")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Calculate Date Range (Last 10 Days)
    today = datetime.date.today()
    end_date = today.strftime('%Y-%m-%d')
    start_date = (today - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    
    print(f"--- Fetching data from {start_date} to {end_date} ---")
    
    # 2. Download Data
    try:
        data = yf.download(
            TICKERS, 
            start=start_date, 
            end=end_date, 
            group_by='ticker',
            progress=False
        )
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        return

    # 3. Process and Save
    for ticker in TICKERS:
        try:
            if len(TICKERS) == 1:
                df = data
            else:
                df = data[ticker]
            
            if 'Close' in df.columns:
                df = df[['Close']].copy()
                
                filename = f"{ticker}_weekly_data.csv"
                file_path = os.path.join(OUTPUT_DIR, filename)
                
                df.to_csv(file_path)
                print(f"✅ Saved {ticker}: {len(df)} rows")
            else:
                print(f"⚠️ {ticker}: 'Close' column not found.")
                
        except KeyError:
            print(f"⚠️ {ticker}: No data found.")

if __name__ == "__main__":
    run_collection()
