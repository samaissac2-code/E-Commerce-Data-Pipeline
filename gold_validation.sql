
-- ============================================================
 --  1. CHECK GOLD TABLES
-- ============================================================ 

SELECT 'dim_customers' AS table_name, COUNT(*) AS total_rows
FROM gold.dim_customers

UNION ALL

SELECT 'dim_products', COUNT(*)
FROM gold.dim_products

UNION ALL

SELECT 'dim_date', COUNT(*)
FROM gold.dim_date

UNION ALL

SELECT 'fact_sales', COUNT(*)
FROM gold.fact_sales;


-- ============================================================
-- 2. PRODUCT DIMENSION
-- ============================================================ 

SELECT
    product_key,
    product_id,
    product_number,
    product_name
FROM gold.dim_products;


-- ============================================================
-- 3. FACT TABLE - PRODUCT KEY MAPPING
-- ============================================================ 

SELECT
    f.order_number,
    f.sales_amount,
    f.quantity,
    f.price,
    COUNT(*) AS matching_source_rows
FROM gold.fact_sales AS f
JOIN silver.crm_sales_details AS s
    ON f.order_number = s.sls_ord_num
   AND f.sales_amount = s.sls_sales
   AND f.quantity = s.sls_quantity
   AND f.price = s.sls_price
GROUP BY
    f.order_number,
    f.sales_amount,
    f.quantity,
    f.price
HAVING COUNT(*) > 1;


-- ============================================================
-- 4. UPDATE FACT PRODUCT KEYS
-- ============================================================ 

BEGIN TRANSACTION;

UPDATE f
SET f.product_key = p.product_key
FROM gold.fact_sales AS f
JOIN silver.crm_sales_details AS s
    ON f.order_number = s.sls_ord_num
   AND f.sales_amount = s.sls_sales
   AND f.quantity = s.sls_quantity
   AND f.price = s.sls_price
JOIN gold.dim_products AS p
    ON s.sls_prd_key = p.product_number;

COMMIT TRANSACTION;


-- ============================================================
-- 5. VALIDATE FACT TABLE KEYS
-- ============================================================ 

SELECT
    COUNT(*) AS total_sales,

    SUM(CASE
        WHEN customer_key IS NULL THEN 1
        ELSE 0
    END) AS missing_customer_keys,

    SUM(CASE
        WHEN product_key IS NULL THEN 1
        ELSE 0
    END) AS missing_product_keys

FROM gold.fact_sales;


-- ============================================================
-- 6. VALIDATE DATE RELATIONSHIPS
-- ============================================================ 

SELECT
    COUNT(*) AS total_sales,

    SUM(CASE
        WHEN od.date_key IS NULL THEN 1
        ELSE 0
    END) AS missing_order_dates,

    SUM(CASE
        WHEN sd.date_key IS NULL THEN 1
        ELSE 0
    END) AS missing_shipping_dates,

    SUM(CASE
        WHEN dd.date_key IS NULL THEN 1
        ELSE 0
    END) AS missing_due_dates

FROM gold.fact_sales AS f

LEFT JOIN gold.dim_date AS od
    ON f.order_date_key = od.date_key

LEFT JOIN gold.dim_date AS sd
    ON f.shipping_date_key = sd.date_key

LEFT JOIN gold.dim_date AS dd
    ON f.due_date_key = dd.date_key;


-- ============================================================
-- 7. FINAL GOLD ROW COUNTS
-- ============================================================ 

SELECT 'Customers' AS dimension_name, COUNT(*) AS total_rows
FROM gold.dim_customers

UNION ALL

SELECT 'Products', COUNT(*)
FROM gold.dim_products

UNION ALL

SELECT 'Dates', COUNT(*)
FROM gold.dim_date

UNION ALL

SELECT 'Sales', COUNT(*)
FROM gold.fact_sales;
