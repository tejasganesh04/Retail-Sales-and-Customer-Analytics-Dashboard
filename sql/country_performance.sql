SELECT
    country,
    COALESCE(
        SUM(line_amount) FILTER (WHERE row_class = 'sale'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS gross_sales,
    COUNT(DISTINCT invoice) FILTER (WHERE row_class = 'sale')
        AS completed_orders,
    ROUND(
        gross_sales / NULLIF(completed_orders, 0),
        3
    ) AS average_order_value,
    COUNT(DISTINCT invoice) FILTER (WHERE row_class = 'cancellation')
        AS cancellation_documents,
    COALESCE(
        SUM(ABS(line_amount)) FILTER (WHERE row_class = 'cancellation'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS cancellation_value,
    COUNT(DISTINCT customer_id) FILTER (
        WHERE row_class = 'sale' AND customer_id IS NOT NULL
    ) AS known_customers,
    COALESCE(SUM(line_amount), CAST(0 AS DECIMAL(38, 3)))
        AS net_recorded_value
FROM analytics_transactions
GROUP BY country
ORDER BY gross_sales DESC, country;
