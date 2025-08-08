import pandas as pd
from datetime import datetime

# CONFIGURE THESE
input_csv = 'FinancialTransactions.csv'         # Your source file
output_csv = 'FinancialTransactions_shifted.csv' # Output file
date_column = 'DATE'                             # Name of the date column
years_to_shift = 5                               # Number of years to add
value_columns = ['value']                        # List of columns with EU decimal format

def shift_yyyymmdd_date(date_str, years):
    try:
        dt = datetime.strptime(str(date_str), "%Y%m%d")
        shifted = dt.replace(year=dt.year + years)
        return shifted.strftime("%Y%m%d")
    except Exception:
        return date_str  # If parsing fails, return original

# Read CSV with semicolon delimiter and treat all as string to preserve EU format
df = pd.read_csv(input_csv, delimiter=';', dtype=str)

# Shift the date column
df[date_column] = df[date_column].apply(lambda d: shift_yyyymmdd_date(d, years_to_shift))

# Optionally, ensure EU decimal format is preserved (comma as decimal separator)
for col in value_columns:
    if col in df.columns:
        # Convert to float (handling EU format), then back to string with comma as decimal
        df[col] = df[col].apply(lambda x: '{:,.2f}'.format(float(x.replace(',', '.'))).replace('.', ',') if pd.notnull(x) and x != '' else x)

# Write back to CSV with semicolon delimiter and no index
df.to_csv(output_csv, sep=';', index=False, encoding='utf-8')

print(f"Dates shifted by {years_to_shift} years. Output written to {output_csv}")
