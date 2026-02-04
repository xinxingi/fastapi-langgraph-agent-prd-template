-- 数据库迁移脚本：添加 last_used_at 字段
-- 执行方式: psql -U postgres -d your_database_name -f add_last_used_at_field.sql

-- 方法 1: 如果表名是 bs_bearer_tokens（旧表名）
ALTER TABLE bs_bearer_tokens ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP NULL;

-- 方法 2: 如果表名是 bs_api_keys（新表名）
ALTER TABLE bs_api_keys ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP NULL;

-- 验证字段已添加
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name IN ('bs_bearer_tokens', 'bs_api_keys') 
  AND column_name = 'last_used_at';
