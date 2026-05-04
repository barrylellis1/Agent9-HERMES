-- Migration: 20260502_fix_premium_mix_sql
-- Purpose: Fix premium_mix_pct KPI SQL for lubricants client.
--          BigQuery schema has product_category (not product_tier) for Premium classification.

UPDATE public.kpis
SET sql_query = 'SELECT ROUND(100.0 * SUM(CASE WHEN product_category = ''Premium'' THEN amount ELSE 0 END) / NULLIF(SUM(amount), 0), 2) AS value FROM `agent9-465818.LubricantsBusiness.LubricantsStarSchemaView` WHERE account_type = ''Revenue'' AND version = ''Actual'''
WHERE id = 'premium_mix_pct'
  AND client_id = 'lubricants';
