SELECT
    stock_code,
    COALESCE(
        ARG_MAX(description, invoice_timestamp)
            FILTER (WHERE description IS NOT NULL),
        '(missing description)'
    ) AS description,
    COALESCE(
        SUM(quantity) FILTER (WHERE row_class = 'sale'),
        0
    ) AS quantity_sold,
    COALESCE(
        SUM(line_amount) FILTER (WHERE row_class = 'sale'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS gross_sales,
    COUNT(DISTINCT invoice) FILTER (WHERE row_class = 'sale')
        AS completed_orders,
    COUNT(DISTINCT customer_id) FILTER (
        WHERE row_class = 'sale' AND customer_id IS NOT NULL
    ) AS known_customers,
    COALESCE(
        SUM(ABS(quantity)) FILTER (WHERE row_class = 'cancellation'),
        0
    ) AS cancelled_quantity,
    COALESCE(
        SUM(ABS(line_amount)) FILTER (WHERE row_class = 'cancellation'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS cancellation_value,
    COALESCE(SUM(line_amount), CAST(0 AS DECIMAL(38, 3)))
        AS net_recorded_value
FROM analytics_transactions
GROUP BY stock_code
HAVING COUNT(*) FILTER (
    WHERE row_class IN ('sale', 'cancellation')
) > 0
ORDER BY gross_sales DESC, stock_code;
