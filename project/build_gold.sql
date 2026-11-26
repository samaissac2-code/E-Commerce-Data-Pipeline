


-- ============================================================
-- 1. CREATE DIMENSION TABLES
-- ============================================================ 

-- Customer Dimension

IF OBJECT_ID('gold.dim_customers', 'U') IS NULL
BEGIN
    CREATE TABLE gold.dim_customers
    (
        customer_key INT IDENTITY(1,1) PRIMARY KEY,
        customer_id INT,
        customer_number NVARCHAR(50),
        first_name NVARCHAR(100),
        last_name NVARCHAR(100),
        country NVARCHAR(100),
        marital_status NVARCHAR(20),
        gender NVARCHAR(20),
        birth_date DATE,
        create_date DATE
    );
END;


-- Product Dimension

IF OBJECT_ID('gold.dim_products', 'U') IS NULL
BEGIN
    CREATE TABLE gold.dim_products
    (
        product_key INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT,
        product_number NVARCHAR(50),
        product_name NVARCHAR(200),
        category_id NVARCHAR(50),
        category NVARCHAR(100),
        subcategory NVARCHAR(100),
        maintenance NVARCHAR(50),
        cost INT,
        product_line NVARCHAR(50),
        start_date DATE
    );
END;


-- Date Dimension

IF OBJECT_ID('gold.dim_date', 'U') IS NULL
BEGIN
    CREATE TABLE gold.dim_date
    (
        date_key INT PRIMARY KEY,
        full_date DATE,
        day_number INT,
        day_name NVARCHAR(20),
        month_number INT,
        month_name NVARCHAR(20),
        quarter_number INT,
        year_number INT
    );
END;


-- ============================================================
-- 2. CREATE FACT TABLE
-- ============================================================ 

IF OBJECT_ID('gold.fact_sales', 'U') IS NULL
BEGIN
    CREATE TABLE gold.fact_sales
    (
        order_number NVARCHAR(50),
        product_key INT,
        customer_key INT,
        order_date_key INT,
        shipping_date_key INT,
        due_date_key INT,
        sales_amount INT,
        quantity INT,
        price INT
    );
END;


-- ============================================================
-- 3.LOAD CUSTOMER DIMENSION
-- ============================================================ 

IF NOT EXISTS (SELECT 1 FROM gold.dim_customers)
BEGIN

    INSERT INTO gold.dim_customers

    (
        customer_id,
        customer_number,
        first_name,
        last_name,
        country,
        marital_status,
        gender,
        birth_date,
        create_date
    )

    SELECT
        ci.cst_id,
        ci.cst_key,
        ci.cst_firstname,
        ci.cst_lastname,
        la.cntry,
        ci.cst_marital_status,

        CASE
            WHEN UPPER(LTRIM(RTRIM(ci.cst_gndr))) IN ('M', 'F')
                THEN UPPER(LTRIM(RTRIM(ci.cst_gndr)))

            WHEN UPPER(LTRIM(RTRIM(ca.gen))) IN ('M', 'F')
                THEN UPPER(LTRIM(RTRIM(ca.gen)))

            ELSE 'Unknown'
        END,

        ca.bdate,
        ci.cst_create_date

    FROM silver.crm_cust_info ci

    LEFT JOIN silver.erp_cust_az12 ca
        ON ci.cst_key = ca.cid

    LEFT JOIN silver.erp_loc_a101 la
        ON ci.cst_key = la.cid;

END;


-- ============================================================
-- 4. LOAD PRODUCT DIMENSION
-- ============================================================ 

IF NOT EXISTS (SELECT 1 FROM gold.dim_products)
BEGIN

    ;WITH product_versions AS
    (
        SELECT
            *,
            ROW_NUMBER() OVER
            (
                PARTITION BY prd_key
                ORDER BY prd_start_dt DESC, prd_id DESC
            ) AS rn

        FROM silver.crm_prd_info
    )

    INSERT INTO gold.dim_products
    (
        product_id,
        product_number,
        product_name,
        category_id,
        category,
        subcategory,
        maintenance,
        cost,
        product_line,
        start_date
    )

    SELECT
        p.prd_id,

        -- Remove the first six characters
        SUBSTRING(p.prd_key, 7, LEN(p.prd_key)),

        p.prd_nm,

        CONCAT(
            LEFT(p.prd_key, 2),
            '_',
            SUBSTRING(p.prd_key, 4, 2)
        ),

        pc.cat,
        pc.subcat,
        pc.maintenance,
        p.prd_cost,
        p.prd_line,
        CONVERT(DATE, p.prd_start_dt)

    FROM product_versions p

    LEFT JOIN silver.erp_px_cat_g1v2 pc
        ON CONCAT(
            LEFT(p.prd_key, 2),
            '_',
            SUBSTRING(p.prd_key, 4, 2)
        ) = pc.id

    WHERE p.rn = 1;

END;


-- ============================================================
--5. LOAD DATE DIMENSION
-- ============================================================ 

IF NOT EXISTS (SELECT 1 FROM gold.dim_date)
BEGIN

    ;WITH repaired_sales_dates AS
    (
        SELECT

            CASE
                WHEN s.sls_ord_num = 'SO64339'
                    THEN CONVERT(DATE, '20130816', 112)

                WHEN s.sls_ord_num = 'SO65340'
                    THEN CONVERT(DATE, '20130829', 112)

                ELSE COALESCE
                (
                    CASE
                        WHEN LEN(CONVERT(VARCHAR(20), s.sls_order_dt)) = 8
                        THEN TRY_CONVERT(
                            DATE,
                            CONVERT(CHAR(8), s.sls_order_dt),
                            112
                        )
                    END,
                    valid_order.correct_order_date
                )
            END AS order_date,

            CASE
                WHEN LEN(CONVERT(VARCHAR(20), s.sls_ship_dt)) = 8
                THEN TRY_CONVERT(
                    DATE,
                    CONVERT(CHAR(8), s.sls_ship_dt),
                    112
                )
            END AS shipping_date,

            CASE
                WHEN LEN(CONVERT(VARCHAR(20), s.sls_due_dt)) = 8
                THEN TRY_CONVERT(
                    DATE,
                    CONVERT(CHAR(8), s.sls_due_dt),
                    112
                )
            END AS due_date

        FROM silver.crm_sales_details s

        OUTER APPLY
        (
            SELECT
                MAX
                (
                    CASE
                        WHEN LEN(CONVERT(VARCHAR(20), s2.sls_order_dt)) = 8
                        THEN TRY_CONVERT(
                            DATE,
                            CONVERT(CHAR(8), s2.sls_order_dt),
                            112
                        )
                    END
                ) AS correct_order_date

            FROM silver.crm_sales_details s2
            WHERE s2.sls_ord_num = s.sls_ord_num

        ) valid_order
    ),

    all_dates AS
    (
        SELECT order_date AS full_date
        FROM repaired_sales_dates

        UNION

        SELECT shipping_date
        FROM repaired_sales_dates

        UNION

        SELECT due_date
        FROM repaired_sales_dates
    )

    INSERT INTO gold.dim_date
    (
        date_key,
        full_date,
        day_number,
        day_name,
        month_number,
        month_name,
        quarter_number,
        year_number
    )

    SELECT DISTINCT
        CONVERT(INT, CONVERT(CHAR(8), full_date, 112)),
        full_date,
        DAY(full_date),
        DATENAME(WEEKDAY, full_date),
        MONTH(full_date),
        DATENAME(MONTH, full_date),
        DATEPART(QUARTER, full_date),
        YEAR(full_date)

    FROM all_dates
    WHERE full_date IS NOT NULL;

END;


-- ============================================================
-- 6. LOAD FACT SALES
-- ============================================================ 

IF NOT EXISTS (SELECT 1 FROM gold.fact_sales)
BEGIN

    ;WITH repaired_sales AS
    (
        SELECT
            s.*,

            CASE
                WHEN s.sls_ord_num = 'SO64339'
                    THEN CONVERT(DATE, '20130816', 112)

                WHEN s.sls_ord_num = 'SO65340'
                    THEN CONVERT(DATE, '20130829', 112)

                ELSE COALESCE
                (
                    CASE
                        WHEN LEN(CONVERT(VARCHAR(20), s.sls_order_dt)) = 8
                        THEN TRY_CONVERT(
                            DATE,
                            CONVERT(CHAR(8), s.sls_order_dt),
                            112
                        )
                    END,
                    valid_order.correct_order_date
                )
            END AS corrected_order_date,

            CASE
                WHEN LEN(CONVERT(VARCHAR(20), s.sls_ship_dt)) = 8
                THEN TRY_CONVERT(
                    DATE,
                    CONVERT(CHAR(8), s.sls_ship_dt),
                    112
                )
            END AS corrected_shipping_date,

            CASE
                WHEN LEN(CONVERT(VARCHAR(20), s.sls_due_dt)) = 8
                THEN TRY_CONVERT(
                    DATE,
                    CONVERT(CHAR(8), s.sls_due_dt),
                    112
                )
            END AS corrected_due_date

        FROM silver.crm_sales_details s

        OUTER APPLY
        (
            SELECT
                MAX
                (
                    CASE
                        WHEN LEN(CONVERT(VARCHAR(20), s2.sls_order_dt)) = 8
                        THEN TRY_CONVERT(
                            DATE,
                            CONVERT(CHAR(8), s2.sls_order_dt),
                            112
                        )
                    END
                ) AS correct_order_date

            FROM silver.crm_sales_details s2
            WHERE s2.sls_ord_num = s.sls_ord_num

        ) valid_order
    )

    INSERT INTO gold.fact_sales
    (
        order_number,
        product_key,
        customer_key,
        order_date_key,
        shipping_date_key,
        due_date_key,
        sales_amount,
        quantity,
        price
    )

    SELECT
        sd.sls_ord_num,
        pr.product_key,
        cu.customer_key,

        CONVERT(INT, CONVERT(CHAR(8), sd.corrected_order_date, 112)),

        CONVERT(INT, CONVERT(CHAR(8), sd.corrected_shipping_date, 112)),

        CONVERT(INT, CONVERT(CHAR(8), sd.corrected_due_date, 112)),

        sd.sls_sales,
        sd.sls_quantity,
        sd.sls_price

    FROM repaired_sales sd

    LEFT JOIN gold.dim_products pr
        ON sd.sls_prd_key = pr.product_number

    LEFT JOIN gold.dim_customers cu
        ON sd.sls_cust_id = cu.customer_id;

END;


-- ============================================================
-- 7.VERIFY GOLD TABLE ROW COUNTS
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
-- 8. VALIDATE FACT TABLE KEYS
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
-- 9. VALIDATE DATE RELATIONSHIPS
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

FROM gold.fact_sales f

LEFT JOIN gold.dim_date od
    ON f.order_date_key = od.date_key

LEFT JOIN gold.dim_date sd
    ON f.shipping_date_key = sd.date_key

LEFT JOIN gold.dim_date dd
    ON f.due_date_key = dd.date_key;
