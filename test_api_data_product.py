import requests
import json
import sys

def test_data_product_api():
    url = "http://localhost:8000/api/v1/registry/data-products/dp_sales_analytics_009"
    try:
        print(f"Fetching {url}...")
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            return

        data = response.json()
        dp = data.get("data", {})
        
        print(f"✅ ID: {dp.get('id')}")
        print(f"   Name: {dp.get('name')}")
        print(f"   Source System: {dp.get('source_system')}")
        
        if dp.get('source_system') == 'bigquery':
            print("   Status: CORRECT (API serving BigQuery)")
        else:
            print(f"   Status: INCORRECT (Expected 'bigquery', got '{dp.get('source_system')}')")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_data_product_api()
