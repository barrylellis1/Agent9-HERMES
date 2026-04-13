#!/usr/bin/env python3
"""
Bootstrap Databricks Trial Environment for Agent9 Onboarding Demo

This utility creates a minimal FI Star Schema in a Databricks Community Edition
workspace with sample data, enabling validation of the OnboardingService discovery
and analysis workflow.

IMPORTANT: This is a temporary bootstrap utility for trial/demo purposes.
It should be deprecated once customers have real curated data.

Usage:
    python scripts/bootstrap_databricks_trial.py \
        --server-hostname adb-123.cloud.databricks.com \
        --http-path /sql/1.0/warehouses/abc123 \
        --token dapi... \
        --catalog main \
        --schema default

Environment variables (alternative to flags):
    DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN,
    DATABRICKS_CATALOG, DATABRICKS_SCHEMA
"""

import argparse
import logging
import sys
from typing import Optional
import os

try:
    from databricks import sql
except ImportError:
    print("ERROR: databricks-sql-connector not installed")
    print("Install with: pip install databricks-sql-connector")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class DatabricksTrialBootstrap:
    """Bootstrap Databricks trial environment with FI Star Schema sample data."""

    def __init__(
        self,
        server_hostname: str,
        http_path: str,
        token: str,
        catalog: str,
        schema: str,
    ):
        self.server_hostname = server_hostname
        self.http_path = http_path
        self.token = token
        self.catalog = catalog
        self.schema = schema
        self.conn = None

    def connect(self) -> bool:
        """Connect to Databricks."""
        try:
            self.conn = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                personal_access_token=self.token,
            )
            logger.info(f"Connected to Databricks: {self.server_hostname}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from Databricks."""
        if self.conn:
            self.conn.close()

    def execute(self, sql_stmt: str) -> bool:
        """Execute SQL statement."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_stmt)
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"SQL error: {e}")
            logger.error(f"SQL: {sql_stmt}")
            return False

    def create_schema(self) -> bool:
        """Create schema if not exists."""
        logger.info(f"Creating schema {self.catalog}.{self.schema}...")
        sql_stmt = f"CREATE SCHEMA IF NOT EXISTS `{self.catalog}`.`{self.schema}`"
        return self.execute(sql_stmt)

    def create_dimension_tables(self) -> bool:
        """Create dimension tables."""
        logger.info("Creating dimension tables...")

        # Customers dimension
        sql_stmt = f"""
        CREATE TABLE IF NOT EXISTS `{self.catalog}`.`{self.schema}`.customers (
            customer_id STRING NOT NULL PRIMARY KEY,
            customer_name STRING NOT NULL,
            customer_type STRING,
            region STRING,
            country STRING,
            created_date DATE
        )
        """
        if not self.execute(sql_stmt):
            return False

        # Products dimension
        sql_stmt = f"""
        CREATE TABLE IF NOT EXISTS `{self.catalog}`.`{self.schema}`.products (
            product_id STRING NOT NULL PRIMARY KEY,
            product_name STRING NOT NULL,
            product_category STRING,
            unit_price DECIMAL(10, 2),
            created_date DATE
        )
        """
        if not self.execute(sql_stmt):
            return False

        # Profit Centers dimension
        sql_stmt = f"""
        CREATE TABLE IF NOT EXISTS `{self.catalog}`.`{self.schema}`.profit_centers (
            profit_center_id STRING NOT NULL PRIMARY KEY,
            profit_center_name STRING NOT NULL,
            manager_name STRING,
            region STRING,
            created_date DATE
        )
        """
        if not self.execute(sql_stmt):
            return False

        # GL Accounts dimension
        sql_stmt = f"""
        CREATE TABLE IF NOT EXISTS `{self.catalog}`.`{self.schema}`.gl_accounts (
            account_id STRING NOT NULL PRIMARY KEY,
            account_name STRING NOT NULL,
            account_type STRING,
            account_code STRING,
            created_date DATE
        )
        """
        return self.execute(sql_stmt)

    def create_fact_table(self) -> bool:
        """Create fact table."""
        logger.info("Creating fact table...")
        sql_stmt = f"""
        CREATE TABLE IF NOT EXISTS `{self.catalog}`.`{self.schema}`.financial_transactions (
            transaction_id STRING NOT NULL PRIMARY KEY,
            transaction_date DATE NOT NULL,
            customer_id STRING NOT NULL,
            product_id STRING NOT NULL,
            profit_center_id STRING NOT NULL,
            account_id STRING NOT NULL,
            transaction_amount DECIMAL(15, 2) NOT NULL,
            transaction_quantity INT,
            version STRING DEFAULT 'Actual',
            created_date DATE
        )
        """
        return self.execute(sql_stmt)

    def load_sample_data(self) -> bool:
        """Load sample data into tables."""
        logger.info("Loading sample data...")

        # Sample customers
        sql_stmt = f"""
        INSERT INTO `{self.catalog}`.`{self.schema}`.customers VALUES
            ('CUST001', 'Acme Corporation', 'Enterprise', 'North America', 'USA', '2024-01-01'),
            ('CUST002', 'Global Tech Ltd', 'Enterprise', 'Europe', 'UK', '2024-01-05'),
            ('CUST003', 'Regional Retail', 'SMB', 'North America', 'Canada', '2024-01-10'),
            ('CUST004', 'Local Services', 'SMB', 'Asia Pacific', 'Australia', '2024-01-15')
        """
        if not self.execute(sql_stmt):
            return False

        # Sample products
        sql_stmt = f"""
        INSERT INTO `{self.catalog}`.`{self.schema}`.products VALUES
            ('PROD001', 'Enterprise Software Suite', 'Software', 999.99, '2024-01-01'),
            ('PROD002', 'Cloud Services Pro', 'Services', 1499.99, '2024-01-01'),
            ('PROD003', 'Support & Maintenance', 'Services', 299.99, '2024-01-05'),
            ('PROD004', 'Training Program', 'Training', 2999.99, '2024-01-10')
        """
        if not self.execute(sql_stmt):
            return False

        # Sample profit centers
        sql_stmt = f"""
        INSERT INTO `{self.catalog}`.`{self.schema}`.profit_centers VALUES
            ('PC001', 'North America Operations', 'John Smith', 'North America', '2024-01-01'),
            ('PC002', 'EMEA Operations', 'Sarah Jones', 'Europe', '2024-01-05'),
            ('PC003', 'APAC Operations', 'David Chen', 'Asia Pacific', '2024-01-10')
        """
        if not self.execute(sql_stmt):
            return False

        # Sample GL accounts
        sql_stmt = f"""
        INSERT INTO `{self.catalog}`.`{self.schema}`.gl_accounts VALUES
            ('4000', 'Product Revenue', 'Revenue', '4000', '2024-01-01'),
            ('4100', 'Service Revenue', 'Revenue', '4100', '2024-01-01'),
            ('5000', 'Cost of Goods Sold', 'Expense', '5000', '2024-01-05'),
            ('6000', 'Operating Expenses', 'Expense', '6000', '2024-01-05')
        """
        if not self.execute(sql_stmt):
            return False

        # Sample financial transactions
        sql_stmt = f"""
        INSERT INTO `{self.catalog}`.`{self.schema}`.financial_transactions VALUES
            ('TXN001', '2024-01-15', 'CUST001', 'PROD001', 'PC001', '4000', 50000.00, 1, 'Actual', '2024-01-15'),
            ('TXN002', '2024-01-16', 'CUST002', 'PROD002', 'PC002', '4100', 75000.00, 1, 'Actual', '2024-01-16'),
            ('TXN003', '2024-01-17', 'CUST001', 'PROD003', 'PC001', '4100', 25000.00, 1, 'Actual', '2024-01-17'),
            ('TXN004', '2024-01-18', 'CUST003', 'PROD002', 'PC001', '4000', 60000.00, 1, 'Actual', '2024-01-18'),
            ('TXN005', '2024-02-01', 'CUST004', 'PROD001', 'PC003', '4000', 45000.00, 1, 'Actual', '2024-02-01'),
            ('TXN006', '2024-02-05', 'CUST002', 'PROD004', 'PC002', '4100', 30000.00, 1, 'Actual', '2024-02-05'),
            ('TXN007', '2024-02-10', 'CUST001', 'PROD002', 'PC001', '4100', 85000.00, 1, 'Actual', '2024-02-10'),
            ('TXN008', '2024-02-15', 'CUST003', 'PROD001', 'PC001', '4000', 55000.00, 1, 'Actual', '2024-02-15')
        """
        return self.execute(sql_stmt)

    def create_curated_view(self) -> bool:
        """Create curated FI Star View for Agent9 onboarding."""
        logger.info("Creating curated FI Star View...")
        sql_stmt = f"""
        CREATE OR REPLACE VIEW `{self.catalog}`.`{self.schema}`.fi_star_view AS
        SELECT
            ft.transaction_id,
            ft.transaction_date,
            YEAR(ft.transaction_date) AS fiscal_year,
            QUARTER(ft.transaction_date) AS fiscal_quarter,
            MONTH(ft.transaction_date) AS fiscal_month,
            DATE_FORMAT(ft.transaction_date, 'yyyy-MM') AS fiscal_year_month,
            ft.customer_id,
            c.customer_name,
            c.customer_type,
            c.region,
            ft.product_id,
            p.product_name,
            p.product_category,
            ft.profit_center_id,
            pc.profit_center_name,
            ft.account_id,
            ga.account_name,
            ga.account_type,
            ft.transaction_amount,
            ft.transaction_quantity,
            ft.version
        FROM `{self.catalog}`.`{self.schema}`.financial_transactions ft
        JOIN `{self.catalog}`.`{self.schema}`.customers c ON ft.customer_id = c.customer_id
        JOIN `{self.catalog}`.`{self.schema}`.products p ON ft.product_id = p.product_id
        JOIN `{self.catalog}`.`{self.schema}`.profit_centers pc ON ft.profit_center_id = pc.profit_center_id
        JOIN `{self.catalog}`.`{self.schema}`.gl_accounts ga ON ft.account_id = ga.account_id
        """
        return self.execute(sql_stmt)

    def run(self) -> bool:
        """Execute full bootstrap workflow."""
        logger.info("=" * 70)
        logger.info("Databricks Trial Environment Bootstrap for Agent9 Onboarding")
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
            logger.info(f"Catalog.Schema: {self.catalog}.{self.schema}")
            logger.info(f"Tables: customers, products, profit_centers, gl_accounts, financial_transactions")
            logger.info(f"View: fi_star_view (ready for Agent9 onboarding)")
            logger.info("")
            logger.info("Next Steps:")
            logger.info("1. Use Agent9 Admin Console to register data product")
            logger.info("2. Select view: fi_star_view")
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
        description="Bootstrap Databricks trial environment for Agent9 onboarding demo"
    )
    parser.add_argument(
        "--server-hostname",
        default=os.getenv("DATABRICKS_HOST"),
        help="Databricks server hostname",
    )
    parser.add_argument(
        "--http-path",
        default=os.getenv("DATABRICKS_HTTP_PATH"),
        help="Databricks HTTP path",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("DATABRICKS_TOKEN"),
        help="Databricks personal access token",
    )
    parser.add_argument(
        "--catalog",
        default=os.getenv("DATABRICKS_CATALOG", "main"),
        help="Catalog name",
    )
    parser.add_argument(
        "--schema",
        default=os.getenv("DATABRICKS_SCHEMA", "default"),
        help="Schema name",
    )

    args = parser.parse_args()

    # Validate required arguments
    if not all([args.server_hostname, args.http_path, args.token]):
        logger.error("Missing required arguments. Provide via flags or environment variables.")
        parser.print_help()
        sys.exit(1)

    bootstrap = DatabricksTrialBootstrap(
        server_hostname=args.server_hostname,
        http_path=args.http_path,
        token=args.token,
        catalog=args.catalog,
        schema=args.schema,
    )

    success = bootstrap.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
