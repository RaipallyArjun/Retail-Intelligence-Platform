-- ==========================================
-- BASIC QUERIES
-- ==========================================

-- Total Records
SELECT COUNT(*) AS Total_Records
FROM Superstore;

-- First 10 Records
SELECT *
FROM Superstore
LIMIT 10;

-- Total Sales
SELECT ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore;

-- Total Profit
SELECT ROUND(SUM(Profit),2) AS Total_Profit
FROM Superstore;

-- Total Orders
SELECT COUNT(DISTINCT "Order ID") AS Total_Orders
FROM Superstore;

-- Total Customers
SELECT COUNT(DISTINCT "Customer ID") AS Total_Customers
FROM Superstore;

-- Total Products
SELECT COUNT(DISTINCT "Product ID") AS Total_Products
FROM Superstore;