import pandas as pd
import os
import glob
from sqlalchemy import create_engine

# --- Configuration ---
# Since this script lives with the data, we look in the current directory
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_URL = os.getenv("DATABASE_URL")

STOCK_FILES = {
    'TSM':  'TSM_weekly_data.csv',
    'AAPL': 'AAPL_weekly_data.csv',
    'NVDA': 'NVDA_weekly_data.csv',
    'AMD':  'AMD_weekly_data.csv',
    'QCOM': 'QCOM_weekly_data.csv',
}

def get_latest_earthquake_file():
    """Finds the most recently created earthquake CSV in the current folder."""
    try:
        # Search for files starting with '202' (timestamps)
        search_path = os.path.join(DATA_DIR, '202*.csv')
        files = glob.glob(search_path)
        if not files:
            print(f"No earthquake files found in {DATA_DIR}")
            return None
        return max(files, key=os.path.getctime)
    except Exception as e:
        print(f"Error searching for files: {e}")
        return None

def process_and_upload():
    print("-" * 30)
    print(f"📂 Processing data in: {DATA_DIR}")
    
    if not DB_URL:
        print("❌ Error: DATABASE_URL environment variable is missing.")
        return

    # 1. Find Earthquake File
    eq_file = get_latest_earthquake_file()
    if not eq_file:
        print("❌ Error: No earthquake data file found.")
        return
    print(f"📄 Found Earthquake File: {os.path.basename(eq_file)}")

    # 2. Load and Standardize Stocks
    stock_dfs = []
    for ticker, filename in STOCK_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                
                # Dynamic Column Matching
                date_col = next((c for c in df.columns if 'date' in c.lower()), None)
                close_col = next((c for c in df.columns if 'close' in c.lower()), None)
                
                if date_col and close_col:
                    df = df.rename(columns={date_col: 'merge_date', close_col: 'Close'})
                    df['merge_date'] = pd.to_datetime(df['merge_date'], utc=True).dt.normalize()
                    df['ticker'] = ticker
                    stock_dfs.append(df[['merge_date', 'ticker', 'Close']])
                    print(f"   ✅ Loaded {ticker}: {len(df)} rows")
                else:
                    print(f"   ⚠️  Skipping {ticker}: Missing columns")
            except Exception as e:
                print(f"   ❌ Error reading {filename}: {e}")
        else:
            print(f"   ⚠️  Missing file: {filename}")

    if not stock_dfs:
        print("❌ No valid stock data found. Aborting.")
        return

    # 3. Merge & Pivot Stocks
    print("🔄 Pivoting Stock Data...")
    full_stock_df = pd.concat(stock_dfs)
    wide_stock_df = full_stock_df.pivot_table(index='merge_date', columns='ticker', values='Close')
    wide_stock_df.columns = [f"{col}_Close" for col in wide_stock_df.columns]
    wide_stock_df.reset_index(inplace=True)

    # 4. Process Earthquake Data
    print("🔄 Processing Earthquake Data...")
    try:
        eq_df = pd.read_csv(eq_file)
        eq_df.columns = eq_df.columns.str.strip().str.lower()
        
        eq_date_col = next((c for c in eq_df.columns if 'date' in c), None)
        eq_mag_col = next((c for c in eq_df.columns if 'mag' in c or 'ml' in c), None)

        if eq_date_col and eq_mag_col:
            eq_df['merge_date'] = pd.to_datetime(eq_df[eq_date_col], utc=True).dt.normalize()
            eq_df[eq_mag_col] = pd.to_numeric(eq_df[eq_mag_col], errors='coerce')
            
            # Aggregate max magnitude per day
            eq_agg = eq_df.sort_values(['merge_date', eq_mag_col], ascending=[True, False])
            eq_agg = eq_agg.drop_duplicates(subset=['merge_date'], keep='first')
            eq_agg = eq_agg.rename(columns={eq_mag_col: 'max_magnitude'})
            print(f"   ✅ Aggregated {len(eq_agg)} earthquake days")
        else:
            print("❌ Error: Could not find Date/Magnitude columns.")
            return
    except Exception as e:
        print(f"❌ Error processing earthquake file: {e}")
        return

    # 5. Final Merge
    print("🔄 Merging Datasets...")
    final_df = pd.merge(wide_stock_df, eq_agg[['merge_date', 'max_magnitude']], on='merge_date', how='left')
    final_df['max_magnitude'] = final_df['max_magnitude'].fillna(0)
    
    print(f"✅ Final Dataset: {final_df.shape[0]} rows")

    # 6. Upload
    print("🚀 Uploading to Database...")
    try:
        engine = create_engine(DB_URL)
        table_name = "processed_training_data"
        final_df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"🎉 SUCCESS! Written to table: '{table_name}'")
    except Exception as e:
        print(f"❌ Database Upload Failed: {e}")

if __name__ == "__main__":
    process_and_upload()
