import sys
sys.path.insert(0, 'src')

from database.backends.bigquery_manager import BigQueryManager
import asyncio

async def test():
    mgr = BigQueryManager({'project': 'agent9-465818', 'dataset': 'SalesOrders'})
    
    connected = await mgr.connect({
        'service_account_json_path': r'C:\Users\barry\CascadeProjects\Agent9-HERMES\secretsagent9\BigQuery\agent9-465818-2e57f7c9b334.json'
    })
    
    print(f"Connected: {connected}")
    
    if connected:
        query = """
            SELECT table_name 
            FROM `agent9-465818.SalesOrders.INFORMATION_SCHEMA.TABLES` 
            WHERE table_type IN ('BASE TABLE', 'VIEW')
        """
        
        print(f"Executing query:\n{query}")
        result = await mgr.execute_query(query)
        
        print(f"\nResult type: {type(result)}")
        print(f"Has to_dict: {hasattr(result, 'to_dict')}")
        print(f"Has empty: {hasattr(result, 'empty')}")
        
        if hasattr(result, 'shape'):
            print(f"Shape: {result.shape}")
        if hasattr(result, 'columns'):
            print(f"Columns: {list(result.columns)}")
        if hasattr(result, 'empty'):
            print(f"Empty: {result.empty}")
            
        print(f"\nData:\n{result}")

asyncio.run(test())
