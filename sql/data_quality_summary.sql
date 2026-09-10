SELECT
    COUNT(*) AS curated_rows,
    COUNT(*) FILTER (WHERE row_class = 'sale') AS sale_rows,
    COUNT(*) FILTER (WHERE row_class = 'cancellation') AS cancellation_rows,
    COUNT(*) FILTER (WHERE row_class = 'other_adjustment') AS adjustment_rows,
    COUNT(*) FILTER (WHERE description IS NULL) AS missing_description_rows,
    COUNT(*) FILTER (WHERE customer_id IS NULL) AS missing_customer_id_rows,
    COUNT(*) FILTER (WHERE quantity <= 0) AS non_positive_quantity_rows,
    COUNT(*) FILTER (WHERE unit_price <= 0) AS non_positive_price_rows,
    COALESCE(
        SUM(line_amount) FILTER (WHERE row_class = 'sale'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS sale_value,
    COALESCE(
        SUM(line_amount) FILTER (WHERE row_class = 'cancellation'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS cancellation_value,
    COALESCE(
        SUM(line_amount) FILTER (WHERE row_class = 'other_adjustment'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS adjustment_value,
    COALESCE(SUM(line_amount), CAST(0 AS DECIMAL(38, 3)))
        AS net_recorded_value,
    MIN(invoice_timestamp) AS earliest_timestamp,
    MAX(invoice_timestamp) AS latest_timestamp
FROM analytics_transactions;
