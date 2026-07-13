-- ==========================================
-- ADVANCED QUERIES
-- ==========================================

-- 1. Top 10 Customers by Sales
SELECT
    "Customer Name",
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY "Customer Name"
ORDER BY Total_Sales DESC
LIMIT 10;

-- 2. Top 10 Products by Sales
SELECT
    "Product Name",
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY "Product Name"
ORDER BY Total_Sales DESC
LIMIT 10;

-- 3. Monthly Sales Trend
SELECT
    "Order Year",
    "Order Month",
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY "Order Year","Order Month"
ORDER BY "Order Year","Order Month";

-- 4. Monthly Profit Trend
SELECT
    "Order Year",
    "Order Month",
    ROUND(SUM(Profit),2) AS Total_Profit
FROM Superstore
GROUP BY "Order Year","Order Month"
ORDER BY "Order Year","Order Month";

-- 5. Average Shipping Days by Ship Mode
SELECT
    "Ship Mode",
    ROUND(AVG("Shipping Days"),2) AS Avg_Shipping_Days
FROM Superstore
GROUP BY "Ship Mode";

-- 6. Sales by Discount Category
SELECT
    "Discount Category",
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY "Discount Category"
ORDER BY Total_Sales DESC;

-- 7. Profit by Order Size
SELECT
    "Order Size",
    ROUND(SUM(Profit),2) AS Total_Profit
FROM Superstore
GROUP BY "Order Size"
ORDER BY Total_Profit DESC;

-- 8. Customer Lifetime Value
SELECT
    "Customer Name",
    ROUND(MAX("Customer Lifetime Value"),2) AS Lifetime_Value
FROM Superstore
GROUP BY "Customer Name"
ORDER BY Lifetime_Value DESC
LIMIT 10;