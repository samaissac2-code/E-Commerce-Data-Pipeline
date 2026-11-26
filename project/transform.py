import os
import pandas as pd
import numpy as np

# Set working directory to the folder where this script is saved
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Output folder
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 50)
print("Starting Data Cleaning & Transformation...")
print("=" * 50)


# ---------------------------------------------------------
# A. CLEANING CUSTOMERS (Dim Customer)
# ---------------------------------------------------------

print("\n[1/3] Processing Customers Data...")

crm_cust = pd.read_csv("data/raw/crm_cust_info.csv")
erp_cust = pd.read_csv("data/raw/erp_cust_az12.csv")
erp_loc = pd.read_csv("data/raw/erp_loc_a101.csv")

# Clean CRM customers
crm_cust = crm_cust.dropna(subset=['cst_id'])
crm_cust['cst_id'] = crm_cust['cst_id'].astype(int)

crm_cust['cst_firstname'] = crm_cust['cst_firstname'].str.strip()
crm_cust['cst_lastname'] = crm_cust['cst_lastname'].str.strip()

crm_cust = crm_cust.sort_values('cst_create_date')
crm_cust = crm_cust.drop_duplicates(
    subset=['cst_id'],
    keep='last'
)

# Standardize ERP customer keys
erp_cust['cst_key'] = (
    erp_cust['CID']
    .astype(str)
    .str.replace('NAS', '', regex=False)
    .str.strip()
)

# Standardize gender
gen = erp_cust['GEN'].str.strip().str.upper()

erp_cust['GEN'] = gen.map({
    'MALE': 'M',
    'M': 'M',
    'FEMALE': 'F',
    'F': 'F'
}).fillna('U')

# Clean birth dates
erp_cust['BDATE'] = pd.to_datetime(
    erp_cust['BDATE'],
    errors='coerce'
)

erp_cust.loc[
    erp_cust['BDATE'] > pd.Timestamp.today(),
    'BDATE'
] = pd.NaT

# Standardize location keys
erp_loc['cst_key'] = (
    erp_loc['CID']
    .astype(str)
    .str.replace('-', '', regex=False)
    .str.strip()
)

# Standardize country names
erp_loc['CNTRY'] = (
    erp_loc['CNTRY']
    .str.strip()
    .replace({
        'USA': 'United States',
        'US': 'United States',
        'DE': 'Germany',
        '': np.nan
    })
    .fillna('Unknown')
)

# Merge CRM and ERP data
dim_customer = crm_cust.merge(
    erp_cust[['cst_key', 'BDATE', 'GEN']],
    on='cst_key',
    how='left'
)

dim_customer = dim_customer.merge(
    erp_loc[['cst_key', 'CNTRY']],
    on='cst_key',
    how='left'
)

# Fill missing values
dim_customer['cst_gndr'] = (
    dim_customer['cst_gndr']
    .fillna(dim_customer['GEN'])
    .fillna('U')
)

dim_customer['CNTRY'] = (
    dim_customer['CNTRY'].fillna('Unknown')
)

dim_customer = dim_customer.drop(columns=['GEN'])

# Save customer dimension
customer_path = os.path.join(
    OUTPUT_DIR,
    "dim_customer.csv"
)

dim_customer.to_csv(customer_path, index=False)

print(
    f"Saved dim_customer.csv | Shape: {dim_customer.shape}"
)


# ---------------------------------------------------------
# B. CLEANING PRODUCTS (Dim Product)
# ---------------------------------------------------------

print("\n[2/3] Processing Products Data...")

crm_prd = pd.read_csv("data/raw/crm_prd_info.csv")
erp_px = pd.read_csv("data/raw/erp_px_cat_g1v2.csv")

# Fill missing product costs
crm_prd['prd_cost'] = crm_prd['prd_cost'].fillna(0)

# Map product lines
line_map = {
    'R': 'Road',
    'M': 'Mountain',
    'T': 'Touring',
    'S': 'Other Sales'
}

crm_prd['prd_line_desc'] = (
    crm_prd['prd_line']
    .str.strip()
    .map(line_map)
    .fillna('Unknown')
)

# Extract category code and product key
crm_prd['cat_code'] = (
    crm_prd['prd_key']
    .str[:5]
    .str.replace('-', '_', regex=False)
)

crm_prd['product_key'] = crm_prd['prd_key'].str[6:]

# Convert product start dates
crm_prd['prd_start_dt'] = pd.to_datetime(
    crm_prd['prd_start_dt']
)

# Calculate product end dates
crm_prd = crm_prd.sort_values(
    ['product_key', 'prd_start_dt']
)

next_start = (
    crm_prd.groupby('product_key')['prd_start_dt']
    .shift(-1)
)

crm_prd['prd_end_dt'] = (
    next_start - pd.Timedelta(days=1)
)

# Keep current product versions
crm_prd = crm_prd[
    crm_prd['prd_end_dt'].isna()
]

# Merge product categories
dim_product = crm_prd.merge(
    erp_px,
    left_on='cat_code',
    right_on='ID',
    how='left'
)

# Rename category columns
dim_product = dim_product.rename(columns={
    'CAT': 'category',
    'SUBCAT': 'subcategory',
    'MAINTENANCE': 'maintenance'
})

# Fill missing category values
dim_product[
    ['category', 'subcategory', 'maintenance']
] = dim_product[
    ['category', 'subcategory', 'maintenance']
].fillna('Unknown')

# Drop unnecessary columns
dim_product = dim_product.drop(
    columns=[
        'ID',
        'prd_key',
        'prd_end_dt',
        'prd_line'
    ]
)

# Save product dimension
product_path = os.path.join(
    OUTPUT_DIR,
    "dim_product.csv"
)

dim_product.to_csv(product_path, index=False)

print(
    f"Saved dim_product.csv | Shape: {dim_product.shape}"
)


# ---------------------------------------------------------
# C. CLEANING SALES (Fact Sales)
# ---------------------------------------------------------

print("\n[3/3] Processing Sales Data...")

sales = pd.read_csv(
    "data/raw/crm_sales_details.csv"
)

# Convert date columns
date_cols = [
    'sls_order_dt',
    'sls_ship_dt',
    'sls_due_dt'
]

for col in date_cols:
    sales[col] = pd.to_datetime(
        sales[col].astype(str),
        format='%Y%m%d',
        errors='coerce'
    )

# Recalculate incorrect sales values
calc = (
    sales['sls_quantity'] *
    sales['sls_price'].abs()
)

bad_sales = (
    sales['sls_sales'].isna()
    | (sales['sls_sales'] <= 0)
    | (
        calc.notna()
        & ~np.isclose(
            sales['sls_sales'],
            calc
        )
    )
)

sales['sls_sales'] = np.where(
    bad_sales,
    calc,
    sales['sls_sales']
)

# Recalculate missing or incorrect prices
bad_price = (
    sales['sls_price'].isna()
    | (sales['sls_price'] <= 0)
)

sales['sls_price'] = np.where(
    bad_price,
    sales['sls_sales'] / sales['sls_quantity'],
    sales['sls_price']
)

# Keep all sales rows
fact_sales = sales.copy()

# Save sales fact
sales_path = os.path.join(
    OUTPUT_DIR,
    "fact_sales.csv"
)

fact_sales.to_csv(sales_path, index=False)

print(
    f"Saved fact_sales.csv | Shape: {fact_sales.shape}"
)


# ---------------------------------------------------------
# D. QUICK DATA QUALITY CHECKS
# ---------------------------------------------------------

print("\nRunning Data Quality Checks...")

assert dim_customer['cst_id'].is_unique, (
    "Dim Customer has repeated IDs"
)

assert dim_product['product_key'].is_unique, (
    "Dim Product has repeated product keys"
)

assert fact_sales['sls_cust_id'].isin(
    dim_customer['cst_id']
).all(), "Sales with unknown customer"

assert fact_sales['sls_prd_key'].isin(
    dim_product['product_key']
).all(), "Sales with unknown product"

assert fact_sales[
    ['sls_sales', 'sls_price']
].notna().all().all(), (
    "Missing sales or price"
)


# ---------------------------------------------------------
# COMPLETION
# ---------------------------------------------------------

print("\n" + "=" * 50)
print("Transformation Completed Successfully!")
print("=" * 50)

print("\nOutput Files:")

print(customer_path)
print(product_path)
print(sales_path)

print("\nAll processed files saved successfully!")