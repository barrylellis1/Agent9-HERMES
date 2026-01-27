import sys
import asyncio
import logging
sys.path.insert(0, 'src')

from database.backends.bigquery_manager import BigQueryManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test')

async def test_bigquery_manager():
    # Create manager
    mgr = BigQueryManager(
        {'project': 'agent9-465818', 'dataset': 'SalesOrders'}, 
        logger
    )
    
    # Connect with service account
    connection_params = {
        'service_account_json_path': r'C:\Users\barry\CascadeProjects\Agent9-HERMES\secretsagent9\BigQuery\agent9-465818-2e57f7c9b334.json',
        'project': 'agent9-465818',
        'dataset': 'SalesOrders'
    }
    
    print("Connecting to BigQuery...")
    connected = await mgr.connect(connection_params)
    print(f"Connected: {connected}")
    
    if not connected:
        print("Failed to connect!")
        return
    
    # Execute discovery query
    query = """
        SELECT table_name
        FROM `agent9-465818.SalesOrders.INFORMATION_SCHEMA.TABLES`
        WHERE table_type IN ('BASE TABLE', 'VIEW')
    """
    
    print(f"\nExecuting query:\n{query}\n")
    
    result = await mgr.execute_query(query, {})
    
    print(f"\nResult type: {type(result)}")
    print(f"Result shape: {result.shape if hasattr(result, 'shape') else 'N/A'}")
    print(f"Result columns: {list(result.columns) if hasattr(result, 'columns') else 'N/A'}")
    print(f"Number of rows: {len(result)}")
    
    if len(result) > 0:
        print(f"\nTables found:")
        for idx, row in result.iterrows():
            print(f"  - {row['table_name']}")
    else:
        print("\nNo tables found!")
    
    await mgr.disconnect()

if __name__ == "__main__":
    asyncio.run(test_bigquery_manager())
