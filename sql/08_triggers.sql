-- ==========================================
-- TRIGGERS
-- ==========================================
-- Logs every new Superstore order into Sales_Audit automatically.
-- Requires Sales_Audit to exist first (see 02_create_tables.sql).

CREATE TRIGGER IF NOT EXISTS trg_sales_insert
AFTER INSERT ON Superstore
BEGIN
    INSERT INTO Sales_Audit (Order_ID, Sales)
    VALUES (NEW."Order ID", NEW.Sales);
END;

-- Verify it was created:
-- SELECT name FROM sqlite_master WHERE type='trigger';

-- NOTE ON RUNNING THIS FILE: some GUI SQL clients (including VS
-- Code's SQLTools) split scripts into separate statements at every
-- semicolon, which breaks multi-statement trigger bodies like the
-- one above. If "Run on active connection" fails with an error like
-- "cannot commit - no transaction is active", select the full
-- CREATE TRIGGER...END; block manually and run it as one selection,
-- or run this file with the sqlite3 CLI / Python's
-- conn.executescript(), both of which execute it correctly.
