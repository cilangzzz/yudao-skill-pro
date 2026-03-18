-- SQL 文件合并输出
-- 生成时间: 2026-03-18 21:55:52
-- 文件数量: 2
-- 分类: table_update
--
-- 包含的文件:
--   2026-03-06 | 2026_03_06_fz_warning_sign_rel_update.sql
--   2026-03-09 | 2026_03_09_fz_letter_handle_update.sql
--

-- ============================================================
-- 文件: 2026_03_06_fz_warning_sign_rel_update.sql
-- 表名: fz_warning_sign_rel
-- 分类: table_update
-- 日期: 2026-03-06
-- ============================================================

ALTER TABLE `GDPAT`.`fz_warning_sign_rel`
ALTER COLUMN `value` TYPE character varying(500);

-- ============================================================
-- 文件: 2026_03_09_fz_letter_handle_update.sql
-- 表名: fz_letter_handle
-- 分类: table_update
-- 日期: 2026-03-09
-- ============================================================

ALTER TABLE `GDPAT`.`fz_letter_handle` MODIFY COLUMN `check_handle_status` CHARACTER VARYING(5120) NULL COMMENT '核查办理情况';

