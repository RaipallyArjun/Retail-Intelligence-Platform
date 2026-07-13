-- ==========================================
-- SQL VIEWS
-- ==========================================

CREATE VIEW IF NOT EXISTS Sales_By_Region AS
SELECT
    Region,
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY Region;

CREATE VIEW IF NOT EXISTS Profit_By_Category AS
SELECT
    Category,
    ROUND(SUM(Profit),2) AS Total_Profit
FROM Superstore
GROUP BY Category;

CREATE VIEW IF NOT EXISTS Monthly_Sales AS
SELECT
    "Order Year",
    "Order Month",
    ROUND(SUM(Sales),2) AS Total_Sales
FROM Superstore
GROUP BY "Order Year","Order Month";