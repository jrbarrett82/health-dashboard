#!/usr/bin/env python3
"""Main script to sync Lose It! data from Gmail to InfluxDB."""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gmail_fetcher import GmailFetcher
from csv_parser import LoseItCSVParser
from database import HealthDatabase

load_dotenv()


def main():
    """Main sync process."""
    print("=" * 60)
    print("Health Data Sync - Lose It! → InfluxDB")
    print("=" * 60)
    print()
    
    # Configuration
    lookback_days = int(os.getenv('SYNC_LOOKBACK_DAYS', 90))
    
    # Initialize components
    gmail = GmailFetcher()
    parser = LoseItCSVParser()
    db = HealthDatabase()
    
    try:
        # Step 1: Connect to database
        print("[1/4] Connecting to InfluxDB...")
        if not db.connect():
            print("✗ Failed to connect to database. Is InfluxDB running?")
            print("  Try: docker compose up -d")
            return 1
        print()
        
        # Step 2: Authenticate with Gmail
        print("[2/4] Authenticating with Gmail...")
        try:
            gmail.authenticate()
        except FileNotFoundError as e:
            print(f"✗ {e}")
            print("\nTo set up Gmail API access:")
            print("1. Go to https://console.cloud.google.com/")
            print("2. Create a project and enable Gmail API")
            print("3. Create OAuth 2.0 credentials")
            print("4. Download credentials.json to this directory")
            return 1
        print()
        
        # Step 3: Fetch emails and attachments
        print(f"[3/4] Fetching emails from last {lookback_days} days...")
        messages = gmail.fetch_messages(days_back=lookback_days)
        
        if not messages:
            print("✗ No messages found with CSV attachments")
            return 1
        
        print(f"✓ Found {len(messages)} emails with attachments")
        
        # Extract all CSV files
        csv_files = []
        for msg in messages:
            for attachment in msg['attachments']:
                print(f"  - {attachment['filename']}")
                csv_files.append(attachment['data'])
        
        print()
        
        # Step 4: Parse and store data
        print("[4/4] Parsing CSV data and storing in database...")
        nutrition_data, food_entries = parser.parse_multiple_csvs(csv_files, extract_foods=True)
        
        if not nutrition_data:
            print("✗ No data parsed from CSV files")
            return 1
        
        # Write daily nutrition data to database
        success = db.batch_write_nutrition(nutrition_data)
        
        # Write individual food entries to database
        if food_entries:
            food_success = db.batch_write_food_entries(food_entries)
            if not food_success:
                print("⚠ Warning: Failed to write some food entries")
        
        if success:
            print()
            print("=" * 60)
            print("✓ Sync completed successfully!")
            print(f"  Total days synced: {len(nutrition_data)}")
            if food_entries:
                print(f"  Total food entries: {len(food_entries)}")
            
            # Show date range
            if nutrition_data:
                first_date = nutrition_data[0]['date']
                last_date = nutrition_data[-1]['date']
                print(f"  Date range: {first_date} to {last_date}")
            
            print()
            print("Next steps:")
            print("  • View in Grafana: http://localhost:3000")
            print("  • Chat with your data: python health_chat.py")
            print("=" * 60)
            return 0
        else:
            print("✗ Failed to write data to database")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n✗ Sync cancelled by user")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
