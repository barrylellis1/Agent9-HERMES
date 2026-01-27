from google.cloud import bigquery
from google.oauth2 import service_account

# Load credentials
creds = service_account.Credentials.from_service_account_file(
    r'C:\Users\barry\CascadeProjects\Agent9-HERMES\secretsagent9\BigQuery\agent9-465818-2e57f7c9b334.json'
)

# Create client
client = bigquery.Client(credentials=creds, project='agent9-465818')

# Query for tables
query = """
SELECT table_name, table_type
FROM `agent9-465818.SalesOrders.INFORMATION_SCHEMA.TABLES`
WHERE table_type IN ('BASE TABLE', 'VIEW')
"""

print(f"Executing query:\n{query}\n")

try:
    result = client.query(query).result()
    print(f"Query succeeded. Total rows: {result.total_rows}")
    
    if result.total_rows == 0:
        print("\nNo tables or views found in the SalesOrders dataset.")
        print("Checking if dataset exists...")
        
        # List all datasets
        datasets = list(client.list_datasets())
        print(f"\nAvailable datasets in project agent9-465818:")
        for dataset in datasets:
            print(f"  - {dataset.dataset_id}")
    else:
        print("\nTables/Views found:")
        for row in result:
            print(f"  - {row.table_name} ({row.table_type})")
            
except Exception as e:
    print(f"Error: {e}")
