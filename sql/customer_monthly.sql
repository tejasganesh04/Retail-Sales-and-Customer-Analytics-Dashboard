SELECT
    order_month,
    COUNT(DISTINCT customer_id) AS active_known_customers,
    COUNT(*) AS known_customer_orders,
    COUNT(*) FILTER (WHERE customer_order_type = 'new')
        AS new_customer_orders,
    COUNT(*) FILTER (WHERE customer_order_type = 'repeat')
        AS repeat_customer_orders,
    COALESCE(
        SUM(order_value) FILTER (WHERE customer_order_type = 'new'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS new_customer_sales,
    COALESCE(
        SUM(order_value) FILTER (WHERE customer_order_type = 'repeat'),
        CAST(0 AS DECIMAL(38, 3))
    ) AS repeat_customer_sales
FROM customer_orders
GROUP BY order_month
ORDER BY order_month;
