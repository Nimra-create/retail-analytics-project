-- ============================================================
-- Business Analytics — KPI Views
-- Run against sql/business.db (SQLite). These views are the
-- layer Power BI (or any SQL client) queries directly, so KPI
-- logic lives in one place instead of being redefined per tool.
-- ============================================================

DROP VIEW IF EXISTS v_monthly_kpis;
CREATE VIEW v_monthly_kpis AS
SELECT
    strftime('%Y-%m', order_date)              AS month,
    SUM(revenue)                                AS total_revenue,
    SUM(profit)                                 AS total_profit,
    ROUND(SUM(profit) * 1.0 / SUM(revenue), 4)  AS gross_margin_pct,
    COUNT(DISTINCT order_id)                    AS total_orders,
    ROUND(SUM(revenue) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_order_value,
    COUNT(DISTINCT customer_id)                 AS active_customers
FROM sales
GROUP BY 1
ORDER BY 1;

DROP VIEW IF EXISTS v_category_performance;
CREATE VIEW v_category_performance AS
SELECT
    category,
    SUM(revenue)                                AS total_revenue,
    SUM(profit)                                 AS total_profit,
    ROUND(SUM(profit) * 1.0 / SUM(revenue), 4)  AS gross_margin_pct,
    COUNT(DISTINCT order_id)                    AS total_orders,
    ROUND(SUM(revenue) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_order_value
FROM sales
GROUP BY category
ORDER BY total_revenue DESC;

DROP VIEW IF EXISTS v_region_performance;
CREATE VIEW v_region_performance AS
SELECT
    region,
    SUM(revenue)              AS total_revenue,
    SUM(profit)                AS total_profit,
    COUNT(DISTINCT order_id)   AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;

DROP VIEW IF EXISTS v_channel_performance;
CREATE VIEW v_channel_performance AS
SELECT
    channel,
    SUM(revenue)                               AS total_revenue,
    ROUND(SUM(revenue) * 100.0 / (SELECT SUM(revenue) FROM sales), 1) AS pct_of_total_revenue,
    COUNT(DISTINCT order_id)                   AS total_orders
FROM sales
GROUP BY channel
ORDER BY total_revenue DESC;

DROP VIEW IF EXISTS v_customer_value;
CREATE VIEW v_customer_value AS
SELECT
    customer_id,
    COUNT(DISTINCT order_id)   AS total_orders,
    SUM(revenue)                AS lifetime_revenue,
    SUM(profit)                 AS lifetime_profit,
    ROUND(AVG(revenue), 2)      AS avg_order_value,
    MIN(order_date)             AS first_order,
    MAX(order_date)             AS last_order
FROM sales
GROUP BY customer_id
ORDER BY lifetime_revenue DESC;

DROP VIEW IF EXISTS v_top10_customers;
CREATE VIEW v_top10_customers AS
SELECT * FROM v_customer_value ORDER BY lifetime_revenue DESC LIMIT 10;

-- Repeat purchase rate as a single-row summary KPI
DROP VIEW IF EXISTS v_repeat_purchase_rate;
CREATE VIEW v_repeat_purchase_rate AS
SELECT
    ROUND(
        SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4
    ) AS repeat_purchase_rate,
    COUNT(*) AS total_customers
FROM v_customer_value;
