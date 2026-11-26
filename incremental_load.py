
import pandas as pd
import pyodbc
import logging
from pathlib import Path

from logging_config import log_start, log_success, log_error

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "incremental"

SERVER = "depi-ecommerce-server-2026.database.windows.net"
DATABASE = "ECommerceDataWarehouse"
USERNAME = "za30612200107519@depi.eui.edu.eg"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Authentication=ActiveDirectoryInteractive;"
    f"UID={USERNAME};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

TABLES = {
    "crm_cust_info": ("crm_cust_info.csv", ["cst_id"]),
    "crm_prd_info": ("crm_prd_info.csv", ["prd_id"]),
    "crm_sales_details": (
        "crm_sales_details.csv",
        ["sls_ord_num", "sls_prd_key"]
    ),
    "erp_cust_az12": ("erp_cust_az12.csv", ["cid"]),
    "erp_loc_a101": ("erp_loc_a101.csv", ["cid"]),
    "erp_px_cat_g1v2": ("erp_px_cat_g1v2.csv", ["id"]),
}


def load_incremental_table(cursor, conn, table_name, file_name, keys):
    stage = f"Incremental Loading - {table_name}"
    log_start(stage)

    file_path = DATA_DIR / file_name

    if not file_path.exists():
        print(f"[SKIP] {file_name} not found")
        return

    df = pd.read_csv(file_path)

    if df.empty:
        print(f"[SKIP] {file_name} is empty")
        return

    if not set(keys).issubset(df.columns):
        raise ValueError(f"Missing key columns in {file_name}")

    if df[keys].isnull().any().any():
        raise ValueError(f"Null primary key found in {file_name}")

    if df.duplicated(subset=keys).any():
        raise ValueError(f"Duplicate keys found in {file_name}")

    columns = list(df.columns)

    cursor.execute(
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = 'bronze' AND TABLE_NAME = ?",
        table_name
    )

    db_columns = {row[0] for row in cursor.fetchall()}

    if set(columns) != db_columns:
        raise ValueError(f"CSV columns do not match bronze.{table_name}")

    cursor.execute(f"SELECT * FROM bronze.{table_name}")

    existing_rows = cursor.fetchall()
    existing_columns = [column[0] for column in cursor.description]

    existing_df = pd.DataFrame.from_records(
        existing_rows,
        columns=existing_columns
    )

    if existing_df.empty:
        new_df = df.copy()
    else:
        existing_keys = existing_df[keys].astype(str).agg("|".join, axis=1)
        incoming_keys = df[keys].astype(str).agg("|".join, axis=1)

        new_df = df[~incoming_keys.isin(set(existing_keys))].copy()

    if new_df.empty:
        log_success(stage, 0)
        print(f"[PASS] {table_name}: No new records")
        return

    placeholders = ", ".join(["?"] * len(columns))
    column_names = ", ".join(f"[{col}]" for col in columns)

    sql = (
        f"INSERT INTO bronze.{table_name} "
        f"({column_names}) VALUES ({placeholders})"
    )

    rows = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in new_df.itertuples(index=False, name=None)
    ]

    cursor.fast_executemany = True
    cursor.executemany(sql, rows)

    conn.commit()

    log_success(stage, len(rows))
    print(f"[PASS] {table_name}: Inserted {len(rows)} new rows")


def main():
    if not DATA_DIR.exists():
        print("Incremental folder not found.")
        return

    csv_files = list(DATA_DIR.glob("*.csv"))

    if not csv_files:
        print("No incremental files found. Nothing to load.")
        return

    conn = None
    cursor = None

    log_start("Incremental Loading Pipeline")

    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        for table_name, (file_name, keys) in TABLES.items():
            load_incremental_table(
                cursor,
                conn,
                table_name,
                file_name,
                keys
            )

        log_success("Incremental Loading Pipeline")
        print("\nIncremental loading completed.")

    except Exception as error:
        if conn:
            conn.rollback()

        log_error("Incremental Loading Pipeline", error)
        print(f"\nIncremental loading failed: {error}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()