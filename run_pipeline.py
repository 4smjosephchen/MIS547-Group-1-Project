import collect_data
import earthquake_scraper
import time
import datetime

def main():
    print(f"\n[{datetime.datetime.now()}] --- STARTING BI-WEEKLY PIPELINE ---")
    
    # Step 1: Collect Stocks
    print("\n[Step 1] Running Stock Collector...")
    try:
        collect_data.run_collection()
        print("✅ Stock collection finished.")
    except Exception as e:
        print(f"❌ Stock collection failed: {e}")

    # Give the filesystem a moment
    time.sleep(2)

    # Step 2: Scrape Earthquakes (which automatically triggers Step 3: Processing)
    print("\n[Step 2] Running Earthquake Scraper & Processor...")
    try:
        earthquake_scraper.download_data()
        print("✅ Earthquake scraping and processing finished.")
    except Exception as e:
        print(f"❌ Earthquake pipeline failed: {e}")

    print(f"\n[{datetime.datetime.now()}] --- PIPELINE COMPLETE ---")

if __name__ == "__main__":
    main()
