

-- ============================================================
-- 1. Validate customer and product relationships
-- ============================================================ 

SELECT
    COUNT(*) AS total_sales,

    SUM(CASE
        WHEN c.customer_key IS NULL THEN 1
        ELSE 0
    END) AS missing_customers,

    SUM(CASE
        WHEN p.product_key IS NULL THEN 1
        ELSE 0
    END) AS missing_products

FROM gold.fact_sales AS f

LEFT JOIN gold.dim_customers AS c
    ON f.customer_key = c.customer_key

LEFT JOIN gold.dim_products AS p
    ON f.product_key = p.product_key;


-- ============================================================
--2. Validate date relationships
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
-- 3. Check dimension primary key uniquenes
-- ============================================================ 

SELECT
    'dim_customers' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT customer_key) AS unique_keys
FROM gold.dim_customers

UNION ALL

SELECT
    'dim_products',
    COUNT(*),
    COUNT(DISTINCT product_key)
FROM gold.dim_products

UNION ALL

SELECT
    'dim_date',
    COUNT(*),
    COUNT(DISTINCT date_key)
FROM gold.dim_date;




