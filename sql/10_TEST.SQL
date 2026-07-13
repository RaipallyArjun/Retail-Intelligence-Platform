-- ==========================================
-- TRIGGER TEST (round-trip, self-cleaning)
-- ==========================================
-- Confirms trg_sales_insert fires correctly on a real insert.
-- Run each statement individually and check the result before
-- moving to the next one.

-- 1. Insert a throwaway test order
INSERT INTO Superstore ("Order ID", Sales) VALUES ('TEST-0001', 999.99);

-- 2. Confirm the trigger logged it
SELECT * FROM Sales_Audit WHERE Order_ID = 'TEST-0001';
-- Expect exactly one row: Sales = 999.99, Action_Time auto-populated

-- 3. Clean up the test data (always run this after step 2)
DELETE FROM Superstore WHERE "Order ID" = 'TEST-0001';
DELETE FROM Sales_Audit WHERE Order_ID = 'TEST-0001';
