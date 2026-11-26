import os
import pandas as pd
import pyodbc

from logging_config import log_start, log_success, log_error

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

log_start("Bronze Loading")

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    for table_name, file_name in tables.items():

        stage = f"Bronze Loading - {table_name}"

        log_start(stage)

        file_path = os.path.join(data_path, file_name)

        df = pd.read_csv(file_path)

        cursor.execute(
            f"SELECT COUNT(*) FROM bronze.{table_name}"
        )

        existing_rows = cursor.fetchone()[0]

        if existing_rows > 0:
            raise Exception(
                f"Table bronze.{table_name} is not empty."
            )

        columns = list(df.columns)

        placeholders = ", ".join(["?"] * len(columns))
        column_names = ", ".join(
            f"[{col}]" for col in columns
        )

        sql = (
            f"INSERT INTO bronze.{table_name} "
            f"({column_names}) VALUES ({placeholders})"
        )

        rows = [
            tuple(
                None if pd.isna(value) else value
                for value in row
            )
            for row in df.itertuples(index=False, name=None)
        ]

        cursor.fast_executemany = True

        cursor.executemany(sql, rows)

        conn.commit()

        cursor.execute(
            f"SELECT COUNT(*) FROM bronze.{table_name}"
        )

        loaded_rows = cursor.fetchone()[0] - existing_rows

        log_success(stage, loaded_rows)

        print(
            f"Loaded {loaded_rows} rows into bronze.{table_name}"
        )

    log_success("Bronze Loading - All Tables")

except Exception as e:

    if conn:
        conn.rollback()

    log_error("Bronze Loading", e)

    print("\nLoading failed:")
    print(e)

finally:

    if cursor:
        cursor.close()

    if conn:
        conn.close()