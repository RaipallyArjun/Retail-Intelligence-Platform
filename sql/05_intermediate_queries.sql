-- ==========================================
-- INTERMEDIATE QUERIES
-- ==========================================

-- 1. Sales by Region
SELECT
    Region,
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY Region
ORDER BY Total_Sales DESC;

-- 2. Profit by Region
SELECT
    Region,
    ROUND(SUM(Profit),2) AS Total_Profit
FROM Superstore
GROUP BY Region
ORDER BY Total_Profit DESC;

-- 3. Sales by Category
SELECT
    Category,
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY Category
ORDER BY Total_Sales DESC;

-- 4. Profit by Category
SELECT
    Category,
    ROUND(SUM(Profit),2) AS Total_Profit
FROM Superstore
GROUP BY Category
ORDER BY Total_Profit DESC;

-- 5. Sales by Segment
SELECT
    Segment,
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY Segment
ORDER BY Total_Sales DESC;

-- 6. Top 10 States by Sales
SELECT
    State,
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY State
ORDER BY Total_Sales DESC
LIMIT 10;

-- 7. Top 10 Cities by Profit
SELECT
    City,
    ROUND(SUM(Profit),2) AS Total_Profit
FROM Superstore
GROUP BY City
ORDER BY Total_Profit DESC
LIMIT 10;