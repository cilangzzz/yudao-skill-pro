-- SQL 文件合并输出
-- 生成时间: 2026-03-18 21:55:52
-- 文件数量: 3
-- 分类: index
--
-- 包含的文件:
--   无日期 | 2026_2_07_fz_letter_reply_idx.sql
--   无日期 | 2025_1_05_fz_petition_visit_idx.sql
--   无日期 | 2025_12_30_2025_12_30_idx.sql
--

-- ============================================================
-- 文件: 2026_2_07_fz_letter_reply_idx.sql
-- 表名: 未知
-- 分类: index
-- ============================================================

CREATE INDEX idx_letter_id ON fz_letter_reply (letter_id, deleted);

-- ============================================================
-- 文件: 2025_1_05_fz_petition_visit_idx.sql
-- 表名: 未知
-- 分类: index
-- ============================================================

CREATE INDEX idx_petition_deleted_id ON fz_petition_visit (deleted, id DESC);

-- ============================================================
-- 文件: 2025_12_30_2025_12_30_idx.sql
-- 表名: 未知
-- 分类: index
-- ============================================================

ALTER TABLE fz_letter_business_type ADD INDEX idx_id_deleted (id, deleted);
ALTER TABLE fz_letter_message_type ADD INDEX idx_id_deleted (id, deleted);
ALTER TABLE fz_letter_case_direction ADD INDEX idx_id_deleted (id, deleted);


CREATE INDEX idx_label_del_dept ON fz_letter_label (deleted, id, dept_path);
CREATE INDEX idx_rel_lette r_label ON fz_letter_label_rel (letter_id, deleted, label_id);

