import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def verify_supabase_data():
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return

    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }

    # Query specific data product
    target_id = "dp_sales_analytics_009"
    url = f"{supabase_url}/rest/v1/data_products?id=eq.{target_id}&select=*"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data:
                print(f"❌ Data product {target_id} NOT FOUND in Supabase.")
            else:
                dp = data[0]
                source_system = dp.get('source_system')
                print(f"✅ Data product {target_id} FOUND.")
                print(f"   Source System: {source_system}")
                
                if source_system == 'bigquery':
                    print("   Status: CORRECT (Updated seed applied)")
                else:
                    print(f"   Status: INCORRECT (Expected 'bigquery', got '{source_system}')")
                    print("   Action: Re-seeding required.")
        else:
            print(f"Error querying Supabase: {response.status_code} {response.text}")
            
    except Exception as e:
        print(f"Exception verifying data: {e}")

if __name__ == "__main__":
    verify_supabase_data()
