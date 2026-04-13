#!/usr/bin/env python3
"""
Bootstrap Snowflake Trial Environment for Agent9 Onboarding Demo

This utility creates a minimal FI Star Schema in a Snowflake trial account
with sample data, enabling validation of the OnboardingService discovery and
analysis workflow.

IMPORTANT: This is a temporary bootstrap utility for trial/demo purposes.
It should be deprecated once customers have real curated data.

Usage:
    python scripts/bootstrap_snowflake_trial.py \
        --account xh12345.us-east-1 \
        --warehouse compute_wh \
        --database agent9_trial \
        --schema public \
        --user your_username \
        --password your_password

Environment variables (alternative to flags):
    SNOWFLAKE_ACCOUNT, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE,
    SNOWFLAKE_SCHEMA, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD
"""

import argparse
import logging
import sys
from typing import Optional
import os

try:
    import snowflake.connector
except ImportError:
    print("ERROR: snowflake-connector-python not installed")
    print("Install with: pip install snowflake-connector-python")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class SnowflakeTrialBootstrap:
    """Bootstrap Snowflake trial environment with FI Star Schema sample data."""

    def __init__(
        self,
        account: str,
        warehouse: str,
        database: str,
        schema: str,
        user: str,
        password: str,
    ):
        self.account = account
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.user = user
        self.password = password
        self.conn = None

    def connect(self) -> bool:
        """Connect to Snowflake."""
        try:
            self.conn = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
            )
            logger.info(f"Connected to Snowflake: {self.account}/{self.database}/{self.schema}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from Snowflake."""
        if self.conn:
            self.conn.close()

    def execute(self, sql: str) -> bool:
        """Execute SQL statement."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"SQL error: {e}")
            logger.error(f"SQL: {sql}")
            return False

    def create_schema(self) -> bool:
        """Create schema if not exists."""
        logger.info(f"Creating schema {self.schema}...")
        sql = f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'
        return self.execute(sql)

    def create_dimension_tables(self) -> bool:
        """Create dimension tables."""
        logger.info("Creating dimension tables...")

        # Customers dimension
        sql = f"""
        CREATE OR REPLACE TABLE "{self.schema}".CUSTOMERS (
            CUSTOMER_ID STRING PRIMARY KEY,
            CUSTOMER_NAME STRING NOT NULL,
            CUSTOMER_TYPE STRING,
            REGION STRING,
            COUNTRY STRING,
            CREATED_DATE DATE
        )
        """
        if not self.execute(sql):
            return False

        # Products dimension
        sql = f"""
        CREATE OR REPLACE TABLE "{self.schema}".PRODUCTS (
            PRODUCT_ID STRING PRIMARY KEY,
            PRODUCT_NAME STRING NOT NULL,
            PRODUCT_CATEGORY STRING,
            UNIT_PRICE DECIMAL(10, 2),
            CREATED_DATE DATE
        )
        """
        if not self.execute(sql):
            return False

        # Profit Centers dimension
        sql = f"""
        CREATE OR REPLACE TABLE "{self.schema}".PROFIT_CENTERS (
            PROFIT_CENTER_ID STRING PRIMARY KEY,
            PROFIT_CENTER_NAME STRING NOT NULL,
            MANAGER_NAME STRING,
            REGION STRING,
            CREATED_DATE DATE
        )
        """
        if not self.execute(sql):
            return False

        # GL Accounts dimension
        sql = f"""
        CREATE OR REPLACE TABLE "{self.schema}".GL_ACCOUNTS (
            ACCOUNT_ID STRING PRIMARY KEY,
            ACCOUNT_NAME STRING NOT NULL,
            ACCOUNT_TYPE STRING,
            ACCOUNT_CODE STRING,
            CREATED_DATE DATE
        )
        """
        return self.execute(sql)

    def create_fact_table(self) -> bool:
        """Create fact table."""
        logger.info("Creating fact table...")
        sql = f"""
        CREATE OR REPLACE TABLE "{self.schema}".FINANCIAL_TRANSACTIONS (
            TRANSACTION_ID STRING PRIMARY KEY,
            TRANSACTION_DATE DATE NOT NULL,
            CUSTOMER_ID STRING NOT NULL,
            PRODUCT_ID STRING NOT NULL,
            PROFIT_CENTER_ID STRING NOT NULL,
            ACCOUNT_ID STRING NOT NULL,
            TRANSACTION_AMOUNT DECIMAL(15, 2) NOT NULL,
            TRANSACTION_QUANTITY INT,
            VERSION STRING DEFAULT 'Actual',
            CREATED_DATE DATE,
            FOREIGN KEY (CUSTOMER_ID) REFERENCES "{self.schema}".CUSTOMERS(CUSTOMER_ID),
            FOREIGN KEY (PRODUCT_ID) REFERENCES "{self.schema}".PRODUCTS(PRODUCT_ID),
            FOREIGN KEY (PROFIT_CENTER_ID) REFERENCES "{self.schema}".PROFIT_CENTERS(PROFIT_CENTER_ID),
            FOREIGN KEY (ACCOUNT_ID) REFERENCES "{self.schema}".GL_ACCOUNTS(ACCOUNT_ID)
        )
        """
        return self.execute(sql)

    def load_sample_data(self) -> bool:
        """Load sample data into tables."""
        logger.info("Loading sample data...")

        # Sample customers
        sql = f"""
        INSERT INTO "{self.schema}".CUSTOMERS VALUES
            ('CUST001', 'Acme Corporation', 'Enterprise', 'North America', 'USA', '2024-01-01'),
            ('CUST002', 'Global Tech Ltd', 'Enterprise', 'Europe', 'UK', '2024-01-05'),
            ('CUST003', 'Regional Retail', 'SMB', 'North America', 'Canada', '2024-01-10'),
            ('CUST004', 'Local Services', 'SMB', 'Asia Pacific', 'Australia', '2024-01-15')
        """
        if not self.execute(sql):
            return False

        # Sample products
        sql = f"""
        INSERT INTO "{self.schema}".PRODUCTS VALUES
            ('PROD001', 'Enterprise Software Suite', 'Software', 999.99, '2024-01-01'),
            ('PROD002', 'Cloud Services Pro', 'Services', 1499.99, '2024-01-01'),
            ('PROD003', 'Support & Maintenance', 'Services', 299.99, '2024-01-05'),
            ('PROD004', 'Training Program', 'Training', 2999.99, '2024-01-10')
        """
        if not self.execute(sql):
            return False

        # Sample profit centers
        sql = f"""
        INSERT INTO "{self.schema}".PROFIT_CENTERS VALUES
            ('PC001', 'North America Operations', 'John Smith', 'North America', '2024-01-01'),
            ('PC002', 'EMEA Operations', 'Sarah Jones', 'Europe', '2024-01-05'),
            ('PC003', 'APAC Operations', 'David Chen', 'Asia Pacific', '2024-01-10')
        """
        if not self.execute(sql):
            return False

        # Sample GL accounts
        sql = f"""
        INSERT INTO "{self.schema}".GL_ACCOUNTS VALUES
            ('4000', 'Product Revenue', 'Revenue', '4000', '2024-01-01'),
            ('4100', 'Service Revenue', 'Revenue', '4100', '2024-01-01'),
            ('5000', 'Cost of Goods Sold', 'Expense', '5000', '2024-01-05'),
            ('6000', 'Operating Expenses', 'Expense', '6000', '2024-01-05')
        """
        if not self.execute(sql):
            return False

        # Sample financial transactions
        sql = f"""
        INSERT INTO "{self.schema}".FINANCIAL_TRANSACTIONS VALUES
            ('TXN001', '2024-01-15', 'CUST001', 'PROD001', 'PC001', '4000', 50000.00, 1, 'Actual', '2024-01-15'),
            ('TXN002', '2024-01-16', 'CUST002', 'PROD002', 'PC002', '4100', 75000.00, 1, 'Actual', '2024-01-16'),
            ('TXN003', '2024-01-17', 'CUST001', 'PROD003', 'PC001', '4100', 25000.00, 1, 'Actual', '2024-01-17'),
            ('TXN004', '2024-01-18', 'CUST003', 'PROD002', 'PC001', '4000', 60000.00, 1, 'Actual', '2024-01-18'),
            ('TXN005', '2024-02-01', 'CUST004', 'PROD001', 'PC003', '4000', 45000.00, 1, 'Actual', '2024-02-01'),
            ('TXN006', '2024-02-05', 'CUST002', 'PROD004', 'PC002', '4100', 30000.00, 1, 'Actual', '2024-02-05'),
            ('TXN007', '2024-02-10', 'CUST001', 'PROD002', 'PC001', '4100', 85000.00, 1, 'Actual', '2024-02-10'),
            ('TXN008', '2024-02-15', 'CUST003', 'PROD001', 'PC001', '4000', 55000.00, 1, 'Actual', '2024-02-15')
        """
        return self.execute(sql)

    def create_curated_view(self) -> bool:
        """Create curated FI Star View for Agent9 onboarding."""
        logger.info("Creating curated FI Star View...")
        sql = f"""
        CREATE OR REPLACE VIEW "{self.schema}".FI_STAR_VIEW AS
        SELECT
            ft.TRANSACTION_ID,
            ft.TRANSACTION_DATE,
            YEAR(ft.TRANSACTION_DATE) AS FISCAL_YEAR,
            QUARTER(ft.TRANSACTION_DATE) AS FISCAL_QUARTER,
            MONTH(ft.TRANSACTION_DATE) AS FISCAL_MONTH,
            TO_VARCHAR(ft.TRANSACTION_DATE, 'YYYY-MM') AS FISCAL_YEAR_MONTH,
            ft.CUSTOMER_ID,
            c.CUSTOMER_NAME,
            c.CUSTOMER_TYPE,
            c.REGION,
            ft.PRODUCT_ID,
            p.PRODUCT_NAME,
            p.PRODUCT_CATEGORY,
            ft.PROFIT_CENTER_ID,
            pc.PROFIT_CENTER_NAME,
            ft.ACCOUNT_ID,
            ga.ACCOUNT_NAME,
            ga.ACCOUNT_TYPE,
            ft.TRANSACTION_AMOUNT,
            ft.TRANSACTION_QUANTITY,
            ft.VERSION
        FROM "{self.schema}".FINANCIAL_TRANSACTIONS ft
        JOIN "{self.schema}".CUSTOMERS c ON ft.CUSTOMER_ID = c.CUSTOMER_ID
        JOIN "{self.schema}".PRODUCTS p ON ft.PRODUCT_ID = p.PRODUCT_ID
        JOIN "{self.schema}".PROFIT_CENTERS pc ON ft.PROFIT_CENTER_ID = pc.PROFIT_CENTER_ID
        JOIN "{self.schema}".GL_ACCOUNTS ga ON ft.ACCOUNT_ID = ga.ACCOUNT_ID
        """
        return self.execute(sql)

    def run(self) -> bool:
        """Execute full bootstrap workflow."""
        logger.info("=" * 70)
        logger.info("Snowflake Trial Environment Bootstrap for Agent9 Onboarding")
        logger.info("=" * 70)

        if not self.connect():
            return False

        try:
            if not self.create_schema():
                return False

            if not self.create_dimension_tables():
                return False

            if not self.create_fact_table():
                return False

            if not self.load_sample_data():
                return False

            if not self.create_curated_view():
                return False

            logger.info("=" * 70)
            logger.info("Bootstrap Complete!")
            logger.info("=" * 70)
            logger.info(f"Schema: {self.schema}")
            logger.info(f"Tables: CUSTOMERS, PRODUCTS, PROFIT_CENTERS, GL_ACCOUNTS, FINANCIAL_TRANSACTIONS")
            logger.info(f"View: FI_STAR_VIEW (ready for Agent9 onboarding)")
            logger.info("")
            logger.info("Next Steps:")
            logger.info("1. Use Agent9 Admin Console to register data product")
            logger.info("2. Select view: FI_STAR_VIEW")
            logger.info("3. OnboardingService will auto-extract schema and FK relationships")
            logger.info("4. Review and register contract")
            logger.info("")
            logger.info("IMPORTANT: This schema is temporary for trial/demo purposes.")
            logger.info("Replace with real curated data before production use.")
            logger.info("=" * 70)

            return True
        finally:
            self.disconnect()


def main():
    """Parse arguments and run bootstrap."""
    parser = argparse.ArgumentParser(
        description="Bootstrap Snowflake trial environment for Agent9 onboarding demo"
    )
    parser.add_argument("--account", default=os.getenv("SNOWFLAKE_ACCOUNT"), help="Snowflake account")
    parser.add_argument("--warehouse", default=os.getenv("SNOWFLAKE_WAREHOUSE"), help="Warehouse name")
    parser.add_argument("--database", default=os.getenv("SNOWFLAKE_DATABASE"), help="Database name")
    parser.add_argument("--schema", default=os.getenv("SNOWFLAKE_SCHEMA", "public"), help="Schema name")
    parser.add_argument("--user", default=os.getenv("SNOWFLAKE_USER"), help="Username")
    parser.add_argument("--password", default=os.getenv("SNOWFLAKE_PASSWORD"), help="Password")

    args = parser.parse_args()

    # Validate required arguments
    if not all([args.account, args.warehouse, args.database, args.user, args.password]):
        logger.error("Missing required arguments. Provide via flags or environment variables.")
        parser.print_help()
        sys.exit(1)

    bootstrap = SnowflakeTrialBootstrap(
        account=args.account,
        warehouse=args.warehouse,
        database=args.database,
        schema=args.schema,
        user=args.user,
        password=args.password,
    )

    success = bootstrap.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
