SELECT
    transaction_month,
    COALESCE(
        SUM(line_amount) FILTER (WHERE row_class = 'sale'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS gross_sales,
    COALESCE(
        SUM(ABS(line_amount)) FILTER (WHERE row_class = 'cancellation'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS cancellation_value,
    COALESCE(SUM(line_amount), CAST(0 AS DECIMAL(38, 3)))
        AS net_recorded_value,
    COUNT(DISTINCT invoice) FILTER (WHERE row_class = 'sale')
        AS completed_orders,
    COUNT(DISTINCT invoice) FILTER (WHERE row_class = 'cancellation')
        AS cancellation_documents,
    COUNT(DISTINCT customer_id) FILTER (
        WHERE row_class = 'sale' AND customer_id IS NOT NULL
    ) AS known_customers
FROM analytics_transactions
GROUP BY transaction_month
ORDER BY transaction_month;
