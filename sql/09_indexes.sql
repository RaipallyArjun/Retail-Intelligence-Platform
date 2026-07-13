-- ==========================================
-- INDEXES
-- ==========================================
-- Superstore itself is read in full by every dashboard page (pandas
-- filters in memory), so it gets no indexes here — an index only
-- helps queries filtered/sorted by SQLite itself, not a full-table
-- SELECT * that's filtered in pandas afterward.
--
-- Sales_Audit, however, grows with every insert and is the table
-- most likely to be queried directly by Order_ID or by time range,
-- so it gets indexed:

CREATE INDEX IF NOT EXISTS idx_sales_audit_order_id
ON Sales_Audit (Order_ID);

CREATE INDEX IF NOT EXISTS idx_sales_audit_action_time
ON Sales_Audit (Action_Time);

-- Verify:
-- SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='Sales_Audit';
