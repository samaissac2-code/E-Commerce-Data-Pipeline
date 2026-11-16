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

# Tables and their candidate primary keys
tables = {
    "crm_cust_info": ["cst_id"],
    "crm_prd_info": ["prd_id"],
    "crm_sales_details": ["sls_ord_num", "sls_prd_key"],
    "erp_cust_az12": ["cid"],
    "erp_loc_a101": ["cid"],
    "erp_px_cat_g1v2": ["id"]
}

conn = None
cursor = None

log_start("Silver Validation")

try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    all_passed = True

    for table, keys in tables.items():

        # Total rows
        cursor.execute(f"SELECT COUNT(*) FROM silver.{table}")
        total = cursor.fetchone()[0]

        # Check NULL keys
        null_condition = " OR ".join(
            f"[{col}] IS NULL" for col in keys
        )

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM silver.{table}
            WHERE {null_condition}
            """
        )
        nulls = cursor.fetchone()[0]

        # Check duplicate key combinations
        group_columns = ", ".join(
            f"[{col}]" for col in keys
        )

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {group_columns}
                FROM silver.{table}
                GROUP BY {group_columns}
                HAVING COUNT(*) > 1
            ) AS duplicates
            """
        )

        duplicates = cursor.fetchone()[0]

        status = (
            "PASS"
            if nulls == 0 and duplicates == 0
            else "WARNING"
        )

        if status == "WARNING":
            all_passed = False

        print(
            f"[{status}] {table} | "
            f"Rows: {total} | "
            f"Null Keys: {nulls} | "
            f"Duplicate Keys: {duplicates}"
        )

    if all_passed:
        log_success("Silver Validation")
        print("\nAll Silver tables passed validation!")
    else:
        print("\nSilver validation completed with warnings.")

except Exception as error:
    log_error("Silver Validation", error)
    print(f"\nValidation failed: {error}")

finally:
    if cursor:
        cursor.close()

    if conn:
        conn.close()