-- ==========================================
-- TABLES
-- ==========================================
-- NOTE: Superstore is normally created automatically by
-- src/database/import_data.py, which loads
-- data/processed/processed_superstore.csv via pandas'
-- df.to_sql("Superstore", conn). The DDL below documents the
-- resulting schema (and can be used to pre-create the table before
-- an `if_exists="append"` import). Column names match the CSV
-- headers exactly, including spaces and hyphens.

CREATE TABLE IF NOT EXISTS Superstore (
    "Row ID" INTEGER,
    "Order ID" TEXT,
    "Order Date" TEXT,
    "Ship Date" TEXT,
    "Ship Mode" TEXT,
    "Customer ID" TEXT,
    "Customer Name" TEXT,
    "Segment" TEXT,
    "Country" TEXT,
    "City" TEXT,
    "State" TEXT,
    "Postal Code" INTEGER,
    "Region" TEXT,
    "Product ID" TEXT,
    "Category" TEXT,
    "Sub-Category" TEXT,
    "Product Name" TEXT,
    "Sales" REAL,
    "Quantity" INTEGER,
    "Discount" REAL,
    "Profit" REAL,
    "Order Year" INTEGER,
    "Order Month" INTEGER,
    "Order Month Name" TEXT,
    "Order Quarter" INTEGER,
    "Order Day" INTEGER,
    "Order Weekday" TEXT,
    "Shipping Days" INTEGER,
    "Profit Margin (%)" REAL,
    "Sales Per Unit" REAL,
    "Discount Category" TEXT,
    "Order Size" TEXT,
    "Sales Category" TEXT,
    "Profit Category" TEXT,
    "Shipping Speed" TEXT,
    "Customer Lifetime Value" REAL
);

-- Audit log table — populated automatically by trg_sales_insert
-- (see 08_triggers.sql) whenever a row is inserted into Superstore.
CREATE TABLE IF NOT EXISTS Sales_Audit (
    Audit_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Order_ID TEXT,
    Sales REAL,
    Action_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
