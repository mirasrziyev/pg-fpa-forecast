-- Views on top of the tables created by 02_load_sql.py
-- A view is a saved query: it always shows current data when you SELECT from it.

DROP VIEW IF EXISTS v_segment_yoy;
CREATE VIEW v_segment_yoy AS
SELECT s.period_id,
       p.period_index,
       s.segment_id,
       s.net_sales,
       LAG(s.net_sales, 4) OVER (PARTITION BY s.segment_id ORDER BY p.period_index) AS net_sales_py,
       1.0 * s.net_sales
         / LAG(s.net_sales, 4) OVER (PARTITION BY s.segment_id ORDER BY p.period_index) - 1 AS yoy_growth,
       s.organic_pct
FROM fact_segment AS s
JOIN dim_period AS p USING (period_id);

DROP VIEW IF EXISTS v_quarterly_pl;
CREATE VIEW v_quarterly_pl AS
SELECT p.period_id,
       p.period_index,
       SUM(CASE WHEN f.metric = 'net_sales'           THEN f.value END) AS net_sales,
       SUM(CASE WHEN f.metric = 'cost_of_sales'       THEN f.value END) AS cost_of_sales,
       SUM(CASE WHEN f.metric = 'sga'                 THEN f.value END) AS sga,
       SUM(CASE WHEN f.metric = 'operating_income'    THEN f.value END) AS operating_income,
       SUM(CASE WHEN f.metric = 'net_earnings_pg'     THEN f.value END) AS net_earnings_pg,
       SUM(CASE WHEN f.metric = 'operating_cash_flow' THEN f.value END) AS operating_cash_flow,
       SUM(CASE WHEN f.metric = 'capex'               THEN f.value END) AS capex,
       SUM(CASE WHEN f.metric = 'receivables'         THEN f.value END) AS receivables,
       SUM(CASE WHEN f.metric = 'inventory'           THEN f.value END) AS inventory,
       SUM(CASE WHEN f.metric = 'payables'            THEN f.value END) AS payables
FROM dim_period AS p
LEFT JOIN fact_financials AS f USING (period_id)
GROUP BY p.period_id, p.period_index
ORDER BY p.period_index;