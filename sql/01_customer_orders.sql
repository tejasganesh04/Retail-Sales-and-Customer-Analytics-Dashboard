CREATE OR REPLACE VIEW customer_orders AS
WITH completed_orders AS (
    SELECT
        customer_id,
        invoice,
        MIN(invoice_timestamp) AS order_timestamp,
        CAST(DATE_TRUNC('month', MIN(invoice_timestamp)) AS DATE) AS order_month,
        SUM(line_amount) AS order_value
    FROM analytics_transactions
    WHERE row_class = 'sale'
      AND customer_id IS NOT NULL
    GROUP BY customer_id, invoice
),
numbered_orders AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_timestamp, invoice
        ) AS customer_order_number
    FROM completed_orders
)
SELECT
    customer_id,
    invoice,
    order_timestamp,
    order_month,
    order_value,
    customer_order_number,
    CASE
        WHEN customer_order_number = 1 THEN 'new'
        ELSE 'repeat'
    END AS customer_order_type
FROM numbered_orders;
