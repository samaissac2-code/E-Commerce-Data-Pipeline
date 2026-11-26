import os
import pandas as pd
import pyodbc

from logging_config import log_start, log_success, log_error

# Azure SQL Configuration
server = "depi-ecommerce-server-2026.database.windows.net"
database = "ECommerceDataWarehouse"
username = "za30612200107519@depi.eui.edu.eg"

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Authentication=ActiveDirectoryInteractive;"
    f"UID={username};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

# Raw data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, "data", "raw")

tables = {
    "crm_cust_info": "crm_cust_info.csv",
    "crm_prd_info": "crm_prd_info.csv",
    "crm_sales_details": "crm_sales_details.csv",
    "erp_cust_az12": "erp_cust_az12.csv",
    "erp_loc_a101": "erp_loc_a101.csv",
    "erp_px_cat_g1v2": "erp_px_cat_g1v2.csv"
}

conn = None
cursor = None

log_start("Bronze Validation")

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    all_passed = True

    for table_name, file_name in tables.items():

        stage = f"Bronze Validation - {table_name}"
        log_start(stage)

        file_path = os.path.join(data_path, file_name)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        df = pd.read_csv(file_path)
        source_rows = len(df)

        cursor.execute(
            f"SELECT COUNT(*) FROM bronze.{table_name}"
        )

        bronze_rows = cursor.fetchone()[0]

        if source_rows == bronze_rows:

            log_success(stage, bronze_rows)

            print(
                f"[PASS] {table_name} | "
                f"CSV: {source_rows} | "
                f"Bronze: {bronze_rows}"
            )

        else:

            all_passed = False

            error_message = (
                f"Row count mismatch | "
                f"CSV: {source_rows} | "
                f"Bronze: {bronze_rows}"
            )

            log_error(stage, error_message)

            print(
                f"[FAIL] {table_name} | "
                f"CSV: {source_rows} | "
                f"Bronze: {bronze_rows}"
            )

    if all_passed:
        log_success("Bronze Validation - All Tables")
        print("\nAll Bronze tables passed validation!")

    else:
        log_error(
            "Bronze Validation - All Tables",
            "One or more tables have row count mismatches."
        )
        print("\nBronze validation completed with errors.")

except Exception as e:

    log_error("Bronze Validation", e)

    print("\nValidation failed:")
    print(e)

finally:

    if cursor:
        cursor.close()

    if conn:
        conn.close()