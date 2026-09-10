CREATE OR REPLACE VIEW analytics_transactions AS
SELECT
    *,
    CAST(invoice_timestamp AS DATE) AS transaction_date,
    CAST(DATE_TRUNC('month', invoice_timestamp) AS DATE) AS transaction_month,
    CASE
        WHEN is_cancelled THEN 'cancellation'
        WHEN quantity > 0 AND unit_price > 0 THEN 'sale'
        ELSE 'other_adjustment'
    END AS row_class
FROM curated_transactions;
