import pandas as pd
import os
import logging
from pathlib import Path


# =========================================================
# 1. PROJECT CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

RAW_FOLDER = BASE_DIR / "data" / "raw"
PROCESSED_FOLDER = BASE_DIR / "data" / "processed"
LOG_FOLDER = BASE_DIR / "logs"

LOG_FOLDER.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. LOGGING CONFIGURATION
# =========================================================

logging.basicConfig(
    filename=LOG_FOLDER / "pipeline.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
    force=True
)

logger = logging.getLogger("DataQuality")


# =========================================================
# 3. EXPECTED RAW FILES
# =========================================================

raw_files = {
    "crm_cust_info.csv": 18494,
    "crm_prd_info.csv": 397,
    "crm_sales_details.csv": 60398,
    "erp_cust_az12.csv": 18484,
    "erp_loc_a101.csv": 18484,
    "erp_px_cat_g1v2.csv": 37,
    "products_api.csv": None
}


# =========================================================
# 4. PROCESSED FILES
# =========================================================

customer_file = PROCESSED_FOLDER / "dim_customer.csv"
product_file = PROCESSED_FOLDER / "dim_product.csv"
sales_file = PROCESSED_FOLDER / "fact_sales.csv"


# =========================================================
# 5. GENERAL DATA QUALITY CHECKS
# =========================================================

def check_file(file_path, expected_rows=None):

    file_name = file_path.name

    print("\n" + "=" * 60)
    print(f"FILE: {file_name}")
    print("=" * 60)

    logger.info(f"Starting file check: {file_name}")

    if not file_path.exists():

        print("STATUS: FILE NOT FOUND")

        logger.warning(f"{file_name} - File not found")

        return None

    try:

        df = pd.read_csv(file_path)

        rows = len(df)
        columns = len(df.columns)

        missing_values = df.isnull().sum()
        total_missing = int(missing_values.sum())

        duplicates = int(df.duplicated().sum())

        print(f"Rows: {rows}")
        print(f"Columns: {columns}")

        print("\nColumn Names:")
        print(list(df.columns))

        print("\nMissing Values:")

        if total_missing == 0:

            print("No missing values found.")

        else:

            print(missing_values[missing_values > 0])

        print(f"\nTotal Missing Values: {total_missing}")

        print(f"Duplicate Rows: {duplicates}")

        logger.info(
            f"{file_name} | Rows: {rows} | "
            f"Columns: {columns} | "
            f"Missing: {total_missing} | "
            f"Duplicates: {duplicates}"
        )

        # Row count validation

        if expected_rows is not None:

            if rows == expected_rows:

                print("Row Count Check: PASSED")

                logger.info(
                    f"{file_name} - Row count check PASSED"
                )

            else:

                print(
                    f"Row Count Check: FAILED "
                    f"(Expected: {expected_rows})"
                )

                logger.warning(
                    f"{file_name} - Row count mismatch"
                )

        # Duplicate validation

        if duplicates == 0:

            print("Duplicate Check: PASSED")

        else:

            print("Duplicate Check: WARNING")

            logger.warning(
                f"{file_name} - Duplicate records found: {duplicates}"
            )

        # Missing values validation

        if total_missing == 0:

            print("Missing Values Check: PASSED")

        else:

            print("Missing Values Check: WARNING")

            logger.warning(
                f"{file_name} - Missing values: {total_missing}"
            )

        return df

    except Exception as e:

        print(f"ERROR: {e}")

        logger.error(
            f"{file_name} - File check failed: {e}"
        )

        return None


# =========================================================
# 6. RAW DATA QUALITY CHECK
# =========================================================

def check_raw_data():

    print("\n\n")
    print("#" * 60)
    print("RAW DATA QUALITY CHECK")
    print("#" * 60)

    logger.info("RAW DATA QUALITY CHECK STARTED")

    if not RAW_FOLDER.exists():

        print("\nRaw folder not found!")

        logger.warning(
            f"Raw folder not found: {RAW_FOLDER}"
        )

        return

    for file_name, expected_rows in raw_files.items():

        file_path = RAW_FOLDER / file_name

        check_file(
            file_path,
            expected_rows
        )

    logger.info("RAW DATA QUALITY CHECK COMPLETED")


# =========================================================
# 7. GOLD DATA QUALITY CHECK
# =========================================================

def check_gold_data():

    print("\n\n")
    print("#" * 60)
    print("GOLD DATA QUALITY CHECK")
    print("#" * 60)

    logger.info("GOLD DATA QUALITY CHECK STARTED")

    customer = check_file(customer_file)

    product = check_file(product_file)

    sales = check_file(sales_file)

    logger.info("GOLD DATA QUALITY CHECK COMPLETED")

    return customer, product, sales


# =========================================================
# 8. PRIMARY KEY VALIDATION
# =========================================================

def check_primary_keys(customer, product):

    print("\n\n")
    print("#" * 60)
    print("PRIMARY KEY VALIDATION")
    print("#" * 60)

    logger.info("PRIMARY KEY VALIDATION STARTED")

    if customer is None or product is None:

        print("Cannot perform primary key validation.")

        logger.warning(
            "Primary key validation skipped: missing files"
        )

        return

    # Customer Primary Key

    customer_key = "cst_id"

    if customer_key in customer.columns:

        null_customers = int(
            customer[customer_key].isna().sum()
        )

        duplicate_customers = int(
            customer[customer_key].duplicated().sum()
        )

        print("\nCustomer ID:")

        print(f"NULL Values: {null_customers}")

        print(f"Duplicate Keys: {duplicate_customers}")

        if null_customers == 0 and duplicate_customers == 0:

            print("Customer Primary Key: PASSED")

            logger.info("Customer Primary Key PASSED")

        else:

            print("Customer Primary Key: FAILED")

            logger.warning("Customer Primary Key FAILED")

    # Product Primary Key

    product_key = "product_key"

    if product_key in product.columns:

        null_products = int(
            product[product_key].isna().sum()
        )

        duplicate_products = int(
            product[product_key].duplicated().sum()
        )

        print("\nProduct Key:")

        print(f"NULL Values: {null_products}")

        print(f"Duplicate Keys: {duplicate_products}")

        if null_products == 0 and duplicate_products == 0:

            print("Product Primary Key: PASSED")

            logger.info("Product Primary Key PASSED")

        else:

            print("Product Primary Key: FAILED")

            logger.warning("Product Primary Key FAILED")

    logger.info("PRIMARY KEY VALIDATION COMPLETED")


# =========================================================
# 9. REFERENTIAL INTEGRITY VALIDATION
# =========================================================

def check_referential_integrity(customer, product, sales):

    print("\n\n")
    print("#" * 60)
    print("REFERENTIAL INTEGRITY VALIDATION")
    print("#" * 60)

    logger.info("REFERENTIAL INTEGRITY CHECK STARTED")

    if customer is None or product is None or sales is None:

        print("Cannot perform relationship validation.")

        logger.warning(
            "Referential integrity check skipped: missing files"
        )

        return

    # Required columns

    required_columns = {
        "customer": (customer, "cst_id"),
        "product": (product, "product_key"),
        "sales_customer": (sales, "sls_cust_id"),
        "sales_product": (sales, "sls_prd_key")
    }

    for name, (df, column) in required_columns.items():

        if column not in df.columns:

            print(f"Missing required column: {column}")

            logger.error(
                f"Referential integrity check failed: "
                f"missing column {column}"
            )

            return

    # Normalize customer IDs for comparison

    customer_ids = pd.to_numeric(
        customer["cst_id"],
        errors="coerce"
    )

    sales_customer_ids = pd.to_numeric(
        sales["sls_cust_id"],
        errors="coerce"
    )

    valid_customer_ids = set(
        customer_ids.dropna()
    )

    # Normalize product keys

    product_keys = set(
        product["product_key"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    sales_product_keys = (
        sales["sls_prd_key"]
        .astype("string")
        .str.strip()
    )

    # Check missing customer references

    missing_customers = (
        sales_customer_ids.notna()
        & ~sales_customer_ids.isin(valid_customer_ids)
    ).sum()

    null_customer_references = int(
        sales_customer_ids.isna().sum()
    )

    print("\nCustomer Relationship:")

    print(
        f"Missing Customer References: {missing_customers}"
    )

    print(
        f"NULL Customer References: {null_customer_references}"
    )

    if missing_customers == 0 and null_customer_references == 0:

        print("Customer Relationship: PASSED")

        logger.info("Customer Relationship PASSED")

    else:

        print("Customer Relationship: FAILED")

        logger.warning(
            f"Customer relationship issues: {missing_customers}"
        )

    # Check missing product references

    missing_products = (
        sales_product_keys.notna()
        & ~sales_product_keys.isin(product_keys)
    ).sum()

    null_product_references = int(
        sales_product_keys.isna().sum()
    )

    print("\nProduct Relationship:")

    print(
        f"Missing Product References: {missing_products}"
    )

    print(
        f"NULL Product References: {null_product_references}"
    )

    if missing_products == 0 and null_product_references == 0:

        print("Product Relationship: PASSED")

        logger.info("Product Relationship PASSED")

    else:

        print("Product Relationship: FAILED")

        logger.warning(
            f"Product relationship issues: {missing_products}"
        )

    logger.info("REFERENTIAL INTEGRITY CHECK COMPLETED")


# =========================================================
# 10. MAIN EXECUTION
# =========================================================

def main():

    print("\n")
    print("*" * 60)
    print("ECOMMERCE DATA QUALITY VALIDATION")
    print("*" * 60)

    logger.info("=" * 60)

    logger.info("ECOMMERCE DATA QUALITY PIPELINE STARTED")

    # Step 1: Raw validation

    check_raw_data()

    # Step 2: Gold validation

    customer, product, sales = check_gold_data()

    # Step 3: Primary key validation

    check_primary_keys(
        customer,
        product
    )

    # Step 4: Referential integrity

    check_referential_integrity(
        customer,
        product,
        sales
    )

    print("\n")
    print("*" * 60)
    print("DATA QUALITY VALIDATION COMPLETED")
    print("*" * 60)

    logger.info("ECOMMERCE DATA QUALITY PIPELINE COMPLETED")

    logger.info("=" * 60)


# =========================================================
# 11. PROGRAM ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()