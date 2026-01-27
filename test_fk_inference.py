import re

# Actual BigQuery view format from SalesOrderStarSchemaView
view_def = """FROM
  `agent9-465818`.SalesOrders.SalesOrders AS so
  JOIN
  `agent9-465818`.SalesOrders.BusinessPartners AS bp
  ON so.PARTNERID = bp.PARTNERID
  JOIN
  `agent9-465818`.SalesOrders.SalesOrderItems AS soi
  ON so.SALESORDERID = soi.SALESORDERID
  LEFT JOIN
  `agent9-465818`.SalesOrders.Products AS p
  ON soi.PRODUCTID = p.PRODUCTID"""

# BigQuery uses `project`.dataset.table format (backticks only around project name)
# Pattern needs to match: `project`.dataset.table or just table_name
# Capture the full qualified name including dots outside backticks
join_pattern = re.compile(
    r'(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\s+(?:`[^`]+`\.)?(\S+)\s+(?:AS\s+)?(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)',
    re.IGNORECASE | re.DOTALL
)

# FROM pattern: `project`.dataset.table AS alias
from_pattern = re.compile(r'FROM\s+(?:`[^`]+`\.)?(\S+)\s+(?:AS\s+)?(\w+)', re.IGNORECASE)
join_table_pattern = re.compile(r'JOIN\s+(?:`[^`]+`\.)?(\S+)\s+(?:AS\s+)?(\w+)', re.IGNORECASE)

# Test 1: Does FROM pattern match?
print("=== Test 1: FROM pattern ===")
for match in from_pattern.finditer(view_def):
    table_name = match.group(1)
    alias = match.group(2)
    if '.' in table_name:
        table_name = table_name.split('.')[-1]
    print(f"FROM: {alias} -> {table_name}")

# Test 2: Does simple JOIN pattern match (without ON)?
print("\n=== Test 2: Simple JOIN pattern ===")
for match in join_table_pattern.finditer(view_def):
    table_name = match.group(1)
    alias = match.group(2)
    if '.' in table_name:
        table_name = table_name.split('.')[-1]
    print(f"  JOIN: {alias} -> {table_name}")

# Test 3: Does ON pattern exist separately?
print("\n=== Test 3: ON conditions ===")
on_pattern = re.compile(r'ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', re.IGNORECASE)
for match in on_pattern.finditer(view_def):
    print(f"  ON: {match.group(1)}.{match.group(2)} = {match.group(3)}.{match.group(4)}")

# Test 4: Full JOIN...ON pattern
print("\n=== Test 4: Full JOIN...ON pattern ===")
for match in join_pattern.finditer(view_def):
    print(f"  Match: {match.groups()}")
