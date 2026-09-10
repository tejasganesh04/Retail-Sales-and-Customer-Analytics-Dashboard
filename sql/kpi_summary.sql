WITH totals AS (
    SELECT
        COUNT(*) AS curated_rows,
        COUNT(*) FILTER (WHERE row_class = 'sale') AS sale_rows,
        COUNT(*) FILTER (WHERE row_class = 'cancellation') AS cancellation_rows,
        COUNT(*) FILTER (WHERE row_class = 'other_adjustment') AS adjustment_rows,
        COALESCE(
            SUM(line_amount) FILTER (WHERE row_class = 'sale'),
            CAST(0 AS DECIMAL(38, 3))
        ) AS gross_sales,
        COALESCE(SUM(line_amount), CAST(0 AS DECIMAL(38, 3)))
            AS net_recorded_value,
        COUNT(DISTINCT invoice) FILTER (WHERE row_class = 'sale')
            AS completed_orders,
        COUNT(DISTINCT invoice) FILTER (WHERE row_class = 'cancellation')
            AS cancellation_documents,
        COUNT(DISTINCT customer_id) FILTER (
            WHERE row_class = 'sale' AND customer_id IS NOT NULL
        ) AS known_customers,
        MIN(transaction_date) AS first_transaction_date,
        MAX(transaction_date) AS last_transaction_date
    FROM analytics_transactions
)
SELECT
    curated_rows,
    sale_rows,
    cancellation_rows,
    adjustment_rows,
    gross_sales,
    net_recorded_value,
    completed_orders,
    ROUND(gross_sales / NULLIF(completed_orders, 0), 3)
        AS average_order_value,
    cancellation_documents,
    ROUND(
        100.0 * cancellation_documents
        / NULLIF(completed_orders + cancellation_documents, 0),
        2
    ) AS cancellation_document_rate_pct,
    known_customers,
    first_transaction_date,
    last_transaction_date
FROM totals;
